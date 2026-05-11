#!/usr/bin/env python3
"""
VoidTally - Non-intrusive AI CLI performance observation tool
Statistics for time lost in AI waiting void
"""

import sys
import os
import argparse

def main():
    if len(sys.argv) < 2:
        print("Usage: voidtally <command> [args]", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  run <cli> [args]        - Run a CLI tool with VoidTally monitoring", file=sys.stderr)
        print("  board [--tool T] [--project P] - Display the efficiency dashboard", file=sys.stderr)
        print("  tools                   - List all tracked AI CLI tools", file=sys.stderr)
        print("  projects                - List all tracked projects", file=sys.stderr)
        print("  clear                   - Clear all tracking data (with backup)", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "run":
        if len(sys.argv) < 3:
            print("Usage: voidtally run <cli> [args]", file=sys.stderr)
            sys.exit(1)

        from void_observer import VoidObserver
        target_cli = sys.argv[2]
        target_args = sys.argv[3:]

        observer = VoidObserver(target_cli, target_args)
        sys.exit(observer.run())

    elif command == "board":
        # Parse board command arguments
        parser = argparse.ArgumentParser(
            prog="voidtally board",
            description="Display the VoidTally efficiency dashboard"
        )
        parser.add_argument(
            "--tool",
            type=str,
            help="Filter statistics by tool name (e.g., aider, claude-cli)"
        )
        parser.add_argument(
            "--project",
            type=str,
            help="Filter statistics by project path (e.g., /home/user/project1)"
        )

        # Parse only the board command args (skip 'voidtally board')
        board_args = parser.parse_args(sys.argv[2:])

        # Normalize project path to absolute path for consistent matching
        project_filter = board_args.project
        if project_filter:
            project_filter = os.path.abspath(project_filter)

        # Phase 6: Trigger manual save in running sessions
        from pathlib import Path
        import signal
        import time

        voidtally_dir = Path.home() / ".voidtally"
        if voidtally_dir.exists():
            # Find all PID files
            pid_files = list(voidtally_dir.glob("run_*.pid"))
            triggered = 0

            for pid_file in pid_files:
                try:
                    content = pid_file.read_text().strip().split('\n')
                    pid = int(content[0])

                    # Check if process is still running
                    try:
                        os.kill(pid, 0)  # Signal 0 just checks if process exists
                        # Process exists, send SIGUSR1 to trigger save
                        os.kill(pid, signal.SIGUSR1)
                        triggered += 1
                    except ProcessLookupError:
                        # Process no longer exists, clean up PID file
                        pid_file.unlink()
                except (ValueError, IndexError, FileNotFoundError):
                    pass

            if triggered > 0:
                print(f"💾 Triggered manual save in {triggered} running session(s)...", file=sys.stderr)
                time.sleep(3)  # Give processes time to save (file-diff + git can take 1-3s)
            else:
                if pid_files:
                    pass  # stale PID files were cleaned up
                # No running observer — board will show last persisted data
                print("ℹ️  No active voidtally sessions found; showing last saved data.", file=sys.stderr)

        from void_dashboard import VoidDashboard
        dashboard = VoidDashboard(tool_filter=board_args.tool, project_filter=project_filter)
        sys.exit(dashboard.run())

    elif command == "tools":
        # List all available tools
        from void_storage import DataStorage
        storage = DataStorage()
        tools = storage.get_available_tools()

        if not tools:
            print("No tools tracked yet.", file=sys.stderr)
            print("Run 'voidtally run <cli>' to start tracking.", file=sys.stderr)
            sys.exit(0)

        print("Tracked AI CLI Tools:")
        for tool in tools:
            print(f"  - {tool}")
        print(f"\nUse 'voidtally board --tool <name>' to filter by tool.")
        sys.exit(0)

    elif command == "projects":
        # List all available projects
        from void_storage import DataStorage
        storage = DataStorage()
        projects = storage.get_available_projects()

        if not projects:
            print("No projects tracked yet.", file=sys.stderr)
            print("Run 'voidtally run <cli>' to start tracking.", file=sys.stderr)
            sys.exit(0)

        print("Tracked Projects:")
        for project in projects:
            print(f"  - {project}")
        print(f"\nUse 'voidtally board --project <path>' to filter by project.")
        sys.exit(0)

    elif command == "clear":
        # Clear all tracking data
        from void_storage import DataStorage
        storage = DataStorage()

        # Check if data exists
        if not storage.data_file.exists():
            print("No data to clear.", file=sys.stderr)
            sys.exit(0)

        # Show current statistics
        summary = storage.get_statistics_summary()
        print(f"Current data:")
        print(f"  Sessions: {summary['total_sessions']}")
        print(f"  LOC Added: {summary['total_loc_added']}")
        print(f"  LOC Deleted: {summary['total_loc_deleted']}")
        print(f"  Data file: {storage.data_file}")
        print()

        # Confirm deletion
        try:
            response = input("Are you sure you want to clear ALL data? (y/N): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            sys.exit(0)

        if response != 'y' and response != 'yes':
            print("Cancelled.")
            sys.exit(0)

        # Clear data (with automatic backup)
        try:
            storage.clear_all_data(backup=True)
            print(f"✓ Data cleared successfully.")
            print(f"✓ Backup saved in {storage.data_dir}")
            sys.exit(0)
        except RuntimeError as e:
            print(f"✗ Failed to clear data: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
