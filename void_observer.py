#!/usr/bin/env python3
"""
PTY Transparent Proxy - The Void Observer
Implements 100% ANSI passthrough pseudo-terminal proxy
"""

import os
import sys
import pty
import select
import termios
import tty
import signal
import struct
import fcntl
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from void_tracker import LatencyTracker
from void_storage import DataStorage
from void_watcher import VoidWatcher
from void_git import GitAnalyzer  # Phase 3
from void_snapshot import SnapshotManager, file_diff_to_file_change  # Phase 5
from void_char_counter import count_meaningful_chars  # P1: ANSI-aware counting


class VoidObserver:
    """PTY transparent proxy core class"""

    # Mapping from (cli, first_arg) to a display name that's recognized as an AI tool
    _CLI_DISPLAY_NAMES = {
        ('gh', 'copilot'): 'gh-copilot',
    }

    def __init__(self, target_cli: str, target_args: List[str]):
        self.target_cli = target_cli
        self.target_args = target_args

        # Compute a human-readable tool name for storage/display.
        # e.g. "gh copilot ..." → "gh-copilot" so it isn't filtered as a non-AI gh command.
        first_arg = target_args[0] if target_args else ''
        self.tool_name = self._CLI_DISPLAY_NAMES.get(
            (target_cli, first_arg), target_cli
        )
        self.tracker = LatencyTracker()
        self.storage = DataStorage()
        self.watcher = VoidWatcher()  # Phase 2: File system watcher
        self.git_analyzer = GitAnalyzer()  # Phase 3: Git analyzer
        self.snapshot_manager = SnapshotManager()  # Phase 5: Snapshot manager

        # Phase 6: Auto-save configuration
        self.auto_save_interval = 30  # Auto-save every 30 seconds
        self.auto_save_thread = None
        self.should_stop_auto_save = False
        self.session_start_time = None
        self.session_id = None  # Unique session identifier for updates
        self.pid_file = Path.home() / ".voidtally" / f"run_{os.getpid()}.pid"
        self.manual_save_requested = False  # Flag for manual save trigger

        # Save original terminal settings
        self.old_tty = None

    def _setup_terminal(self):
        """Set terminal to raw mode"""
        try:
            self.old_tty = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
        except termios.error:
            pass  # Non-TTY environment

    def _restore_terminal(self):
        """Restore terminal settings"""
        if self.old_tty:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.old_tty)
            except termios.error:
                pass

    def _handle_sigwinch(self, signum, frame):
        """Handle window resize signal (SIGWINCH)"""
        # Get current terminal window size
        s = struct.pack('HHHH', 0, 0, 0, 0)
        try:
            size = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, s)
            # Set PTY window size
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, size)
        except (OSError, IOError):
            pass

    def _handle_sigusr1(self, signum, frame):
        """Handle manual save trigger from board command (Phase 6)"""
        self.manual_save_requested = True
        print("\n💾 Manual save triggered by board command", file=sys.stderr, flush=True)

    def _proxy_data(self, master_fd: int) -> int:
        """
        Proxy data stream: stdin <-> PTY <-> stdout
        While monitoring Void time

        Returns child process exit code
        """
        try:
            while True:
                # Use select to monitor multiple file descriptors
                r, _, _ = select.select([sys.stdin, master_fd], [], [], 0.1)

                # Check if AI output has stopped and auto-finalize void time
                # This handles multi-terminal scenarios where user switches away
                if not r:
                    # No I/O activity, check for idle timeout
                    self.tracker.check_and_finalize_if_idle()

                if sys.stdin in r:
                    # User input -> PTY
                    try:
                        data = os.read(sys.stdin.fileno(), 1024)
                    except OSError:
                        break

                    if not data:
                        break

                    # Detect Enter key: start void time measurement
                    if b'\n' in data or b'\r' in data:
                        self.tracker.mark_input_received()
                    else:
                        # Any other key: end void time measurement
                        # Only printable characters (ASCII 32-126 or multi-byte UTF-8)
                        # count — this excludes ESC sequences (27), Ctrl keys (<32),
                        # arrow keys (\x1b[A etc.), and DEL (127).
                        has_visible_chars = any(
                            32 <= byte <= 126 or byte >= 128
                            for byte in data
                        )
                        if has_visible_chars:
                            self.tracker.mark_user_typing()

                    # Pass through to PTY (100% lossless)
                    os.write(master_fd, data)

                if master_fd in r:
                    # PTY -> User terminal
                    try:
                        data = os.read(master_fd, 1024)
                    except OSError:
                        break

                    if not data:
                        break

                    # Count meaningful characters (excludes ANSI escape sequences)
                    meaningful_char_count = count_meaningful_chars(data)

                    # Report character count to tracker for generation time metrics
                    if meaningful_char_count > 0:
                        self.tracker.mark_first_token_received(char_count=meaningful_char_count)

                    # Pass through to stdout (100% lossless)
                    os.write(sys.stdout.fileno(), data)

        except (KeyboardInterrupt, OSError):
            pass

        # Wait for child process to exit
        _, status = os.waitpid(self.child_pid, 0)
        return os.WEXITSTATUS(status) if os.WIFEXITED(status) else 1

    def _compute_and_save_stats(self, is_final: bool = False) -> None:
        """
        Compute and save current session statistics

        Args:
            is_final: Whether this is the final save (on exit)
        """
        try:
            # Get current statistics
            stats = self.tracker.get_statistics()
            changed_files = list(self.watcher.get_changed_files())

            # Compute snapshot diff
            snapshot_stats = None
            attribution_method = "unknown"

            if changed_files:
                try:
                    file_diffs = []
                    for filepath in changed_files:
                        diff = self.snapshot_manager.compute_diff(filepath)
                        if diff:
                            file_diffs.append(diff)

                    if file_diffs:
                        snapshot_stats = {
                            'total_loc_added': sum(d.loc_added for d in file_diffs),
                            'total_loc_deleted': sum(d.loc_deleted for d in file_diffs),
                            'file_changes': [file_diff_to_file_change(d) for d in file_diffs]
                        }
                        attribution_method = "snapshot"
                except Exception as e:
                    if is_final:
                        print(f"⚠️  Snapshot diff failed: {e}", file=sys.stderr)
                    snapshot_stats = None

            # Git fallback
            git_stats = None
            if changed_files and self.git_analyzer.is_git_repository():
                if not snapshot_stats:
                    git_stats = self.git_analyzer.get_files_diff_stats(changed_files)
                    attribution_method = "git"

            final_stats = snapshot_stats if snapshot_stats else (git_stats if git_stats else None)

            # Save or update session
            self.storage.save_session(
                self.tool_name,
                stats,
                changed_files=changed_files,
                git_stats=final_stats,
                attribution_method=attribution_method,
                session_id=self.session_id,
            )

            if not is_final:
                # Print auto-save notification (non-intrusive)
                print(f"\r💾 Auto-saved ({len(changed_files)} files)", end='', file=sys.stderr, flush=True)

        except Exception as e:
            print(f"⚠️  Failed to save stats: {e}", file=sys.stderr)

    def _auto_save_worker(self):
        """Background worker thread for auto-saving"""
        while not self.should_stop_auto_save:
            # Check for manual save request more frequently
            for _ in range(self.auto_save_interval * 2):  # Check every 0.5 seconds
                if self.should_stop_auto_save:
                    return
                if self.manual_save_requested:
                    self.manual_save_requested = False
                    self._compute_and_save_stats(is_final=False)
                    break
                time.sleep(0.5)
            else:
                # Regular auto-save interval reached
                if not self.should_stop_auto_save:
                    self._compute_and_save_stats(is_final=False)

    def run(self) -> int:
        """Run PTY proxy"""
        # Check if target command exists
        import shutil
        if not shutil.which(self.target_cli):
            print(f"❌ Error: Command '{self.target_cli}' not found in PATH", file=sys.stderr)
            print(f"\nPlease make sure '{self.target_cli}' is installed and available in your PATH.", file=sys.stderr)
            print(f"\nAvailable commands you can try:", file=sys.stderr)
            for cmd in ['python', 'python3', 'echo', 'date', 'ls']:
                if shutil.which(cmd):
                    print(f"  ✓ {cmd}", file=sys.stderr)
            return 127  # Command not found exit code

        # Build complete command
        cmd = [self.target_cli] + self.target_args

        # Create pseudo-terminal (PTY)
        self.child_pid, self.master_fd = pty.fork()

        if self.child_pid == 0:
            # Child process: execute target CLI
            os.execvp(self.target_cli, cmd)

        else:
            # Parent process: Proxy I/O
            # Register signal handlers
            signal.signal(signal.SIGWINCH, self._handle_sigwinch)
            signal.signal(signal.SIGUSR1, self._handle_sigusr1)  # Phase 6: Manual save trigger

            # Create PID file for board command to trigger manual saves
            try:
                self.pid_file.parent.mkdir(parents=True, exist_ok=True)
                self.pid_file.write_text(f"{os.getpid()}\n{os.getcwd()}\n{self.target_cli}")
            except Exception as e:
                print(f"⚠️  Failed to create PID file: {e}", file=sys.stderr)

            # Initialize window size
            self._handle_sigwinch(None, None)

            # Set terminal to raw mode
            self._setup_terminal()

            try:
                # Phase 2: Start file system monitoring
                self.watcher.start_watching()
                self.watcher.start_session()

                # Phase 5: Take snapshots of source files in the current directory
                # This allows accurate tracking of AI modifications to existing files
                try:
                    common_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.cpp', '.c', '.h',
                                       '.rs', '.rb', '.php', '.sh', '.yml', '.yaml', '.json', '.md', '.txt']
                    current_files = []
                    for ext in common_extensions:
                        current_files.extend(Path('.').rglob(f'*{ext}'))

                    # Snapshot at most 100 files to avoid excessive memory usage
                    snapshot_files = [str(f) for f in current_files[:100] if f.is_file()]
                    snapshot_count = self.snapshot_manager.take_snapshots(snapshot_files)
                    if snapshot_count > 0:
                        print(f"📸 Snapshot: {snapshot_count} files", file=sys.stderr)
                except Exception as e:
                    # Snapshot failure does not affect main flow
                    print(f"⚠️  Snapshot failed: {e}", file=sys.stderr)

                # Phase 6: Start auto-save background thread
                self.session_start_time = datetime.utcnow()
                self.session_id = f"{self.tool_name}_{self.session_start_time.isoformat()}"
                self.should_stop_auto_save = False
                self.auto_save_thread = threading.Thread(target=self._auto_save_worker, daemon=True)
                self.auto_save_thread.start()
                print(f"💾 Auto-save enabled (every {self.auto_save_interval}s)", file=sys.stderr)

                # Start proxying data
                exit_code = self._proxy_data(self.master_fd)

                # Phase 6: Stop auto-save thread
                self.should_stop_auto_save = True
                if self.auto_save_thread and self.auto_save_thread.is_alive():
                    self.auto_save_thread.join(timeout=2.0)

                # Phase 2: End file monitoring session
                watch_session = self.watcher.end_session()
                self.watcher.stop_watching()

                # Phase 6: Final save with complete statistics
                print("\n💾 Saving final session data...", file=sys.stderr)
                self._compute_and_save_stats(is_final=True)

                return exit_code

            finally:
                # Clean up PID file
                try:
                    if self.pid_file.exists():
                        self.pid_file.unlink()
                except Exception:
                    pass

                # Restore terminal settings
                self._restore_terminal()
                os.close(self.master_fd)


if __name__ == "__main__":
    # Test code
    import sys
    if len(sys.argv) > 1:
        observer = VoidObserver(sys.argv[1], sys.argv[2:])
        sys.exit(observer.run())
    else:
        print("Usage: void_observer.py <command> [args]")
        sys.exit(1)
