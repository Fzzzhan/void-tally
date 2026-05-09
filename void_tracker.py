#!/usr/bin/env python3
"""
Latency Tracker
Implements precise Void time and generation duration statistics
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

        # Use high-precision timer (nanosecond level)
        self.timer = time.perf_counter

    def mark_input_received(self):
        """
        Mark: User pressed Enter (Void phase starts)
        """
        current_time = self.timer()

        # If there's an uncompleted generation, record generation duration
        if self.is_waiting_for_token and self.first_token_time is not None:
            gen_duration = current_time - self.first_token_time
            self.gen_durations.append(gen_duration * 1000)  # Convert to milliseconds

        # Start new Void timing
        self.input_time = current_time
        self.is_waiting_for_token = True
        self.first_token_time = None

    def mark_first_token_received(self):
        """
        Mark: First valid character received (Void phase ends, generation phase starts)
        """
        # Only record when waiting for first token
        if not self.is_waiting_for_token or self.first_token_time is not None:
            return

        current_time = self.timer()
        self.first_token_time = current_time
        self.is_waiting_for_token = False

        # Calculate Void duration (TTFT)
        if self.input_time is not None:
            void_duration = current_time - self.input_time
            self.void_durations.append(void_duration * 1000)  # Convert to milliseconds

    def get_statistics(self) -> SessionStatistics:
        """Get statistics data"""
        total_void = sum(self.void_durations)
        total_gen = sum(self.gen_durations)
        void_count = len(self.void_durations)

        return SessionStatistics(
            total_void_time_ms=total_void,
            total_gen_time_ms=total_gen,
            void_count=void_count,
            average_void_time_ms=total_void / void_count if void_count > 0 else 0.0,
            average_gen_time_ms=total_gen / len(self.gen_durations) if self.gen_durations else 0.0,
            min_void_time_ms=min(self.void_durations) if self.void_durations else 0.0,
            max_void_time_ms=max(self.void_durations) if self.void_durations else 0.0,
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
