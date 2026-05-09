#!/usr/bin/env python3
"""
File System Watcher
Monitors file changes in project directory
"""

import os
import time
import threading
from pathlib import Path
from typing import Set, Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class FileChangeEvent:
    """File change event"""
    path: str
    timestamp: float
    change_type: str  # 'modified', 'created', 'deleted'


@dataclass
class WatchSession:
    """Watch session"""
    start_time: float
    end_time: Optional[float] = None
    changed_files: Set[str] = field(default_factory=set)
    events: List[FileChangeEvent] = field(default_factory=list)


class VoidWatcher:
    """
    File system watcher

    Uses polling to detect file changes (zero-dependency solution)
    Suitable for monitoring AI-generated code scenarios
    """

    def __init__(self, watch_dir: Optional[str] = None, poll_interval: float = 0.5):
        """
        Initialize watcher

        Args:
            watch_dir: Directory to watch, defaults to current working directory
            poll_interval: Polling interval (seconds), defaults to 0.5s
        """
        self.watch_dir = Path(watch_dir or os.getcwd()).resolve()
        self.poll_interval = poll_interval

        # File state snapshot {path: (mtime, size)}
        self.file_snapshot: Dict[str, tuple] = {}

        # Current session
        self.current_session: Optional[WatchSession] = None

        # Watch thread control
        self.watching = False
        self.watch_thread: Optional[threading.Thread] = None

        # Ignored file patterns
        self.ignore_patterns = {
            '.git', '.voidtally', '__pycache__', '.pyc',
            'node_modules', '.DS_Store', '.swp', '.swo'
        }

    def _should_ignore(self, path: Path) -> bool:
        """Check if file should be ignored"""
        path_str = str(path)

        # Ignore hidden files (filenames starting with .)
        if path.name.startswith('.'):
            return True

        # Ignore specific patterns
        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return True

        return False

    def _scan_directory(self) -> Dict[str, tuple]:
        """Scan directory and return file state snapshot"""
        snapshot = {}

        try:
            for root, dirs, files in os.walk(self.watch_dir):
                # Filter directories to ignore
                dirs[:] = [d for d in dirs if not any(
                    pattern in d for pattern in self.ignore_patterns
                )]

                for filename in files:
                    filepath = Path(root) / filename

                    if self._should_ignore(filepath):
                        continue

                    try:
                        stat = filepath.stat()
                        rel_path = str(filepath.relative_to(self.watch_dir))
                        snapshot[rel_path] = (stat.st_mtime, stat.st_size)
                    except (OSError, ValueError):
                        continue

        except Exception as e:
            # Directory scan error (e.g., permission issues), handle silently
            pass

        return snapshot

    def _detect_changes(self) -> List[FileChangeEvent]:
        """Detect file changes"""
        current_snapshot = self._scan_directory()
        changes = []
        current_time = time.time()

        # Detect modifications and creations
        for path, (mtime, size) in current_snapshot.items():
            if path in self.file_snapshot:
                old_mtime, old_size = self.file_snapshot[path]
                if mtime > old_mtime or size != old_size:
                    changes.append(FileChangeEvent(
                        path=path,
                        timestamp=current_time,
                        change_type='modified'
                    ))
            else:
                changes.append(FileChangeEvent(
                    path=path,
                    timestamp=current_time,
                    change_type='created'
                ))

        # Detect deletions
        for path in self.file_snapshot:
            if path not in current_snapshot:
                changes.append(FileChangeEvent(
                    path=path,
                    timestamp=current_time,
                    change_type='deleted'
                ))

        # Update snapshot
        self.file_snapshot = current_snapshot

        return changes

    def _watch_loop(self):
        """Watch loop (runs in separate thread)"""
        # Initialize snapshot
        self.file_snapshot = self._scan_directory()

        while self.watching:
            changes = self._detect_changes()

            # Record changes to current session
            if self.current_session and changes:
                for event in changes:
                    self.current_session.changed_files.add(event.path)
                    self.current_session.events.append(event)

            time.sleep(self.poll_interval)

    def start_watching(self):
        """Start file monitoring"""
        if self.watching:
            return

        self.watching = True
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()

    def stop_watching(self):
        """Stop file monitoring"""
        self.watching = False
        if self.watch_thread:
            self.watch_thread.join(timeout=2.0)

    def start_session(self) -> WatchSession:
        """开始新的Watch session"""
        self.current_session = WatchSession(start_time=time.time())
        return self.current_session

    def end_session(self) -> Optional[WatchSession]:
        """结束当前Watch session"""
        if self.current_session:
            self.current_session.end_time = time.time()
            session = self.current_session
            self.current_session = None
            return session
        return None

    def get_changed_files(self) -> Set[str]:
        """Get list of changed files in current session"""
        if self.current_session:
            return self.current_session.changed_files.copy()
        return set()


if __name__ == "__main__":
    # Test code
    import tempfile
    import shutil

    print("Testing VoidWatcher...")

    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="voidtally_test_")
    print(f"Test directory: {test_dir}")

    try:
        watcher = VoidWatcher(test_dir, poll_interval=0.2)
        watcher.start_watching()
        watcher.start_session()

        print("\nCreating test files...")
        time.sleep(0.3)

        # Create file
        test_file1 = Path(test_dir) / "test1.txt"
        test_file1.write_text("Hello VoidTally")

        time.sleep(0.3)

        # Modify file
        test_file1.write_text("Hello VoidTally - Modified")

        time.sleep(0.3)

        # Create another file
        test_file2 = Path(test_dir) / "test2.py"
        test_file2.write_text("print('test')")

        time.sleep(0.5)

        # End session
        session = watcher.end_session()
        watcher.stop_watching()

        print(f"\nSession results:")
        print(f"  Duration: {session.end_time - session.start_time:.2f}s")
        print(f"  Changed files: {len(session.changed_files)}")
        for filepath in sorted(session.changed_files):
            print(f"    - {filepath}")

        print(f"\n✅ VoidWatcher test completed")

    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"Cleaned up test directory")
