#!/usr/bin/env python3
"""
The Dashboard
Phase 4: Rich TUI Implementation
"""

import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from void_storage import DataStorage

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class VoidDashboard:
    """TUI Dashboard - Phase 4 Complete Implementation"""

    def __init__(self, tool_filter: str = None, project_filter: str = None):
        self.storage = DataStorage()
        self.console = Console() if RICH_AVAILABLE else None
        self.tool_filter = tool_filter
        self.project_filter = project_filter

    def run(self) -> int:
        """Run the dashboard display"""
        if not RICH_AVAILABLE:
            return self._run_text_mode()

        return self._run_rich_mode()

    def _run_text_mode(self):
        """Plain text mode (fallback)"""
        print("=" * 60)
        print(" VoidTally Dashboard - Text Mode")
        print(" (Install 'rich' for enhanced TUI: pip install rich)")
        print("=" * 60)
        print()

        summary = self.storage.get_statistics_summary(self.tool_filter, self.project_filter)
        today_sessions = self.storage.load_sessions_by_date(datetime.now(timezone.utc), deduplicate=True)

        # Apply filters to session list (consistent with summary)
        if self.tool_filter or self.project_filter:
            if self.tool_filter:
                today_sessions = [s for s in today_sessions if s.get("tool") == self.tool_filter]
            if self.project_filter:
                today_sessions = [s for s in today_sessions if s.get("project_path") == self.project_filter]

        print("📊 Overall Statistics")
        print("-" * 60)
        print(f"  Total Sessions: {summary['total_sessions']}")
        print(f"  Total Void Time: {self._format_duration(summary['total_void_time_ms'])}")
        print(f"  Total LOC Added: {summary['total_loc_added']}")
        print(f"  Total LOC Deleted: {summary['total_loc_deleted']}")
        print()
        print(f"📅 Today ({datetime.now().strftime('%Y-%m-%d')})")
        print("-" * 60)
        print(f"  Sessions: {len(today_sessions)}")

        return 0

    def _run_rich_mode(self):
        """Rich TUI mode"""
        # Load data
        all_sessions = self.storage.load_all_sessions()
        today_sessions = self.storage.load_sessions_by_date(datetime.now(timezone.utc))

        # Apply filters to session list (consistent with summary)
        if self.tool_filter or self.project_filter:
            if self.tool_filter:
                all_sessions = [s for s in all_sessions if s.get("tool") == self.tool_filter]
                today_sessions = [s for s in today_sessions if s.get("tool") == self.tool_filter]
            if self.project_filter:
                all_sessions = [s for s in all_sessions if s.get("project_path") == self.project_filter]
                today_sessions = [s for s in today_sessions if s.get("project_path") == self.project_filter]

        # Deduplicate sessions FIRST: keep only the latest record for each unique session
        unique_all_sessions = self._deduplicate_sessions(all_sessions)
        unique_today_sessions = self._deduplicate_sessions(today_sessions)

        # Recalculate statistics based on unique sessions
        summary = self._calculate_summary(unique_all_sessions)
        daily_stats = self._calculate_daily_stats(unique_all_sessions, days=7)

        # Create all panels first
        recent_sessions = unique_all_sessions[-10:] if unique_all_sessions else []

        panels = [
            ("header", self._create_header_panel()),
            ("stats", self._create_stats_panel(summary)),
            ("trend", self._create_trend_panel(daily_stats)),
            ("today", self._create_today_panel(unique_today_sessions)),
            ("sessions", self._create_sessions_table(recent_sessions)),
            ("files", self._create_file_details_panel(recent_sessions)),
        ]

        # Display panels one by one (no fixed layout to avoid terminal size issues)
        for name, panel in panels:
            self.console.print(panel)

        # Show data file location
        self.console.print()
        self.console.print(f"[dim]Data file: {self.storage.data_file}[/dim]")

        return 0

    def _create_header_panel(self) -> Panel:
        """Create header panel"""
        header_text = "VoidTally Dashboard"
        filters = []
        if self.tool_filter:
            filters.append(f"Tool: {self.tool_filter}")
        if self.project_filter:
            # Show project name (last part of path)
            project_name = os.path.basename(self.project_filter) or self.project_filter
            filters.append(f"Project: {project_name}")

        if filters:
            header_text = f"VoidTally Dashboard [{', '.join(filters)}]"

        return Panel(
            Text(header_text, style="bold cyan", justify="center"),
            style="cyan",
            box=box.HEAVY
        )

    def _create_stats_panel(self, summary: Dict) -> Panel:
        """Create the statistics cards panel"""
        total_void_ms = summary['total_void_time_ms']
        net_loc = summary['total_loc_added'] - summary['total_loc_deleted']
        total_loc_changed = summary['total_loc_added'] + summary['total_loc_deleted']  # total changes (additions and deletions both represent productive work)
        sessions = summary['total_sessions']

        # Calculate efficiency (use total changes; deleting code is also valuable work)
        if total_void_ms > 0 and total_loc_changed > 0:
            # Efficiency = (total changes / wait time) * normalization factor
            efficiency = (total_loc_changed / (total_void_ms / 60000)) * 10  # normalize to a human-readable value
        else:
            efficiency = 0

        # Build three-column stats cards
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)

        # Card 1: Total Void
        void_text = Text()
        void_text.append(f"{self._format_duration(total_void_ms)}\n", style="bold yellow")
        void_text.append(f"{sessions} sessions", style="dim")
        card1 = Panel(
            void_text,
            title="[yellow]⏱ Total Void[/yellow]",
            border_style="yellow",
            padding=(1, 2)
        )

        # Card 2: Total LOC Changed (additions + deletions)
        loc_text = Text()
        loc_style = "green"  # always green: both additions and deletions are productive work
        loc_text.append(f"{total_loc_changed:,}\n", style=f"bold {loc_style}")
        loc_text.append(
            f"+{summary['total_loc_added']:,} -{summary['total_loc_deleted']:,}",
            style="dim"
        )
        card2 = Panel(
            loc_text,
            title=f"[{loc_style}]📝 Total LOC[/{loc_style}]",
            border_style=loc_style,
            padding=(1, 2)
        )

        # Card 3: Efficiency
        eff_text = Text()
        eff_text.append(f"{efficiency:.1f}\n", style="bold cyan")
        eff_text.append("LOC/min·void", style="dim")
        card3 = Panel(
            eff_text,
            title="[cyan]⚡ Efficiency[/cyan]",
            border_style="cyan",
            padding=(1, 2)
        )

        grid.add_row(card1, card2, card3)

        return Panel(grid, title="📊 Overall Statistics", border_style="blue")

    def _create_trend_panel(self, daily_stats: List[Dict]) -> Panel:
        """Create 7-day void time trend panel with ASCII bar chart"""
        if not daily_stats or all(day["total_void_ms"] == 0 for day in daily_stats):
            content = Text("No data available for trend analysis.", style="dim italic")
            return Panel(
                content,
                title="[cyan]📈 7-Day Void Time Trend[/cyan]",
                border_style="cyan"
            )

        # Find max value for scaling
        max_void_ms = max(day["total_void_ms"] for day in daily_stats)

        # Create ASCII bar chart
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Date", style="dim", width=10)
        table.add_column("Bar", width=40)
        table.add_column("Value", justify="right", style="cyan", width=10)

        for day in daily_stats:
            date_str = day["date"][5:]  # Show MM-DD only
            void_ms = day["total_void_ms"]
            sessions = day["sessions"]

            # Calculate bar width (max 30 characters)
            if max_void_ms > 0:
                bar_width = int((void_ms / max_void_ms) * 30)
            else:
                bar_width = 0

            # Create bar
            if sessions == 0:
                bar = Text("·" * 30, style="dim")
                value_str = "-"
            else:
                bar = Text("█" * bar_width, style="yellow")
                if bar_width < 30:
                    bar.append("·" * (30 - bar_width), style="dim")
                value_str = self._format_duration(void_ms)

            table.add_row(date_str, bar, value_str)

        return Panel(
            table,
            title="[cyan]📈 7-Day Void Time Trend[/cyan]",
            border_style="cyan"
        )

    def _create_today_panel(self, today_sessions: List[Dict]) -> Panel:
        """Create today's activity panel"""
        today_str = datetime.now().strftime('%Y-%m-%d')

        if not today_sessions:
            content = Text("No sessions today yet.", style="dim italic")
            return Panel(
                content,
                title=f"[green]📅 Today's Activity ({today_str})[/green]",
                border_style="green"
            )

        # Aggregate today's data
        today_void = sum(s.get("void_duration_ms", 0) for s in today_sessions)
        today_loc_added = sum(s.get("loc_added", 0) for s in today_sessions)
        today_loc_deleted = sum(s.get("loc_deleted", 0) for s in today_sessions)
        today_files = sum(s.get("files_changed_count", 0) for s in today_sessions)

        # Phase 5: Count attribution methods
        attribution_counts = {}
        for s in today_sessions:
            method = s.get("attribution_method", "unknown")
            attribution_counts[method] = attribution_counts.get(method, 0) + 1

        # Build table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")

        table.add_row("Sessions", str(len(today_sessions)))
        table.add_row("Void Time", self._format_duration(today_void))
        table.add_row(
            "LOC",
            f"[green]+{today_loc_added}[/green] [red]-{today_loc_deleted}[/red] "
            f"[white](net: {today_loc_added - today_loc_deleted:+d})[/white]"
        )
        table.add_row("Files Changed", str(today_files))

        # Phase 5: Show attribution method breakdown
        if attribution_counts:
            attribution_str = " ".join([
                f"📸{attribution_counts.get('snapshot', 0)}" if attribution_counts.get('snapshot', 0) > 0 else "",
                f"🔀{attribution_counts.get('git', 0)}" if attribution_counts.get('git', 0) > 0 else "",
                f"❓{attribution_counts.get('unknown', 0)}" if attribution_counts.get('unknown', 0) > 0 else ""
            ]).strip()
            if attribution_str:
                table.add_row("Attribution", attribution_str)

        return Panel(
            table,
            title=f"[green]📅 Today's Activity ({today_str})[/green]",
            border_style="green"
        )

    def _create_sessions_table(self, recent_sessions: List[Dict]) -> Panel:
        """Create the recent sessions table"""
        if not recent_sessions:
            content = Text("No sessions recorded yet.", style="dim italic")
            return Panel(
                content,
                title="[magenta]📋 Recent Sessions[/magenta]",
                border_style="magenta"
            )

        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.SIMPLE,
            padding=(0, 1),
            expand=False
        )

        table.add_column("Time", style="dim", width=11)
        table.add_column("Tool", style="cyan", width=10)
        table.add_column("Void", justify="right", width=7)
        table.add_column("LOC", justify="right", width=12)
        table.add_column("Attr", justify="center", width=4)
        table.add_column("Files", style="yellow", width=28, no_wrap=True, overflow="ellipsis")

        # Add recent sessions in reverse chronological order
        for session in reversed(recent_sessions):
            timestamp = session.get("timestamp", "")
            # Format timestamp as local time
            if timestamp:
                try:
                    # Parse UTC timestamp and convert to local timezone
                    dt_utc = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    dt_local = dt_utc.astimezone()  # Convert to local timezone
                    time_str = dt_local.strftime("%m-%d %H:%M")  # Compact: MM-DD HH:MM
                except:
                    time_str = timestamp[:11]
            else:
                time_str = "N/A"

            tool = session.get("tool", "unknown")
            void_ms = session.get("void_duration_ms", 0)
            loc_added = session.get("loc_added", 0)
            loc_deleted = session.get("loc_deleted", 0)
            files_count = session.get("files_changed_count", 0)

            # GetFile change details
            file_changes = session.get("file_changes", [])
            changed_files = session.get("changed_files", [])

            # Format file list for display
            if file_changes:
                # Prefer detailed file_changes (includes LOC info)
                file_names = [fc.get("path", "") for fc in file_changes if fc.get("path")]
            elif changed_files:
                # Fall back to simple changed_files list
                file_names = changed_files
            else:
                file_names = []

            # Limit displayed file count to avoid overly wide tables
            if len(file_names) == 0:
                files_str = f"[dim]{files_count} file(s)[/dim]"
            elif len(file_names) <= 2:
                # 1-2 files: show filename only
                short_names = [Path(f).name for f in file_names]
                files_str = ", ".join(short_names)
            else:
                # 3+ files: show first 2 filenames + remaining count
                short_names = [Path(f).name for f in file_names[:2]]
                remaining = len(file_names) - 2
                files_str = f"{', '.join(short_names)} +{remaining}"

            # Compact LOC display
            if loc_added > 0 or loc_deleted > 0:
                loc_str = f"+{loc_added}/-{loc_deleted}"
            else:
                loc_str = "0"

            # Phase 5: Get attribution method icon
            attribution_method = session.get("attribution_method", "unknown")
            attribution_icon = {
                "snapshot": "📸",
                "git": "🔀",
                "unknown": "❓"
            }.get(attribution_method, "❓")

            table.add_row(
                time_str,
                tool,
                self._format_duration(void_ms),
                loc_str,
                attribution_icon,
                files_str
            )

        return Panel(
            table,
            title=f"[magenta]📋 Recent Sessions (Last {len(recent_sessions)})[/magenta]",
            border_style="magenta"
        )

    def _deduplicate_sessions(self, sessions: List[Dict]) -> List[Dict]:
        """
        Deduplicate sessions by keeping only the latest record for each unique session.

        Strategy:
        1. Records with a 'session_id' field: group by session_id, keep the latest
           (highest void_duration_ms = most complete auto-save or final save).
        2. Legacy records without 'session_id': group by (tool, project_path) and
           use a 5-minute time window to merge adjacent records from the same session.

        This correctly handles the case where two consecutive copilot sessions
        start within 5 minutes of each other — the old time-window approach would
        erroneously merge them and discard the first session's accumulated void time.

        Args:
            sessions: List of all sessions

        Returns:
            List of unique sessions (latest/most-complete record for each)
        """
        return self.storage.deduplicate_sessions(sessions)

    def _calculate_summary(self, sessions: List[Dict]) -> Dict:
        """
        Calculate summary statistics from deduplicated sessions

        Args:
            sessions: List of unique sessions

        Returns:
            Summary dictionary with aggregated statistics
        """
        total_sessions = len(sessions)
        total_void_time_ms = sum(s.get('void_duration_ms', 0) for s in sessions)
        total_gen_time_ms = sum(s.get('gen_duration_ms', 0) for s in sessions)
        total_loc_added = sum(s.get('loc_added', 0) for s in sessions)
        total_loc_deleted = sum(s.get('loc_deleted', 0) for s in sessions)

        return {
            'total_sessions': total_sessions,
            'total_void_time_ms': total_void_time_ms,
            'total_gen_time_ms': total_gen_time_ms,
            'total_loc_added': total_loc_added,
            'total_loc_deleted': total_loc_deleted,
        }

    def _calculate_daily_stats(self, sessions: List[Dict], days: int = 7) -> List[Dict]:
        """
        Calculate daily statistics from deduplicated sessions

        Args:
            sessions: List of unique sessions
            days: Number of days to look back

        Returns:
            List of daily statistics
        """
        from collections import defaultdict
        from datetime import datetime, timedelta, timezone

        # Group by date
        daily_data = defaultdict(lambda: {
            'sessions': 0,
            'total_void_ms': 0,
            'total_loc_added': 0,
            'total_loc_deleted': 0,
        })

        for session in sessions:
            timestamp_str = session.get('timestamp', '')
            if not timestamp_str:
                continue

            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                date_key = dt.date().isoformat()

                daily_data[date_key]['sessions'] += 1
                daily_data[date_key]['total_void_ms'] += session.get('void_duration_ms', 0)
                daily_data[date_key]['total_loc_added'] += session.get('loc_added', 0)
                daily_data[date_key]['total_loc_deleted'] += session.get('loc_deleted', 0)
            except:
                continue

        # Generate last N days
        today = datetime.now(timezone.utc).date()
        result = []
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            date_key = date.isoformat()
            data = daily_data.get(date_key, {
                'sessions': 0,
                'total_void_ms': 0,
                'total_loc_added': 0,
                'total_loc_deleted': 0,
            })
            result.append({
                'date': date_key,
                **data
            })

        return result

    def _create_file_details_panel(self, recent_sessions: List[Dict]) -> Panel:
        """Create the file details panel for the most recent session"""
        if not recent_sessions:
            content = Text("No file changes recorded.", style="dim italic")
            return Panel(
                content,
                title="[blue]📄 File Details (Latest Session)[/blue]",
                border_style="blue"
            )

        # Get the most recent session
        latest_session = recent_sessions[-1]
        file_changes = latest_session.get("file_changes", [])
        tool = latest_session.get("tool", "unknown")
        timestamp = latest_session.get("timestamp", "")

        # Get total LOC stats (fallback display)
        loc_added = latest_session.get("loc_added", 0)
        loc_deleted = latest_session.get("loc_deleted", 0)
        changed_files = latest_session.get("changed_files", [])

        if not file_changes:
            # Check if total LOC data is available (fallback display)
            if loc_added > 0 or loc_deleted > 0 or changed_files:
                # Have totals but no details
                content = Text()
                content.append("⚠️  ", style="yellow")
                content.append("Detailed file statistics not available.\n", style="dim")
                content.append("(Data from Phase 1/2 or non-Git repository)\n\n", style="dim italic")

                # Show total statistics
                content.append("Total Statistics:\n", style="bold")
                content.append(f"  LOC Added:    ", style="cyan")
                content.append(f"+{loc_added}\n", style="green")
                content.append(f"  LOC Deleted:  ", style="cyan")
                content.append(f"-{loc_deleted}\n", style="red")
                content.append(f"  Total Changed: ", style="cyan")
                content.append(f"{loc_added + loc_deleted}\n", style="yellow")

                if changed_files:
                    content.append(f"\n  Files: ", style="cyan")
                    file_list = ", ".join([Path(f).name for f in changed_files[:5]])
                    if len(changed_files) > 5:
                        file_list += f" +{len(changed_files) - 5} more"
                    content.append(file_list, style="dim")

                return Panel(
                    content,
                    title=f"[blue]📄 File Details ({tool})[/blue]",
                    border_style="blue"
                )
            else:
                # No data at all
                content = Text("No file changes recorded.", style="dim italic")
                return Panel(
                    content,
                    title=f"[blue]📄 File Details ({tool})[/blue]",
                    border_style="blue"
                )

        # Build file details table
        table = Table(
            show_header=True,
            header_style="bold blue",
            box=box.SIMPLE,
            padding=(0, 1)
        )

        table.add_column("File", style="cyan")
        table.add_column("Added", justify="right", style="green")
        table.add_column("Deleted", justify="right", style="red")
        table.add_column("Changed", justify="right", style="yellow")

        total_files = len(file_changes)
        for fc in file_changes[:10]:  # show at most 10 files
            path = fc.get("path", "")
            loc_added = fc.get("loc_added", 0)
            loc_deleted = fc.get("loc_deleted", 0)
            total_changed = loc_added + loc_deleted

            # Show filename only (not full path)
            file_name = Path(path).name if path else "unknown"

            table.add_row(
                file_name,
                f"+{loc_added}",
                f"-{loc_deleted}",
                str(total_changed)
            )

        if total_files > 10:
            table.add_row(
                f"[dim]... and {total_files - 10} more files[/dim]",
                "", "", ""
            )

        # Format title timestamp
        try:
            # Parse UTC timestamp and convert to local timezone
            dt_utc = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            dt_local = dt_utc.astimezone()  # Convert to local timezone
            time_str = dt_local.strftime("%H:%M")
        except:
            time_str = "recent"

        # Phase 5: Show attribution method
        attribution_method = latest_session.get("attribution_method", "unknown")
        attribution_icon = {
            "snapshot": "📸",  # Snapshot - Accurate attribution
            "git": "🔀",        # Git - Fallback mode
            "unknown": "❓"     # Unknown - Old data
        }.get(attribution_method, "❓")

        attribution_label = {
            "snapshot": "Snapshot (Accurate)",
            "git": "Git (Fallback)",
            "unknown": "Unknown"
        }.get(attribution_method, "Unknown")

        return Panel(
            table,
            title=f"[blue]📄 File Details ({tool} @ {time_str}) {attribution_icon} {attribution_label}[/blue]",
            border_style="blue"
        )

    def _format_duration(self, ms: float) -> str:
        """Format duration display"""
        if ms < 1000:
            return f"{ms:.0f}ms"
        elif ms < 60000:
            return f"{ms/1000:.1f}s"
        elif ms < 3600000:
            minutes = int(ms / 60000)
            seconds = (ms % 60000) / 1000
            return f"{minutes}m {seconds:.0f}s"
        else:
            hours = int(ms / 3600000)
            minutes = int((ms % 3600000) / 60000)
            return f"{hours}h {minutes}m"


if __name__ == "__main__":
    dashboard = VoidDashboard()
    sys.exit(dashboard.run())
