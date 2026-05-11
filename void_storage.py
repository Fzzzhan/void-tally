#!/usr/bin/env python3
"""
Data Storage
JSONL format storage to ~/.voidtally/data.jsonl
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Optional
from void_tracker import SessionStatistics


class DataStorage:
    """Data storage manager"""

    # Blacklist for non-AI tools (test tools and basic commands)
    # Any tool NOT in this list is considered an AI tool
    NON_AI_TOOL_BLACKLIST = {
        # Basic shell commands
        'echo', 'date', 'ls', 'pwd', 'whoami', 'cat', 'grep', 'find',
        'mkdir', 'rm', 'cp', 'mv', 'touch', 'chmod', 'chown', 'ln',
        'sed', 'awk', 'sort', 'uniq', 'wc', 'head', 'tail', 'less', 'more',
        'diff', 'patch', 'tar', 'gzip', 'zip', 'unzip',

        # Version control (non-AI)
        'git', 'gh', 'svn', 'hg', 'bzr',

        # Package managers (non-AI)
        'npm', 'yarn', 'pnpm', 'pip', 'pip3', 'pipenv', 'poetry',
        'cargo', 'gem', 'brew', 'apt', 'apt-get', 'yum', 'dnf',

        # Build tools (non-AI)
        'make', 'cmake', 'gcc', 'g++', 'clang', 'rustc', 'javac',
        'mvn', 'gradle', 'ant', 'bazel', 'ninja',

        # Interpreters/Compilers (non-AI when used standalone)
        'python', 'python3', 'node', 'ruby', 'perl', 'php', 'java',
        'bash', 'sh', 'zsh', 'fish', 'csh', 'tcsh',

        # Text editors (non-AI)
        'vim', 'vi', 'nvim', 'emacs', 'nano', 'pico',

        # System utilities (non-AI)
        'ps', 'top', 'htop', 'kill', 'killall', 'df', 'du', 'free',
        'uname', 'uptime', 'history', 'env', 'export', 'source',

        # Network tools (non-AI)
        'curl', 'wget', 'ssh', 'scp', 'rsync', 'ping', 'telnet',
        'nc', 'netstat', 'ifconfig', 'ip',

        # Container/VM tools (non-AI)
        'docker', 'docker-compose', 'kubectl', 'k9s', 'podman',
        'vagrant', 'vbox', 'qemu',
    }

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize data storage

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

    def is_ai_tool(self, tool_name: str) -> bool:
        """
        Determine if a tool is a real AI tool (not a test or basic command)

        Args:
            tool_name: Tool name to check

        Returns:
            True if it's a real AI tool, False otherwise
        """
        if not tool_name:
            return False

        tool_lower = tool_name.lower()

        # Exclude tools containing 'test'
        if 'test' in tool_lower:
            return False

        # Exclude basic commands
        if tool_name in self.NON_AI_TOOL_BLACKLIST:
            return False

        # Exclude scripts (starting with ./ or ../)
        if tool_name.startswith('./') or tool_name.startswith('../'):
            return False

        # Everything else is considered an AI tool
        return True

    def save_session(self, tool_name: str, stats: SessionStatistics,
                     loc_added: int = 0, loc_deleted: int = 0,
                     changed_files: list = None, git_stats=None,
                     attribution_method: str = "unknown",
                     session_id: str = None) -> None:
        """
        Save session statistics

        Args:
            tool_name: Target CLI tool name
            stats: Statistics
            loc_added: Lines of code added (deprecated, use git_stats)
            loc_deleted: Lines of code deleted (deprecated, use git_stats)
            changed_files: List of changed files (Phase 2)
            git_stats: Git/Snapshot statistics (Phase 3/5)
            attribution_method: Attribution method "snapshot"|"git"|"unknown" (Phase 5)
            session_id: Unique identifier for this observer session (used for deduplication)
        """
        if changed_files is None:
            changed_files = []

        # Phase 5: Handle snapshot stats (dict) or Git stats (GitStats object)
        file_changes_list = []
        if git_stats:
            if isinstance(git_stats, dict):
                # Snapshot stats (dict format)
                loc_added = git_stats.get('total_loc_added', 0)
                loc_deleted = git_stats.get('total_loc_deleted', 0)
                file_changes_list = git_stats.get('file_changes', [])
            else:
                # Git stats (GitStats object)
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
        # Get current working directory
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
            # Phase 5: Attribution method
            "attribution_method": attribution_method,
            # Session deduplication key (auto-saves of the same session share this ID)
            "session_id": session_id,
        }

        # Append to JSONL file
        with open(self.data_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def load_all_sessions(self, include_all: bool = False) -> List[Dict]:
        """
        Load all session data

        Args:
            include_all: If True, include all sessions (tests, basic commands).
                        If False (default), only include real AI tools.

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
                        session = json.loads(line)
                        # Filter by AI tool unless include_all is True
                        if include_all or self.is_ai_tool(session.get('tool', '')):
                            sessions.append(session)
                    except json.JSONDecodeError:
                        continue  # Skip corrupted lines

        return sessions

    def deduplicate_sessions(self, sessions: List[Dict]) -> List[Dict]:
        """
        Deduplicate sessions by keeping the most complete record for each session.

        Strategy:
        1. Records with a session_id are grouped by session_id and the record with
           the highest void_duration_ms is kept.
        2. Legacy records without a session_id are grouped by (tool, project_path)
           and merged using a 5-minute time window.
        """
        sessions_with_id = [s for s in sessions if s.get("session_id")]
        sessions_without_id = [s for s in sessions if not s.get("session_id")]

        unique_sessions: List[Dict] = []

        if sessions_with_id:
            by_session_id: Dict[str, List[Dict]] = defaultdict(list)
            for session in sessions_with_id:
                by_session_id[session["session_id"]].append(session)

            for sid_group in by_session_id.values():
                best = max(sid_group, key=lambda s: s.get("void_duration_ms", 0))
                unique_sessions.append(best)

        if sessions_without_id:
            grouped: Dict = defaultdict(list)
            for session in sessions_without_id:
                key = (session.get("tool"), session.get("project_path"))
                grouped[key].append(session)

            for group_sessions in grouped.values():
                sorted_sessions = sorted(group_sessions, key=lambda s: s.get("timestamp", ""))
                if not sorted_sessions:
                    continue

                window_sessions = [sorted_sessions[0]]
                for session in sorted_sessions[1:]:
                    try:
                        previous_time = datetime.fromisoformat(
                            window_sessions[-1].get("timestamp", "").replace("Z", "+00:00")
                        )
                        session_time = datetime.fromisoformat(
                            session.get("timestamp", "").replace("Z", "+00:00")
                        )
                        if (session_time - previous_time) > timedelta(minutes=5):
                            window_sessions.append(session)
                        elif session.get("void_duration_ms", 0) >= window_sessions[-1].get("void_duration_ms", 0):
                            window_sessions[-1] = session
                    except ValueError:
                        window_sessions.append(session)

                unique_sessions.extend(window_sessions)

        unique_sessions.sort(key=lambda s: s.get("timestamp", ""))
        return unique_sessions

    def load_sessions_by_date(self, date: datetime, include_all: bool = False,
                              deduplicate: bool = False) -> List[Dict]:
        """
        Load session data for a specific date

        Args:
            date: Target date
            include_all: If True, include all sessions. If False (default), only AI tools.
            deduplicate: If True, merge auto-saves and duplicate session records first.

        Returns:
            List of session data
        """
        all_sessions = self.load_all_sessions(include_all=include_all)
        if deduplicate:
            all_sessions = self.deduplicate_sessions(all_sessions)
        date_str = date.strftime("%Y-%m-%d")

        return [
            session for session in all_sessions
            if session.get("timestamp", "").startswith(date_str)
        ]

    def get_statistics_summary(self, tool_filter: Optional[str] = None,
                             project_filter: Optional[str] = None,
                             include_all: bool = False,
                             deduplicate: bool = True) -> Dict:
        """
        Get statistics summary

        Args:
            tool_filter: Optional tool name filter (e.g., "aider", "claude-cli")
            project_filter: Optional project path filter (e.g., "/home/user/project1")
            include_all: If True, include all sessions. If False (default), only AI tools.
            deduplicate: If True (default), merge auto-saves and duplicate session records.

        Returns:
            Dictionary containing overall statistics
        """
        sessions = self.load_all_sessions(include_all=include_all)

        # Apply tool filter
        if tool_filter:
            sessions = [s for s in sessions if s.get("tool") == tool_filter]

        # Apply project filter
        if project_filter:
            sessions = [s for s in sessions if s.get("project_path") == project_filter]

        if deduplicate:
            sessions = self.deduplicate_sessions(sessions)

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
        Get list of all tools used

        Returns:
            List of tool names (deduplicated and sorted)
        """
        sessions = self.load_all_sessions()
        tools = set(s.get("tool", "unknown") for s in sessions)
        return sorted(list(tools))

    def get_available_projects(self) -> List[str]:
        """
        Get list of all project paths used

        Returns:
            List of project paths (deduplicated and sorted)
        """
        sessions = self.load_all_sessions()
        projects = set(s.get("project_path", "unknown") for s in sessions)
        return sorted(list(projects))

    def get_daily_stats(self, days: int = 7,
                       tool_filter: Optional[str] = None,
                       project_filter: Optional[str] = None,
                       include_all: bool = False,
                       deduplicate: bool = True) -> List[Dict]:
        """
        Get daily aggregated statistics for the past N days

        Args:
            days: Number of days to look back (default: 7)
            tool_filter: Optional tool name filter
            project_filter: Optional project path filter
            include_all: If True, include all sessions. If False (default), only AI tools.
            deduplicate: If True (default), merge auto-saves and duplicate session records.

        Returns:
            List of daily statistics, one dict per day:
            [
                {
                    "date": "2026-05-10",
                    "sessions": 5,
                    "total_void_ms": 12500,
                    "total_gen_ms": 300000,
                    "total_loc_added": 150,
                    "total_loc_deleted": 45
                },
                ...
            ]
        """
        from datetime import datetime, timedelta, timezone

        # Generate date range (past N days including today) — use UTC to match stored timestamps
        today = datetime.now(timezone.utc)
        date_list = [(today - timedelta(days=i)).strftime("%Y-%m-%d")
                     for i in range(days - 1, -1, -1)]

        # Load all sessions (with AI tool filtering)
        all_sessions = self.load_all_sessions(include_all=include_all)

        # Apply additional filters
        if tool_filter:
            all_sessions = [s for s in all_sessions if s.get("tool") == tool_filter]
        if project_filter:
            all_sessions = [s for s in all_sessions if s.get("project_path") == project_filter]

        if deduplicate:
            all_sessions = self.deduplicate_sessions(all_sessions)

        # Group sessions by date
        daily_data = {date: [] for date in date_list}

        for session in all_sessions:
            timestamp = session.get("timestamp", "")
            if not timestamp:
                continue

            # Extract date from timestamp (YYYY-MM-DD)
            date_str = timestamp[:10]

            if date_str in daily_data:
                daily_data[date_str].append(session)

        # Aggregate statistics for each day
        result = []
        for date in date_list:
            sessions = daily_data[date]

            if not sessions:
                # No data for this day
                result.append({
                    "date": date,
                    "sessions": 0,
                    "total_void_ms": 0,
                    "total_gen_ms": 0,
                    "total_loc_added": 0,
                    "total_loc_deleted": 0
                })
            else:
                # Aggregate data
                result.append({
                    "date": date,
                    "sessions": len(sessions),
                    "total_void_ms": sum(s.get("void_duration_ms", 0) for s in sessions),
                    "total_gen_ms": sum(s.get("gen_duration_ms", 0) for s in sessions),
                    "total_loc_added": sum(s.get("loc_added", 0) for s in sessions),
                    "total_loc_deleted": sum(s.get("loc_deleted", 0) for s in sessions)
                })

        return result

    def clear_all_data(self, backup: bool = True) -> bool:
        """
        Clear all data

        Args:
            backup: Whether to back up data before deleting (default: True)

        Returns:
            True if successfully cleared
        """
        import shutil
        from datetime import datetime

        if not self.data_file.exists():
            # File does not exist, nothing to clear
            return True

        # Backup data
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.data_dir / f"data.jsonl.backup_{timestamp}"
            try:
                shutil.copy2(self.data_file, backup_file)
            except Exception as e:
                raise RuntimeError(f"Failed to backup data: {e}")

        # Delete data file
        try:
            self.data_file.unlink()
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete data file: {e}")


if __name__ == "__main__":
    # Test code
    from void_tracker import SessionStatistics

    storage = DataStorage()

    # Create test data
    test_stats = SessionStatistics(
        total_void_time_ms=1250.5,
        total_gen_time_ms=30000.0,
        void_count=3,
        average_void_time_ms=416.83,
        average_gen_time_ms=10000.0,
        min_void_time_ms=200.0,
        max_void_time_ms=800.0,
    )

    # Save test session
    storage.save_session("test-cli", test_stats, loc_added=45, loc_deleted=12)
    print(f"Test session saved to: {storage.data_file}")

    # Load and display
    summary = storage.get_statistics_summary()
    print(f"\nStatistics Summary:")
    print(f"  Total Sessions: {summary['total_sessions']}")
    print(f"  Total Void Time: {summary['total_void_time_ms']:.2f}ms")
    print(f"  Avg Void per Session: {summary['avg_void_per_session_ms']:.2f}ms")
