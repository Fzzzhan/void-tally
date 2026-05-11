#!/usr/bin/env python3
"""
Latency Tracker
Implements precise Void time and generation duration statistics.

Void time = TTLT (Time to Last Token): from the user pressing Enter
to the last AI output character of that turn. Does not include the
user's read/think time after the AI finishes.

Gen time = from first AI token to last AI token (pure generation span).
"""

import time
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class SessionStatistics:
    """Session statistics data"""
    total_void_time_ms: float
    total_gen_time_ms: float
    void_count: int
    average_void_time_ms: float
    average_gen_time_ms: float
    min_void_time_ms: float
    max_void_time_ms: float


class LatencyTracker:
    """
    Latency tracking state machine

    State transitions:
    IDLE -> INPUT_RECEIVED (Enter detected) -> FIRST_TOKEN (First char detected) -> IDLE
    """

    def __init__(self):
        # State
        self.input_time: Optional[float] = None
        self.first_token_time: Optional[float] = None
        self.is_waiting_for_token: bool = False

        # Statistics
        self.void_durations: List[float] = []
        self.gen_durations: List[float] = []

        # Interaction timing: measures from user pressing Enter (submit)
        # to user pressing any other key (ready to type)
        self.last_output_time: Optional[float] = None

        # Auto-finalize: if AI output stops for this many seconds, end void time
        self.idle_threshold_seconds: float = 5.0

        # If AI never outputs a first token within this many seconds, abandon the
        # interaction entirely (don't record void time). Prevents overnight hangs
        # from inflating void time when the session is left open with a pending Enter.
        self.first_token_timeout_seconds: float = 300.0

        # Use high-precision timer (nanosecond level)
        self.timer = time.perf_counter

    def mark_input_received(self):
        """
        Mark: User pressed Enter (submit request)

        Start timing for a new interaction. If a previous interaction had
        AI output (last_output_time is set), save its void and gen durations
        before resetting — this handles the case where the user presses Enter
        again without first typing other keys.
        """
        current_time = self.timer()

        # Save previous interaction if it had AI output (e.g., user presses
        # Enter again without typing first)
        if self.input_time is not None and self.last_output_time is not None:
            void_duration = (self.last_output_time - self.input_time) * 1000
            self.void_durations.append(void_duration)
            if self.first_token_time is not None:
                gen_duration = (self.last_output_time - self.first_token_time) * 1000
                self.gen_durations.append(gen_duration)

        # Start new interaction timing
        self.input_time = current_time
        self.is_waiting_for_token = True
        self.first_token_time = None
        self.last_output_time = None

    def mark_user_typing(self):
        """
        Mark: User pressed a visible key (not Enter)

        Records void time as TTLT (Time to Last Token): from Enter to the
        last AI output character — excluding user read/think time.
        Also records gen_duration = first token to last token.
        """
        if self.input_time is None:
            # No interaction in progress, ignore
            return

        if self.last_output_time is None:
            # AI never responded to this interaction (no token arrived through the PTY).
            # Do NOT fall back to current time — that would include sleep/idle time and
            # produce wildly inflated void measurements. Discard this interaction.
            self.input_time = None
            self.is_waiting_for_token = False
            self.first_token_time = None
            return

        void_duration = (self.last_output_time - self.input_time) * 1000
        self.void_durations.append(void_duration)

        # Record generation duration (first token → last token)
        if self.first_token_time is not None and self.last_output_time is not None:
            gen_duration = (self.last_output_time - self.first_token_time) * 1000
            self.gen_durations.append(gen_duration)

        # Clear state to prevent double-recording
        self.input_time = None
        self.is_waiting_for_token = False
        self.first_token_time = None
        self.last_output_time = None

    def check_and_finalize_if_idle(self):
        """
        Check if AI output has stopped and auto-finalize void time.

        Call this periodically (e.g., every 0.5s) to detect when AI
        has finished outputting but user hasn't pressed any key yet.
        This handles cases where user switches terminals or just reads
        the output without typing.
        """
        if self.input_time is None:
            # No interaction in progress
            return

        current_time = self.timer()

        if self.last_output_time is None:
            # AI hasn't output any token yet. If we've been waiting longer than
            # first_token_timeout_seconds, abandon the interaction without recording
            # void time. This prevents overnight hangs (session left open after Enter)
            # from inflating void time.
            if current_time - self.input_time >= self.first_token_timeout_seconds:
                self.input_time = None
                self.is_waiting_for_token = False
                self.first_token_time = None
                self.last_output_time = None
            return

        idle_duration = current_time - self.last_output_time

        if idle_duration >= self.idle_threshold_seconds:
            # AI has been idle for threshold seconds, finalize void time
            void_duration = (self.last_output_time - self.input_time) * 1000  # ms
            self.void_durations.append(void_duration)

            # Also record gen_duration (first token → last token)
            if self.first_token_time is not None:
                gen_duration = (self.last_output_time - self.first_token_time) * 1000
                self.gen_durations.append(gen_duration)

            # Clear all state
            self.input_time = None
            self.is_waiting_for_token = False
            self.first_token_time = None
            self.last_output_time = None

    def mark_first_token_received(self, char_count: int = 1):
        """
        Mark: Output character received

        Args:
            char_count: Number of characters in this chunk (default: 1)

        Track AI output timestamps for generation time metrics.
        Void time is determined by user keystrokes, not by output.
        """
        if not self.is_waiting_for_token:
            return

        current_time = self.timer()

        # Just update last output time (to track AI is still working)
        self.last_output_time = current_time

        # First token received marker (for generation time tracking)
        if self.first_token_time is None:
            self.first_token_time = current_time

    def get_current_interaction_duration(self) -> float:
        """
        Get current ongoing interaction TTLT estimate (in ms).

        If AI has already output something, returns last_output_time - input_time
        (the TTLT is already determined). Otherwise returns elapsed time so far.
        Returns 0 if no interaction is in progress.
        """
        if self.input_time is not None:
            if self.last_output_time is not None:
                # AI has responded; TTLT is fixed at last output time
                return (self.last_output_time - self.input_time) * 1000
            else:
                # Still waiting for AI; return elapsed time
                return (self.timer() - self.input_time) * 1000
        return 0.0

    def get_statistics(self) -> SessionStatistics:
        """
        Get statistics data.

        Includes the current in-progress interaction's TTLT estimate.
        """
        # Completed interactions
        total_void = sum(self.void_durations)

        # Add current in-progress interaction (TTLT estimate)
        current_duration = self.get_current_interaction_duration()
        total_void += current_duration

        total_gen = sum(self.gen_durations)

        # Count includes current interaction if in progress
        void_count = len(self.void_durations)
        if self.input_time is not None:
            void_count += 1

        # Include current_duration in min/max so they are always consistent
        all_voids = self.void_durations + ([current_duration] if self.input_time is not None else [])

        return SessionStatistics(
            total_void_time_ms=total_void,
            total_gen_time_ms=total_gen,
            void_count=void_count,
            average_void_time_ms=total_void / void_count if void_count > 0 else 0.0,
            average_gen_time_ms=total_gen / len(self.gen_durations) if self.gen_durations else 0.0,
            min_void_time_ms=min(all_voids) if all_voids else 0.0,
            max_void_time_ms=max(all_voids) if all_voids else 0.0,
        )

    def get_void_durations(self) -> List[float]:
        """Get all Void duration list (milliseconds)"""
        return self.void_durations.copy()

    def get_gen_durations(self) -> List[float]:
        """Get all generation duration list (milliseconds)"""
        return self.gen_durations.copy()


if __name__ == "__main__":
    # Test code
    import time

    tracker = LatencyTracker()

    # Simulate interaction
    print("Simulating interaction...")
    tracker.mark_input_received()
    time.sleep(0.5)  # Simulate 500ms Void
    tracker.mark_first_token_received()
    time.sleep(1.0)  # Simulate 1s generation

    tracker.mark_input_received()
    time.sleep(0.3)  # Simulate 300ms Void
    tracker.mark_first_token_received()

    stats = tracker.get_statistics()
    print(f"\nStatistics:")
    print(f"  Total Void: {stats.total_void_time_ms:.2f}ms")
    print(f"  Average Void: {stats.average_void_time_ms:.2f}ms")
    print(f"  Void Count: {stats.void_count}")
    print(f"  Total Gen: {stats.total_gen_time_ms:.2f}ms")
