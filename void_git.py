#!/usr/bin/env python3
"""
Git 分析器 - Git Analyzer
统计代码变更的 LOC（Lines of Code）
"""

import os
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FileChange:
    """单个文件的变更统计"""
    path: str
    loc_added: int
    loc_deleted: int
    loc_net: int  # 净变更（added - deleted）


@dataclass
class GitStats:
    """Git Statistics"""
    total_loc_added: int
    total_loc_deleted: int
    total_loc_net: int
    files_changed: int
    file_changes: List[FileChange]


class GitAnalyzer:
    """
    Git 代码变更分析器

    基于 git diff 统计代码行数变更
    """

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize Git 分析器

        Args:
            repo_path: Git 仓库路径，默认为当前工作目录
        """
        self.repo_path = Path(repo_path or os.getcwd())
        self._is_git_repo = self._check_git_repo()

    def _check_git_repo(self) -> bool:
        """Check是否为 Git 仓库"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def is_git_repository(self) -> bool:
        """Check当前目录是否为 Git 仓库"""
        return self._is_git_repo

    def get_file_diff_stats(self, filepath: str) -> Optional[FileChange]:
        """
        Get单个文件的 Git Diff 统计

        Args:
            filepath: File path（相对于仓库根目录）

        Returns:
            FileChange 对象，If无法Get则Return None
        """
        if not self._is_git_repo:
            return None

        try:
            # Use git diff --numstat HEAD -- <file> Get统计
            result = subprocess.run(
                ['git', 'diff', '--numstat', 'HEAD', '--', filepath],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return None

            output = result.stdout.strip()
            if not output:
                # 文件未被追踪或无变更
                return FileChange(
                    path=filepath,
                    loc_added=0,
                    loc_deleted=0,
                    loc_net=0
                )

            # 解析 numstat 输出：added\tdeleted\tfilename
            parts = output.split('\t')
            if len(parts) >= 2:
                added_str, deleted_str = parts[0], parts[1]

                # Handle二进制文件（显示为 '-'）
                if added_str == '-' or deleted_str == '-':
                    return FileChange(
                        path=filepath,
                        loc_added=0,
                        loc_deleted=0,
                        loc_net=0
                    )

                loc_added = int(added_str)
                loc_deleted = int(deleted_str)

                return FileChange(
                    path=filepath,
                    loc_added=loc_added,
                    loc_deleted=loc_deleted,
                    loc_net=loc_added - loc_deleted
                )

        except (subprocess.TimeoutExpired, ValueError, subprocess.SubprocessError):
            pass

        return None

    def get_files_diff_stats(self, filepaths: List[str]) -> GitStats:
        """
        批量Get多个文件的 Git Diff 统计

        Args:
            filepaths: File path列表

        Returns:
            GitStats 对象
        """
        file_changes = []
        total_added = 0
        total_deleted = 0

        for filepath in filepaths:
            change = self.get_file_diff_stats(filepath)
            if change:
                file_changes.append(change)
                total_added += change.loc_added
                total_deleted += change.loc_deleted

        return GitStats(
            total_loc_added=total_added,
            total_loc_deleted=total_deleted,
            total_loc_net=total_added - total_deleted,
            files_changed=len(file_changes),
            file_changes=file_changes
        )

    def get_shortstat(self) -> Optional[Tuple[int, int, int]]:
        """
        Get git diff --shortstat 的统计

        Returns:
            (files_changed, insertions, deletions) 或 None
        """
        if not self._is_git_repo:
            return None

        try:
            result = subprocess.run(
                ['git', 'diff', '--shortstat', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return None

            output = result.stdout.strip()
            if not output:
                return (0, 0, 0)

            # 解析输出：1 file changed, 2 insertions(+), 3 deletions(-)
            files_match = re.search(r'(\d+) files? changed', output)
            insertions_match = re.search(r'(\d+) insertions?\(\+\)', output)
            deletions_match = re.search(r'(\d+) deletions?\(-\)', output)

            files_changed = int(files_match.group(1)) if files_match else 0
            insertions = int(insertions_match.group(1)) if insertions_match else 0
            deletions = int(deletions_match.group(1)) if deletions_match else 0

            return (files_changed, insertions, deletions)

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None

    def stage_and_commit(self, message: str, files: Optional[List[str]] = None):
        """
        暂存并提交文件（Test辅助方法）

        Args:
            message: 提交消息
            files: 要提交的文件列表，None 表示所有变更
        """
        if not self._is_git_repo:
            raise RuntimeError("Not a git repository")

        try:
            # 暂存文件
            if files:
                subprocess.run(['git', 'add'] + files, cwd=self.repo_path, check=True)
            else:
                subprocess.run(['git', 'add', '-A'], cwd=self.repo_path, check=True)

            # 提交
            subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Git commit failed: {e}")


if __name__ == "__main__":
    # Test code
    import tempfile
    import shutil

    print("Testing GitAnalyzer...")

    # Create临时 Git 仓库
    test_dir = tempfile.mkdtemp(prefix="voidtally_git_")
    print(f"Test directory: {test_dir}")

    try:
        # Initialize Git 仓库
        subprocess.run(['git', 'init'], cwd=test_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=test_dir, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=test_dir, check=True)

        # Create初始文件并提交
        (Path(test_dir) / "README.md").write_text("# Test Project\n")
        subprocess.run(['git', 'add', 'README.md'], cwd=test_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=test_dir, check=True, capture_output=True)

        # Create GitAnalyzer
        analyzer = GitAnalyzer(test_dir)
        assert analyzer.is_git_repository(), "Should be a git repository"
        print("✓ Git repository detected")

        # 修改文件（未提交）
        (Path(test_dir) / "README.md").write_text("# Test Project\n\nNew content\nMore lines\n")
        (Path(test_dir) / "new_file.py").write_text("def hello():\n    print('world')\n")

        # Test单文件统计
        readme_stats = analyzer.get_file_diff_stats("README.md")
        assert readme_stats is not None
        assert readme_stats.loc_added >= 2  # 至少增加了 2 行
        print(f"✓ README.md: +{readme_stats.loc_added} -{readme_stats.loc_deleted}")

        # Test多文件统计
        stats = analyzer.get_files_diff_stats(["README.md", "new_file.py"])
        assert stats.total_loc_added > 0
        assert len(stats.file_changes) == 2
        print(f"✓ Total: +{stats.total_loc_added} -{stats.total_loc_deleted}")

        # Test shortstat
        shortstat = analyzer.get_shortstat()
        assert shortstat is not None
        files, insertions, deletions = shortstat
        print(f"✓ Shortstat: {files} files, +{insertions}, -{deletions}")

        print("✅ GitAnalyzer test completed")

    finally:
        shutil.rmtree(test_dir)
        print("Cleaned up test directory")
