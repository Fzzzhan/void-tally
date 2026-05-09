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
from pathlib import Path
from typing import List, Optional
from void_tracker import LatencyTracker
from void_storage import DataStorage
from void_watcher import VoidWatcher
from void_git import GitAnalyzer  # Phase 3
from void_snapshot import SnapshotManager, file_diff_to_file_change  # Phase 5


class VoidObserver:
    """PTY transparent proxy core class"""

    def __init__(self, target_cli: str, target_args: List[str]):
        self.target_cli = target_cli
        self.target_args = target_args
        self.tracker = LatencyTracker()
        self.storage = DataStorage()
        self.watcher = VoidWatcher()  # Phase 2: 文件系统监听器
        self.git_analyzer = GitAnalyzer()  # Phase 3: Git 分析器
        self.snapshot_manager = SnapshotManager()  # Phase 5: 快照管理器

        # Save原始终端设置
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
        """Handle窗口大小变化信号（SIGWINCH）"""
        # Get当前终端窗口大小
        s = struct.pack('HHHH', 0, 0, 0, 0)
        try:
            size = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, s)
            # Set PTY window size
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, size)
        except (OSError, IOError):
            pass

    def _proxy_data(self, master_fd: int) -> int:
        """
        Proxy data stream: stdin <-> PTY <-> stdout
        While monitoring Void time

        Return子进程退出码
        """
        try:
            while True:
                # Use select 监听多个文件描述符
                r, _, _ = select.select([sys.stdin, master_fd], [], [], 0.1)

                if sys.stdin in r:
                    # User input -> PTY
                    try:
                        data = os.read(sys.stdin.fileno(), 1024)
                    except OSError:
                        break

                    if not data:
                        break

                    # Detect回车符（触发 Void 计时）
                    if b'\n' in data or b'\r' in data:
                        self.tracker.mark_input_received()

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

                    # Detect首个非空字符（TTFT - Time To First Token）
                    for byte in data:
                        # Skip whitespace characters
                        if byte not in (ord(' '), ord('\t'), ord('\n'), ord('\r'), 0):
                            self.tracker.mark_first_token_received()
                            break

                    # Pass through to stdout (100% lossless)
                    os.write(sys.stdout.fileno(), data)

        except (KeyboardInterrupt, OSError):
            pass

        # Wait for child process to exit
        _, status = os.waitpid(self.child_pid, 0)
        return os.WEXITSTATUS(status) if os.WIFEXITED(status) else 1

    def run(self) -> int:
        """Run PTY 代理"""
        # Check目标命令是否存在
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

        # Create伪终端
        self.child_pid, self.master_fd = pty.fork()

        if self.child_pid == 0:
            # 子进程：Execute目标 CLI
            os.execvp(self.target_cli, cmd)

        else:
            # Parent process: Proxy I/O
            # 注册 SIGWINCH 信号Handle器
            signal.signal(signal.SIGWINCH, self._handle_sigwinch)

            # Initialize窗口大小
            self._handle_sigwinch(None, None)

            # 设置终端为原始模式
            self._setup_terminal()

            try:
                # Phase 2: Start文件系统监听
                self.watcher.start_watching()
                self.watcher.start_session()

                # Phase 5: 对当前目录的源代码文件Create快照
                # This allows accurate tracking of AI modifications to existing files
                try:
                    common_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.cpp', '.c', '.h',
                                       '.rs', '.rb', '.php', '.sh', '.yml', '.yaml', '.json', '.md', '.txt']
                    current_files = []
                    for ext in common_extensions:
                        current_files.extend(Path('.').rglob(f'*{ext}'))

                    # 只对前100个文件Create快照（避免过多内存消耗）
                    snapshot_files = [str(f) for f in current_files[:100] if f.is_file()]
                    snapshot_count = self.snapshot_manager.take_snapshots(snapshot_files)
                    if snapshot_count > 0:
                        print(f"📸 Snapshot: {snapshot_count} files", file=sys.stderr)
                except Exception as e:
                    # Snapshot failure does not affect main flow
                    print(f"⚠️  Snapshot failed: {e}", file=sys.stderr)

                # Start代理数据
                exit_code = self._proxy_data(self.master_fd)

                # Phase 2: End文件监听会话
                watch_session = self.watcher.end_session()
                self.watcher.stop_watching()

                # SaveStatistics（包含File change information）
                stats = self.tracker.get_statistics()
                changed_files = list(watch_session.changed_files) if watch_session else []

                # Phase 5: Use快照系统Calculate精确的 LOC 变更
                snapshot_stats = None
                attribution_method = "unknown"

                if changed_files:
                    # 尝试Use快照系统（精确归因）
                    try:
                        # 对变更的文件Calculate差异
                        file_diffs = []
                        for filepath in changed_files:
                            diff = self.snapshot_manager.compute_diff(filepath)
                            if diff:
                                file_diffs.append(diff)

                        if file_diffs:
                            # 成功Use快照统计
                            snapshot_stats = {
                                'total_loc_added': sum(d.loc_added for d in file_diffs),
                                'total_loc_deleted': sum(d.loc_deleted for d in file_diffs),
                                'file_changes': [file_diff_to_file_change(d) for d in file_diffs]
                            }
                            attribution_method = "snapshot"
                    except Exception as e:
                        # 快照失败，将Use Git 作为 fallback
                        print(f"⚠️  Snapshot diff failed: {e}", file=sys.stderr)
                        snapshot_stats = None

                # Phase 3: Git Diff analysis (as fallback)
                git_stats = None
                if changed_files and self.git_analyzer.is_git_repository():
                    # If快照统计失败，Use Git
                    if not snapshot_stats:
                        git_stats = self.git_analyzer.get_files_diff_stats(changed_files)
                        attribution_method = "git"

                # 选择最佳的Statistics
                final_stats = snapshot_stats if snapshot_stats else (git_stats if git_stats else None)

                # Save会话数据
                self.storage.save_session(
                    self.target_cli,
                    stats,
                    changed_files=changed_files,
                    git_stats=final_stats,  # Use快照或 Git 统计
                    attribution_method=attribution_method  # Mark归因方法
                )

                return exit_code

            finally:
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
