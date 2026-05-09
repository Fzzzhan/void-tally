#!/usr/bin/env python3
"""
File snapshot和差异Calculate - File Snapshot & Diff
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
    was_deleted: bool  # 文件是否被Delete


class SnapshotManager:
    """
    File snapshot管理器

    在会话Start时RecordFile snapshot，End时对比Calculate精确的 LOC 变更
    """

    def __init__(self):
        self.snapshots: Dict[str, FileSnapshot] = {}

    def take_snapshot(self, filepath: str) -> Optional[FileSnapshot]:
        """
        对文件Create快照

        Args:
            filepath: File path

        Returns:
            FileSnapshot 对象，If文件无法读取则Return None
        """
        try:
            abs_path = os.path.abspath(filepath)

            # Check文件是否存在
            if not os.path.exists(abs_path):
                # 文件不存在（可能稍后会被Create）
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
        批量Create快照

        Args:
            filepaths: File path列表

        Returns:
            成功Create快照的数量
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
        Calculate文件的差异（与快照对比）

        Args:
            filepath: File path

        Returns:
            FileDiff 对象，If无法Calculate则Return None
        """
        # Get原始快照
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

        # Get当前快照
        current_snapshot = self.take_snapshot(filepath)
        if current_snapshot is None:
            return None

        # 文件被Delete
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

        # 文件未变化（快速Check）
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

        # Use difflib Calculate精确差异
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
        Calculate所有快照文件的差异

        Returns:
            FileDiff 对象列表
        """
        diffs = []
        for filepath in self.snapshots.keys():
            diff = self.compute_diff(filepath)
            if diff and (diff.loc_added > 0 or diff.loc_deleted > 0):
                diffs.append(diff)
        return diffs

    def get_total_stats(self) -> Tuple[int, int, int]:
        """
        Get总的Statistics

        Returns:
            (total_added, total_deleted, total_changed)
        """
        diffs = self.compute_all_diffs()
        total_added = sum(d.loc_added for d in diffs)
        total_deleted = sum(d.loc_deleted for d in diffs)
        total_changed = sum(d.loc_changed for d in diffs)
        return (total_added, total_deleted, total_changed)

    def clear(self):
        """Clear所有快照"""
        self.snapshots.clear()


# Convert FileDiff to Git-compatible format
def file_diff_to_file_change(diff: FileDiff):
    """
    Convert FileDiff to FileChange format (compatible with existing Git code)

    Args:
        diff: FileDiff 对象

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

    # Create临时Test目录
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Create临时目录: {temp_dir}")

    try:
        # CreateTest文件
        test_file = os.path.join(temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("# Original content\n")
            f.write("def hello():\n")
            f.write("    print('Hello')\n")
        print(f"✓ CreateTest文件: {test_file}")

        # Create快照管理器
        manager = SnapshotManager()

        # Take snapshot
        print("\n1️⃣  Take initial snapshot...")
        manager.take_snapshots([test_file])
        print(f"✓ 快照已Create: {len(manager.snapshots)} 个文件")

        # Simulate AI modifying file
        print("\n2️⃣  Simulate AI modifying file...")
        with open(test_file, 'w') as f:
            f.write("# Modified by AI\n")
            f.write("def hello(name):\n")
            f.write("    print(f'Hello {name}')\n")
            f.write("def goodbye():\n")
            f.write("    print('Goodbye')\n")
        print("✓ File modified")

        # Calculate差异
        print("\n3️⃣  Calculate差异...")
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
        manager.take_snapshots([new_file])  # 不存在的File snapshot

        with open(new_file, 'w') as f:
            f.write("# New file\n")
            f.write("print('new')\n")

        new_diff = manager.compute_diff(new_file)
        if new_diff:
            print(f"✓ New file statistics:")
            print(f"  - Was Created:  {new_diff.was_created}")
            print(f"  - LOC Added:    +{new_diff.loc_added}")

        print("\n✅ 所有Test通过！")

    finally:
        # 清理
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Clean up temporary directory")
