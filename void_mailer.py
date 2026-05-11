#!/usr/bin/env python3
"""
Email notification module for VoidTally
Sends daily void time reports via email
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path
import json


class MailerConfig:
    """Email configuration manager"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize mailer configuration

        Args:
            config_dir: Configuration directory, defaults to ~/.voidtally
        """
        if config_dir is None:
            self.config_dir = Path.home() / ".voidtally"
        else:
            self.config_dir = Path(config_dir)

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "mailer_config.json"

    def save_config(self, email: str, smtp_server: str, smtp_port: int,
                   smtp_username: str, smtp_password: str,
                   send_time: str = "20:00") -> None:
        """
        Save email configuration

        Args:
            email: Recipient email address
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP server port (e.g., 587 for TLS)
            smtp_username: SMTP authentication username
            smtp_password: SMTP authentication password
            send_time: Daily send time in HH:MM format (default: 20:00)
        """
        config = {
            "email": email,
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "smtp_username": smtp_username,
            "smtp_password": smtp_password,
            "send_time": send_time,
            "enabled": True
        }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    def load_config(self) -> Optional[Dict]:
        """
        Load email configuration

        Returns:
            Configuration dict or None if not configured
        """
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def is_configured(self) -> bool:
        """Check if email is configured"""
        config = self.load_config()
        return config is not None and config.get("enabled", False)

    def disable(self) -> None:
        """Disable email notifications"""
        config = self.load_config()
        if config:
            config["enabled"] = False
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

    def enable(self) -> None:
        """Enable email notifications"""
        config = self.load_config()
        if config:
            config["enabled"] = True
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)


class VoidMailer:
    """Email notification sender"""

    def __init__(self, config: Dict):
        """
        Initialize mailer with configuration

        Args:
            config: Email configuration dict
        """
        self.config = config

    def format_time(self, ms: int) -> str:
        """
        Format milliseconds to human-readable time

        Args:
            ms: Time in milliseconds

        Returns:
            Formatted time string (e.g., "1h 23m 45s")
        """
        seconds = ms / 1000
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def generate_report_html(self, daily_stats: Dict, sessions: List[Dict]) -> str:
        """
        Generate HTML email report

        Args:
            daily_stats: Daily aggregated statistics
            sessions: List of session details

        Returns:
            HTML content string
        """
        date = daily_stats.get("date", datetime.now().strftime("%Y-%m-%d"))
        total_void_ms = daily_stats.get("total_void_ms", 0)
        total_loc_added = daily_stats.get("total_loc_added", 0)
        total_loc_deleted = daily_stats.get("total_loc_deleted", 0)
        session_count = daily_stats.get("sessions", 0)

        void_time_str = self.format_time(total_void_ms)
        loc_net = total_loc_added - total_loc_deleted

        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header .date {{
                    margin-top: 10px;
                    font-size: 16px;
                    opacity: 0.9;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .stat-card .label {{
                    font-size: 12px;
                    text-transform: uppercase;
                    color: #666;
                    margin-bottom: 5px;
                }}
                .stat-card .value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #667eea;
                }}
                .sessions {{
                    margin-top: 30px;
                }}
                .session {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .session-tool {{
                    font-weight: bold;
                    color: #764ba2;
                    margin-bottom: 5px;
                }}
                .session-details {{
                    font-size: 14px;
                    color: #666;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #999;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 VoidTally Daily Report</h1>
                <div class="date">{date}</div>
            </div>
            <div class="content">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="label">Void Time</div>
                        <div class="value">{void_time_str}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Sessions</div>
                        <div class="value">{session_count}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">LOC Added</div>
                        <div class="value">+{total_loc_added}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">LOC Deleted</div>
                        <div class="value">-{total_loc_deleted}</div>
                    </div>
                </div>

                <div style="background: white; padding: 15px; border-radius: 8px; margin-top: 15px;">
                    <div style="font-weight: bold; margin-bottom: 5px;">Net LOC Change</div>
                    <div style="font-size: 20px; color: {'#22c55e' if loc_net > 0 else '#ef4444'};">
                        {'+' if loc_net > 0 else ''}{loc_net} lines
                    </div>
                </div>
        """

        if sessions:
            html += """
                <div class="sessions">
                    <h3 style="color: #333; margin-bottom: 15px;">Session Details</h3>
            """
            for session in sessions:
                tool = session.get("tool", "unknown")
                void_ms = session.get("void_duration_ms", 0)
                loc_add = session.get("loc_added", 0)
                loc_del = session.get("loc_deleted", 0)
                timestamp = session.get("timestamp", "")
                time_str = timestamp[11:19] if len(timestamp) > 19 else "unknown"

                html += f"""
                    <div class="session">
                        <div class="session-tool">{tool}</div>
                        <div class="session-details">
                            ⏱️ {self.format_time(void_ms)} void time |
                            📝 +{loc_add}/-{loc_del} LOC |
                            🕐 {time_str}
                        </div>
                    </div>
                """
            html += """
                </div>
            """

        html += """
                <div class="footer">
                    Generated by <a href="https://github.com/yourusername/void_tally" style="color: #667eea;">VoidTally</a>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def send_daily_report(self, daily_stats: Dict, sessions: List[Dict]) -> bool:
        """
        Send daily report email

        Args:
            daily_stats: Daily aggregated statistics
            sessions: List of session details

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"VoidTally Daily Report - {daily_stats.get('date', 'Today')}"
            msg['From'] = self.config['smtp_username']
            msg['To'] = self.config['email']

            # Generate HTML content
            html_content = self.generate_report_html(daily_stats, sessions)

            # Attach HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['smtp_username'], self.config['smtp_password'])
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Failed to send email: {e}")
            return False


def send_daily_report_now():
    """
    Send daily report immediately (used for testing or manual triggers)
    """
    from void_storage import DataStorage

    # Load configuration
    config_mgr = MailerConfig()
    config = config_mgr.load_config()

    if not config or not config.get("enabled", False):
        print("Email notifications not configured or disabled.")
        print("Run 'voidtally config email' to set up email notifications.")
        return False

    # Get today's statistics
    storage = DataStorage()
    today = datetime.now(timezone.utc)
    date_str = today.strftime("%Y-%m-%d")

    # Get daily stats
    daily_stats_list = storage.get_daily_stats(days=1)
    if not daily_stats_list:
        print(f"No statistics available for {date_str}")
        return False

    daily_stats = daily_stats_list[0]

    # Get today's sessions
    sessions = storage.load_sessions_by_date(today)

    # Send email
    mailer = VoidMailer(config)
    success = mailer.send_daily_report(daily_stats, sessions)

    if success:
        print(f"✓ Daily report sent to {config['email']}")
        return True
    else:
        print("✗ Failed to send daily report")
        return False


if __name__ == "__main__":
    # Test: send today's report
    send_daily_report_now()
