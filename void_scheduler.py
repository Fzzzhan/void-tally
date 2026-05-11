#!/usr/bin/env python3
"""
Scheduler module for VoidTally
Manages daily email report scheduling
"""

import os
import sys
from pathlib import Path
from datetime import datetime


class VoidScheduler:
    """Manages scheduled tasks for VoidTally"""

    @staticmethod
    def setup_cron_linux():
        """
        Setup cron job for Linux/macOS

        Returns:
            True if successfully set up, False otherwise
        """
        from void_mailer import MailerConfig

        # Load configuration to get send time
        config_mgr = MailerConfig()
        config = config_mgr.load_config()

        if not config:
            print("Email configuration not found. Please run 'voidtally config email' first.")
            return False

        send_time = config.get("send_time", "20:00")
        hour, minute = send_time.split(":")

        # Find voidtally executable path
        voidtally_path = None

        # Method 1: Check if voidtally is in PATH
        import shutil
        voidtally_path = shutil.which("voidtally")

        if not voidtally_path:
            # Method 2: Use python module execution
            python_path = sys.executable
            voidtally_path = f"{python_path} -m voidtally"

        # Create cron command
        cron_command = f"{minute} {hour} * * * {voidtally_path} send-report"

        print("\nTo enable daily email reports, add this line to your crontab:")
        print("-" * 60)
        print(cron_command)
        print("-" * 60)
        print("\nRun: crontab -e")
        print("Add the line above, save and exit.")
        print(f"\nReports will be sent daily at {send_time}")

        return True

    @staticmethod
    def setup_task_scheduler_windows():
        """
        Setup Windows Task Scheduler

        Returns:
            True if successfully set up, False otherwise
        """
        from void_mailer import MailerConfig

        # Load configuration to get send time
        config_mgr = MailerConfig()
        config = config_mgr.load_config()

        if not config:
            print("Email configuration not found. Please run 'voidtally config email' first.")
            return False

        send_time = config.get("send_time", "20:00")

        # Find voidtally executable path
        import shutil
        voidtally_path = shutil.which("voidtally")

        if not voidtally_path:
            python_path = sys.executable
            voidtally_path = python_path

        task_name = "VoidTallyDailyReport"

        # Create PowerShell command for Task Scheduler
        ps_command = f'''
$action = New-ScheduledTaskAction -Execute '{voidtally_path}' -Argument 'send-report'
$trigger = New-ScheduledTaskTrigger -Daily -At {send_time}
Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Description "VoidTally daily email report"
'''

        print("\nTo enable daily email reports on Windows:")
        print("-" * 60)
        print("Run the following PowerShell command as Administrator:")
        print(ps_command)
        print("-" * 60)
        print(f"\nReports will be sent daily at {send_time}")
        print("\nOr manually create a task in Task Scheduler:")
        print(f"  Program: {voidtally_path}")
        print(f"  Arguments: send-report")
        print(f"  Trigger: Daily at {send_time}")

        return True

    @staticmethod
    def setup_scheduler():
        """
        Setup scheduler based on platform

        Returns:
            True if successfully set up, False otherwise
        """
        platform = sys.platform

        if platform.startswith('linux') or platform == 'darwin':
            return VoidScheduler.setup_cron_linux()
        elif platform == 'win32':
            return VoidScheduler.setup_task_scheduler_windows()
        else:
            print(f"Platform {platform} not supported for automatic scheduling.")
            print("Please manually schedule: voidtally send-report")
            return False


if __name__ == "__main__":
    VoidScheduler.setup_scheduler()
