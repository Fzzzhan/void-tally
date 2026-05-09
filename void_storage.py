#!/usr/bin/env python3
"""
Data Storage
JSONL format storage to ~/.voidtally/data.jsonl
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from void_tracker import SessionStatistics


class DataStorage:
    """Data storage manager"""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize数据存储

        Args:
            data_dir: Data directory path, defaults to ~/.voidtally
        """
        if data_dir is None:
            self.data_dir = Path.home() / ".voidtally"
        else:
            self.data_dir = Path(data_dir)

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.data_file = self.data_dir / "data.jsonl"

    def save_session(self, tool_name: str, stats: SessionStatistics,
                     loc_added: int = 0, loc_deleted: int = 0,
                     changed_files: list = None, git_stats=None,
                     attribution_method: str = "unknown") -> None:
        """
        Save会话Statistics

        Args:
            tool_name: Target CLI tool name
            stats: Statistics
            loc_added: 新增代码行数（已弃用，Use git_stats）
            loc_deleted: Delete代码行数（已弃用，Use git_stats）
            changed_files: List of changed files (Phase 2)
            git_stats: Git/Snapshot Statistics（Phase 3/5）
            attribution_method: Attribution method "snapshot"|"git"|"unknown" (Phase 5)
        """
        if changed_files is None:
            changed_files = []

        # Phase 5: Handle快照统计（dict）或 Git 统计（GitStats 对象）
        file_changes_list = []
        if git_stats:
            if isinstance(git_stats, dict):
                # 快照Statistics（dict 格式）
                loc_added = git_stats.get('total_loc_added', 0)
                loc_deleted = git_stats.get('total_loc_deleted', 0)
                file_changes_list = git_stats.get('file_changes', [])
            else:
                # Git Statistics（GitStats 对象）
                loc_added = git_stats.total_loc_added
                loc_deleted = git_stats.total_loc_deleted
                file_changes_list = [
                    {
                        "path": fc.path,
                        "loc_added": fc.loc_added,
                        "loc_deleted": fc.loc_deleted,
                        "loc_net": fc.loc_net
                    }
                    for fc in git_stats.file_changes
                ]
        # Get当前工作目录
        try:
            project_path = os.getcwd()
        except OSError:
            project_path = "unknown"

        # Build data entry (conforming to PRD format)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tool": tool_name,
            "void_duration_ms": int(stats.total_void_time_ms),
            "gen_duration_ms": int(stats.total_gen_time_ms),
            "loc_added": loc_added,
            "loc_deleted": loc_deleted,
            "project_path": project_path,
            # Additional statistics
            "void_count": stats.void_count,
            "avg_void_ms": round(stats.average_void_time_ms, 2),
            "min_void_ms": round(stats.min_void_time_ms, 2),
            "max_void_ms": round(stats.max_void_time_ms, 2),
            # Phase 2: File change information
            "changed_files": changed_files,
            "files_changed_count": len(changed_files),
            # Phase 3/5: Detailed file change statistics
            "file_changes": file_changes_list,
            # Phase 5: 归因方法Mark
            "attribution_method": attribution_method,
        }

        # Append to JSONL file
        with open(self.data_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def load_all_sessions(self) -> List[Dict]:
        """
        Load所有会话数据

        Returns:
            List of session data
        """
        if not self.data_file.exists():
            return []

        sessions = []
        with open(self.data_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        sessions.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # Skip corrupted lines

        return sessions

    def load_sessions_by_date(self, date: datetime) -> List[Dict]:
        """
        Load指定日期的会话数据

        Args:
            date: Target date

        Returns:
            List of session data
        """
        all_sessions = self.load_all_sessions()
        date_str = date.strftime("%Y-%m-%d")

        return [
            session for session in all_sessions
            if session.get("timestamp", "").startswith(date_str)
        ]

    def get_statistics_summary(self, tool_filter: Optional[str] = None,
                             project_filter: Optional[str] = None) -> Dict:
        """
        Get统计摘要

        Args:
            tool_filter: Optional tool name filter (e.g., "aider", "claude-cli")
            project_filter: Optional project path filter (e.g., "/home/user/project1")
                          If都为 None，则Return所有数据的聚合统计

        Returns:
            Dictionary containing overall statistics
        """
        sessions = self.load_all_sessions()

        # Apply工具过滤
        if tool_filter:
            sessions = [s for s in sessions if s.get("tool") == tool_filter]

        # Apply项目过滤
        if project_filter:
            sessions = [s for s in sessions if s.get("project_path") == project_filter]

        if not sessions:
            return {
                "total_sessions": 0,
                "total_void_time_ms": 0,
                "total_gen_time_ms": 0,
                "total_loc_added": 0,
                "total_loc_deleted": 0,
                "tool_filter": tool_filter,
                "project_filter": project_filter,
            }

        return {
            "total_sessions": len(sessions),
            "total_void_time_ms": sum(s.get("void_duration_ms", 0) for s in sessions),
            "total_gen_time_ms": sum(s.get("gen_duration_ms", 0) for s in sessions),
            "total_loc_added": sum(s.get("loc_added", 0) for s in sessions),
            "total_loc_deleted": sum(s.get("loc_deleted", 0) for s in sessions),
            "total_files_changed": sum(s.get("files_changed_count", 0) for s in sessions),  # Phase 2
            "avg_void_per_session_ms": sum(s.get("void_duration_ms", 0) for s in sessions) / len(sessions),
            "tool_filter": tool_filter,
            "project_filter": project_filter,
        }

    def get_available_tools(self) -> List[str]:
        """
        Get所有Use过的工具列表

        Returns:
            List of tool names (deduplicated and sorted)
        """
        sessions = self.load_all_sessions()
        tools = set(s.get("tool", "unknown") for s in sessions)
        return sorted(list(tools))

    def get_available_projects(self) -> List[str]:
        """
        Get所有Use过的项目路径列表

        Returns:
            List of project paths (deduplicated and sorted)
        """
        sessions = self.load_all_sessions()
        projects = set(s.get("project_path", "unknown") for s in sessions)
        return sorted(list(projects))

    def clear_all_data(self, backup: bool = True) -> bool:
        """
        Clear所有数据

        Args:
            backup: 是否在Delete前Backup data（默认为 True）

        Returns:
            是否成功Clear
        """
        import shutil
        from datetime import datetime

        if not self.data_file.exists():
            # 文件不存在，无需Clear
            return True

        # Backup data
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.data_dir / f"data.jsonl.backup_{timestamp}"
            try:
                shutil.copy2(self.data_file, backup_file)
            except Exception as e:
                # 备份失败，不继续Delete
                raise RuntimeError(f"Failed to backup data: {e}")

        # Delete数据文件
        try:
            self.data_file.unlink()
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete data file: {e}")


if __name__ == "__main__":
    # Test code
    from void_tracker import SessionStatistics

    storage = DataStorage()

    # CreateTest数据
    test_stats = SessionStatistics(
        total_void_time_ms=1250.5,
        total_gen_time_ms=30000.0,
        void_count=3,
        average_void_time_ms=416.83,
        average_gen_time_ms=10000.0,
        min_void_time_ms=200.0,
        max_void_time_ms=800.0,
    )

    # SaveTest会话
    storage.save_session("test-cli", test_stats, loc_added=45, loc_deleted=12)
    print(f"Test session saved to: {storage.data_file}")

    # Load并显示
    summary = storage.get_statistics_summary()
    print(f"\nStatistics Summary:")
    print(f"  Total Sessions: {summary['total_sessions']}")
    print(f"  Total Void Time: {summary['total_void_time_ms']:.2f}ms")
    print(f"  Avg Void per Session: {summary['avg_void_per_session_ms']:.2f}ms")
