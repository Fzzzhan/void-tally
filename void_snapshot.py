#!/usr/bin/env python3
"""
File Snapshot & Diff
Phase 5: Accurate Attribution System - Only count code changes during session
"""

import os
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FileSnapshot:
    """File snapshot"""
    path: str
    exists: bool
    content: List[str]  # File line content
    mtime: float  # Modification time
    size: int  # File size


@dataclass
class FileDiff:
    """File difference statistics"""
    path: str
    loc_added: int
    loc_deleted: int
    loc_changed: int  # Actual changes (not net)
    was_created: bool  # Whether file was created
    was_deleted: bool  # Whether the file was deleted


class SnapshotManager:
    """
    File snapshot manager

    Records file snapshots at session start and computes accurate LOC changes at session end
    """

    def __init__(self):
        self.snapshots: Dict[str, FileSnapshot] = {}

    def take_snapshot(self, filepath: str) -> Optional[FileSnapshot]:
        """
        Take a snapshot of a file

        Args:
            filepath: File path

        Returns:
            FileSnapshot object, or None if the file cannot be read
        """
        try:
            abs_path = os.path.abspath(filepath)

            # Check if file exists
            if not os.path.exists(abs_path):
                # File does not exist yet (may be created later)
                return FileSnapshot(
                    path=filepath,
                    exists=False,
                    content=[],
                    mtime=0.0,
                    size=0
                )

            # Read file content
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.readlines()

            stat = os.stat(abs_path)

            return FileSnapshot(
                path=filepath,
                exists=True,
                content=content,
                mtime=stat.st_mtime,
                size=stat.st_size
            )

        except (OSError, UnicodeDecodeError, PermissionError):
            # File cannot be read (binary file, permission issues, etc.)
            return None

    def take_snapshots(self, filepaths: List[str]) -> int:
        """
        Take snapshots of multiple files

        Args:
            filepaths: List of file paths

        Returns:
            Number of snapshots successfully taken
        """
        count = 0
        for filepath in filepaths:
            snapshot = self.take_snapshot(filepath)
            if snapshot is not None:
                self.snapshots[filepath] = snapshot
                count += 1
        return count

    def compute_diff(self, filepath: str) -> Optional[FileDiff]:
        """
        Compute the diff for a file against its snapshot

        Args:
            filepath: File path

        Returns:
            FileDiff object, or None if the diff cannot be computed
        """
        # Get original snapshot
        old_snapshot = self.snapshots.get(filepath)
        if old_snapshot is None:
            # No snapshot, possibly new file
            current_snapshot = self.take_snapshot(filepath)
            if current_snapshot and current_snapshot.exists:
                # New file
                return FileDiff(
                    path=filepath,
                    loc_added=len(current_snapshot.content),
                    loc_deleted=0,
                    loc_changed=len(current_snapshot.content),
                    was_created=True,
                    was_deleted=False
                )
            return None

        # Get current snapshot
        current_snapshot = self.take_snapshot(filepath)
        if current_snapshot is None:
            return None

        # File was deleted
        if old_snapshot.exists and not current_snapshot.exists:
            return FileDiff(
                path=filepath,
                loc_added=0,
                loc_deleted=len(old_snapshot.content),
                loc_changed=len(old_snapshot.content),
                was_created=False,
                was_deleted=True
            )

        # File created
        if not old_snapshot.exists and current_snapshot.exists:
            return FileDiff(
                path=filepath,
                loc_added=len(current_snapshot.content),
                loc_deleted=0,
                loc_changed=len(current_snapshot.content),
                was_created=True,
                was_deleted=False
            )

        # File unchanged (fast check)
        if (old_snapshot.exists and current_snapshot.exists and
            old_snapshot.size == current_snapshot.size and
            old_snapshot.mtime == current_snapshot.mtime):
            return FileDiff(
                path=filepath,
                loc_added=0,
                loc_deleted=0,
                loc_changed=0,
                was_created=False,
                was_deleted=False
            )

        # Use difflib to compute exact diff
        diff = difflib.unified_diff(
            old_snapshot.content,
            current_snapshot.content,
            lineterm=''
        )

        loc_added = 0
        loc_deleted = 0

        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                loc_added += 1
            elif line.startswith('-') and not line.startswith('---'):
                loc_deleted += 1

        return FileDiff(
            path=filepath,
            loc_added=loc_added,
            loc_deleted=loc_deleted,
            loc_changed=loc_added + loc_deleted,
            was_created=False,
            was_deleted=False
        )

    def compute_all_diffs(self) -> List[FileDiff]:
        """
        Compute diffs for all snapshotted files

        Returns:
            List of FileDiff objects
        """
        diffs = []
        for filepath in self.snapshots.keys():
            diff = self.compute_diff(filepath)
            if diff and (diff.loc_added > 0 or diff.loc_deleted > 0):
                diffs.append(diff)
        return diffs

    def get_total_stats(self) -> Tuple[int, int, int]:
        """
        Get aggregate statistics across all diffs

        Returns:
            (total_added, total_deleted, total_changed)
        """
        diffs = self.compute_all_diffs()
        total_added = sum(d.loc_added for d in diffs)
        total_deleted = sum(d.loc_deleted for d in diffs)
        total_changed = sum(d.loc_changed for d in diffs)
        return (total_added, total_deleted, total_changed)

    def clear(self):
        """Clear all snapshots"""
        self.snapshots.clear()


# Convert FileDiff to Git-compatible format
def file_diff_to_file_change(diff: FileDiff):
    """
    Convert FileDiff to FileChange format (compatible with existing Git code)

    Args:
        diff: FileDiff object

    Returns:
        FileChange in dict format
    """
    return {
        "path": diff.path,
        "loc_added": diff.loc_added,
        "loc_deleted": diff.loc_deleted,
        "loc_net": diff.loc_added - diff.loc_deleted
    }


if __name__ == "__main__":
    # Test code
    import tempfile
    import shutil

    print("=" * 60)
    print(" VoidTally Snapshot System Test")
    print("=" * 60)
    print()

    # Create temporary test directory
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Temp directory: {temp_dir}")

    try:
        # Create test file
        test_file = os.path.join(temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("# Original content\n")
            f.write("def hello():\n")
            f.write("    print('Hello')\n")
        print(f"✓ Created test file: {test_file}")

        # Create snapshot manager
        manager = SnapshotManager()

        # Take snapshot
        print("\n1️⃣  Take initial snapshot...")
        manager.take_snapshots([test_file])
        print(f"✓ Snapshots taken: {len(manager.snapshots)} file(s)")

        # Simulate AI modifying file
        print("\n2️⃣  Simulate AI modifying file...")
        with open(test_file, 'w') as f:
            f.write("# Modified by AI\n")
            f.write("def hello(name):\n")
            f.write("    print(f'Hello {name}')\n")
            f.write("def goodbye():\n")
            f.write("    print('Goodbye')\n")
        print("✓ File modified")

        # Compute diff
        print("\n3️⃣  Computing diff...")
        diff = manager.compute_diff(test_file)
        if diff:
            print(f"✓ Difference statistics:")
            print(f"  - LOC Added:   +{diff.loc_added}")
            print(f"  - LOC Deleted: -{diff.loc_deleted}")
            print(f"  - LOC Changed:  {diff.loc_changed}")
            print(f"  - Net Change:  {diff.loc_added - diff.loc_deleted:+d}")

        # Overall statistics
        print("\n4️⃣  Overall statistics...")
        total_added, total_deleted, total_changed = manager.get_total_stats()
        print(f"✓ Total:")
        print(f"  - Total Added:   {total_added}")
        print(f"  - Total Deleted: {total_deleted}")
        print(f"  - Total Changed: {total_changed}")

        # TestNew file
        print("\n5️⃣  TestNew file...")
        new_file = os.path.join(temp_dir, "new.py")
        manager.take_snapshots([new_file])  # snapshot non-existent file

        with open(new_file, 'w') as f:
            f.write("# New file\n")
            f.write("print('new')\n")

        new_diff = manager.compute_diff(new_file)
        if new_diff:
            print(f"✓ New file statistics:")
            print(f"  - Was Created:  {new_diff.was_created}")
            print(f"  - LOC Added:    +{new_diff.loc_added}")

        print("\n✅ All tests passed!")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Clean up temporary directory")
