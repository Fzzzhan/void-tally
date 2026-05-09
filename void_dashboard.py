#!/usr/bin/env python3
"""
The Dashboard
Phase 4: Rich TUI Implementation
"""

import sys
import os
from datetime import datetime
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

    # ROI Calculate常量（来自 PRD line 98）
    HUMAN_CODING_CONSTANT = 1.0  # Human coding rate: 1 LOC = 1 minute (conservative estimate)

    def __init__(self, tool_filter: str = None, project_filter: str = None):
        self.storage = DataStorage()
        self.console = Console() if RICH_AVAILABLE else None
        self.tool_filter = tool_filter
        self.project_filter = project_filter

    def run(self) -> int:
        """Run看板显示"""
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
        today_sessions = self.storage.load_sessions_by_date(datetime.now())

        print("📊 Overall Statistics")
        print("-" * 60)
        print(f"  Total Sessions: {summary['total_sessions']}")
        print(f"  Total Void Time: {self._format_duration(summary['total_void_time_ms'])}")
        print(f"  Total LOC Added: {summary['total_loc_added']}")
        print(f"  Total LOC Deleted: {summary['total_loc_deleted']}")

        if summary['total_sessions'] > 0:
            roi = self._calculate_roi(summary)
            print(f"  ROI: {roi:.2f}%")

        print()
        print(f"📅 Today ({datetime.now().strftime('%Y-%m-%d')})")
        print("-" * 60)
        print(f"  Sessions: {len(today_sessions)}")

        return 0

    def _run_rich_mode(self):
        """Rich TUI mode"""
        # Load数据
        summary = self.storage.get_statistics_summary(self.tool_filter, self.project_filter)
        all_sessions = self.storage.load_all_sessions()
        today_sessions = self.storage.load_sessions_by_date(datetime.now())

        # Create主布局
        layout = Layout()

        # Layout structure:
        # ┌─────────────────────────────────────────┐
        # │              Header                      │
        # ├─────────────────────────────────────────┤
        # │              Stats Cards                 │
        # ├─────────────────────────────────────────┤
        # │         Today's Activity                 │
        # ├─────────────────────────────────────────┤
        # │         Recent Sessions                  │
        # ├─────────────────────────────────────────┤
        # │         File Details                     │
        # ├─────────────────────────────────────────┤
        # │          ROI Analysis                    │
        # └─────────────────────────────────────────┘

        layout.split(
            Layout(name="header", size=3),
            Layout(name="stats", size=7),
            Layout(name="today", size=10),
            Layout(name="sessions", size=12),
            Layout(name="files", size=10),
            Layout(name="roi", size=12),
        )

        # 1. Header
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

        layout["header"].update(
            Panel(
                Text(header_text, style="bold cyan", justify="center"),
                style="cyan",
                box=box.HEAVY
            )
        )

        # 2. Stats Cards
        layout["stats"].update(self._create_stats_panel(summary))

        # 3. Today's Activity
        layout["today"].update(self._create_today_panel(today_sessions))

        # 4. Recent Sessions
        recent_sessions = all_sessions[-10:] if all_sessions else []
        layout["sessions"].update(self._create_sessions_table(recent_sessions))

        # 5. File Details (Latest Session)
        layout["files"].update(self._create_file_details_panel(recent_sessions))

        # 6. ROI Analysis
        layout["roi"].update(self._create_roi_panel(summary))

        # 显示
        self.console.print(layout)

        # 显示数据文件位置
        self.console.print()
        self.console.print(f"[dim]Data file: {self.storage.data_file}[/dim]")

        return 0

    def _create_stats_panel(self, summary: Dict) -> Panel:
        """Create统计卡片面板"""
        total_void_ms = summary['total_void_time_ms']
        net_loc = summary['total_loc_added'] - summary['total_loc_deleted']
        total_loc_changed = summary['total_loc_added'] + summary['total_loc_deleted']  # 总变更量（增删都是正向工作）
        sessions = summary['total_sessions']

        # Calculate效率增益（Use总变更量，因为Delete代码也是有价值的工作）
        if total_void_ms > 0 and total_loc_changed > 0:
            # Efficiency = (total changes / wait time) * normalization factor
            efficiency = (total_loc_changed / (total_void_ms / 60000)) * 10  # 归一化为易读数值
        else:
            efficiency = 0

        # Create三列统计卡片
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)

        # 卡片 1: Total Void
        void_text = Text()
        void_text.append(f"{self._format_duration(total_void_ms)}\n", style="bold yellow")
        void_text.append(f"{sessions} sessions", style="dim")
        card1 = Panel(
            void_text,
            title="[yellow]⏱ Total Void[/yellow]",
            border_style="yellow",
            padding=(1, 2)
        )

        # 卡片 2: Total LOC Changed（总变更量，增删都是正向工作）
        loc_text = Text()
        loc_style = "green"  # 总是绿色，因为增删都是正向工作
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

        # 卡片 3: Efficiency
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

    def _create_today_panel(self, today_sessions: List[Dict]) -> Panel:
        """Create今日活动面板"""
        today_str = datetime.now().strftime('%Y-%m-%d')

        if not today_sessions:
            content = Text("No sessions today yet.", style="dim italic")
            return Panel(
                content,
                title=f"[green]📅 Today's Activity ({today_str})[/green]",
                border_style="green"
            )

        # 统计今日数据
        today_void = sum(s.get("void_duration_ms", 0) for s in today_sessions)
        today_gen = sum(s.get("gen_duration_ms", 0) for s in today_sessions)
        today_loc_added = sum(s.get("loc_added", 0) for s in today_sessions)
        today_loc_deleted = sum(s.get("loc_deleted", 0) for s in today_sessions)
        today_files = sum(s.get("files_changed_count", 0) for s in today_sessions)

        # Phase 5: 统计归因方法
        attribution_counts = {}
        for s in today_sessions:
            method = s.get("attribution_method", "unknown")
            attribution_counts[method] = attribution_counts.get(method, 0) + 1

        # Create表格
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")

        table.add_row("Sessions", str(len(today_sessions)))
        table.add_row("Void Time", self._format_duration(today_void))
        table.add_row("Gen Time", self._format_duration(today_gen))
        table.add_row(
            "LOC",
            f"[green]+{today_loc_added}[/green] [red]-{today_loc_deleted}[/red] "
            f"[white](net: {today_loc_added - today_loc_deleted:+d})[/white]"
        )
        table.add_row("Files Changed", str(today_files))

        # Phase 5: Show attribution method统计
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
        """Create最近会话表格"""
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
            padding=(0, 1)
        )

        table.add_column("Time", style="dim", width=16)
        table.add_column("Tool", style="cyan", width=12)
        table.add_column("Void", justify="right", width=8)
        table.add_column("LOC", justify="right", width=15)
        table.add_column("Attr", justify="center", width=4)  # Phase 5: Attribution method
        table.add_column("Files", style="yellow")

        # 添加最近的会话（倒序）
        for session in reversed(recent_sessions):
            timestamp = session.get("timestamp", "")
            # 格式化时间戳为本地时间
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    time_str = timestamp[:16]
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

            # 格式化文件列表显示
            if file_changes:
                # 优先Use详细的 file_changes（包含 LOC 信息）
                file_names = [fc.get("path", "") for fc in file_changes if fc.get("path")]
            elif changed_files:
                # 降级Use简单的 changed_files 列表
                file_names = changed_files
            else:
                file_names = []

            # 限制显示文件数量，避免表格过宽
            if len(file_names) == 0:
                files_str = f"[dim]{files_count} file(s)[/dim]"
            elif len(file_names) <= 2:
                # 1-2 个文件：直接显示完整路径（只显示文件名）
                short_names = [Path(f).name for f in file_names]
                files_str = ", ".join(short_names)
            else:
                # 3+ 个文件：显示前2个 + 数量
                short_names = [Path(f).name for f in file_names[:2]]
                remaining = len(file_names) - 2
                files_str = f"{', '.join(short_names)} +{remaining}"

            total_changed = loc_added + loc_deleted  # 总变更量（增删都是正向工作）
            loc_style = "green"  # 总是绿色
            loc_str = f"[{loc_style}]{total_changed}[/{loc_style}] (+{loc_added}/-{loc_deleted})"

            # Phase 5: Get归因方法图标
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

    def _create_roi_panel(self, summary: Dict) -> Panel:
        """Create ROI 分析面板"""
        roi = self._calculate_roi(summary)

        if summary['total_sessions'] == 0:
            content = Text("No data available for ROI calculation.", style="dim italic")
            return Panel(
                content,
                title="[yellow]💰 ROI Analysis[/yellow]",
                border_style="yellow"
            )

        # ROI Calculate详情
        total_void_min = summary['total_void_time_ms'] / 60000
        total_loc_changed = summary['total_loc_added'] + summary['total_loc_deleted']  # 总变更量
        net_loc = summary['total_loc_added'] - summary['total_loc_deleted']  # Net changes（仅用于显示）
        ai_output = total_loc_changed * self.HUMAN_CODING_CONSTANT  # AI 产出等价时间（Use总变更量）

        # Create分析表格
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Item", style="cyan", width=30)
        table.add_column("Value", style="bold")

        table.add_row("Total Void Time", f"{total_void_min:.2f} min")
        table.add_row("Total LOC Changed", f"{total_loc_changed:,} (+{summary['total_loc_added']:,} -{summary['total_loc_deleted']:,})")
        table.add_row("Human Coding Constant", f"{self.HUMAN_CODING_CONSTANT} min/LOC")
        table.add_row("AI Equivalent Output", f"{ai_output:.2f} min")

        table.add_row("", "")  # 空行

        # ROI Calculate公式
        formula_text = Text()
        formula_text.append("ROI = ", style="dim")
        formula_text.append(f"(AI Output - Void) / Void", style="yellow")
        table.add_row("Formula", formula_text)

        # Calculate结果
        roi_text = Text()
        roi_style = "green bold" if roi > 0 else "red bold"
        roi_text.append(f"{roi:.2f}%", style=roi_style)

        if roi > 0:
            roi_text.append(f"\n+{roi:.0f}% efficiency gain! 🚀", style="green dim")
        elif roi == 0:
            roi_text.append("\nBreak-even point", style="yellow dim")
        else:
            roi_text.append(f"\n{roi:.0f}% efficiency loss", style="red dim")

        table.add_row("Result", roi_text)

        # 解释
        table.add_row("", "")
        interpretation = Text()
        if roi > 100:
            interpretation.append("Excellent! AI saves significant time.", style="green")
        elif roi > 0:
            interpretation.append("Positive ROI. AI is helpful.", style="green")
        elif roi == 0:
            interpretation.append("Neutral. Consider optimization.", style="yellow")
        else:
            interpretation.append("Negative ROI. Review workflow.", style="red")

        table.add_row("Interpretation", interpretation)

        return Panel(
            table,
            title="[yellow]💰 ROI Analysis[/yellow]",
            border_style="yellow"
        )

    def _calculate_roi(self, summary: Dict) -> float:
        """
        Calculate ROI (Return on Investment)

        ROI = (AI Total Output × Human Coding Constant - Cumulative Wait Time) / Cumulative Wait Time × 100%

        注意：增加和Delete代码都是正向收益（重构、优化、清理也是有价值的工作）

        Args:
            summary: 统计摘要数据

        Returns:
            ROI 百分比
        """
        total_void_min = summary['total_void_time_ms'] / 60000
        total_loc_changed = summary['total_loc_added'] + summary['total_loc_deleted']  # 总变更量

        if total_void_min == 0:
            return 0.0

        # AI total output (converted to time) - both add and delete count
        ai_output_min = total_loc_changed * self.HUMAN_CODING_CONSTANT

        # ROI Calculate
        roi = ((ai_output_min - total_void_min) / total_void_min) * 100

        return roi

    def _create_file_details_panel(self, recent_sessions: List[Dict]) -> Panel:
        """Create文件详情面板 - 显示最近会话的File change details"""
        if not recent_sessions:
            content = Text("No file changes recorded.", style="dim italic")
            return Panel(
                content,
                title="[blue]📄 File Details (Latest Session)[/blue]",
                border_style="blue"
            )

        # Get最近的一个会话
        latest_session = recent_sessions[-1]
        file_changes = latest_session.get("file_changes", [])
        tool = latest_session.get("tool", "unknown")
        timestamp = latest_session.get("timestamp", "")

        # Get总的 LOC 统计（降级显示）
        loc_added = latest_session.get("loc_added", 0)
        loc_deleted = latest_session.get("loc_deleted", 0)
        changed_files = latest_session.get("changed_files", [])

        if not file_changes:
            # Check是否有总的 LOC 数据（降级显示）
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
                # 完全无数据
                content = Text("No file changes recorded.", style="dim italic")
                return Panel(
                    content,
                    title=f"[blue]📄 File Details ({tool})[/blue]",
                    border_style="blue"
                )

        # Create文件详情表格
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
        for fc in file_changes[:10]:  # 最多显示 10 个文件
            path = fc.get("path", "")
            loc_added = fc.get("loc_added", 0)
            loc_deleted = fc.get("loc_deleted", 0)
            total_changed = loc_added + loc_deleted

            # 只显示文件名（不显示完整路径）
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

        # 格式化标题时间
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M")
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
