# Email Notification Feature

VoidTally can now send daily email reports about your void time statistics.

## Features

- 📧 Daily email reports with void time statistics
- 📊 HTML formatted emails with session details
- ⏰ Configurable send time
- 🔄 Cross-platform scheduling support (Linux/macOS/Windows)

## Setup Instructions

### Step 1: Configure Email Settings

Run the interactive configuration command:

```bash
voidtally config email
```

You'll be prompted to enter:
- **Recipient email address**: Where to send the reports
- **SMTP server**: Your email provider's SMTP server
  - Gmail: `smtp.gmail.com`
  - Outlook: `smtp-mail.outlook.com`
  - Yahoo: `smtp.mail.yahoo.com`
- **SMTP port**: Usually 587 for TLS
- **SMTP username**: Your email address
- **SMTP password**: Your email password or app-specific password
- **Send time**: When to send daily reports (format: HH:MM, default: 20:00)

#### Gmail Setup Example

For Gmail, you'll need to use an **App Password** instead of your regular password:

1. Go to your Google Account settings
2. Security → 2-Step Verification (enable if not already)
3. Security → App passwords
4. Generate a new app password for "Mail"
5. Use this 16-character password when configuring VoidTally

Configuration example:
```
Recipient email address: user@example.com
SMTP server: smtp.gmail.com
SMTP port: 587
SMTP username: sender@gmail.com
SMTP password: [16-character app password]
Daily send time: 20:00
```

### Step 2: Test the Configuration

Send a test report immediately:

```bash
voidtally send-report
```

This will send today's void time report to the configured email address.

### Step 3: Set Up Automatic Scheduling

Enable automatic daily email reports:

```bash
voidtally schedule
```

This command will:
- **Linux/macOS**: Show instructions to add a cron job
- **Windows**: Show instructions to create a Task Scheduler task

#### Linux/macOS Scheduling

The command will output a cron line like:
```
0 20 * * * voidtally send-report
```

To enable it:
1. Run `crontab -e`
2. Add the provided line
3. Save and exit

#### Windows Scheduling

The command will provide a PowerShell script. Run it as Administrator to create the scheduled task.

## Email Report Contents

Each daily report includes:

- **Void Time**: Total waiting time for the day
- **Sessions**: Number of AI CLI sessions
- **LOC Added**: Total lines of code added
- **LOC Deleted**: Total lines of code deleted
- **Net LOC Change**: Net code change (+/-)
- **Session Details**: Individual session information with timestamps

## Commands Reference

| Command | Description |
|---------|-------------|
| `voidtally config email` | Configure email notifications |
| `voidtally send-report` | Send daily report immediately |
| `voidtally schedule` | Set up automatic daily reports |

## Configuration Files

Email configuration is stored in:
```
~/.voidtally/mailer_config.json
```

To disable email notifications, edit this file and set `"enabled": false`.

## Troubleshooting

### Email not sending

1. **Check SMTP credentials**: Ensure your username and password are correct
2. **App passwords**: For Gmail/Outlook, use app-specific passwords
3. **Firewall**: Ensure port 587 is not blocked
4. **Test manually**: Run `voidtally send-report` to see error messages

### No data in report

- Make sure you have tracked some sessions with `voidtally run <cli>`
- Run `voidtally board` to verify data exists

### Scheduling not working

- **Linux/macOS**: Check cron is running: `systemctl status cron`
- **Windows**: Check Task Scheduler logs
- Verify the voidtally command is in your PATH

## Security Notes

- Email passwords are stored in plain text in `~/.voidtally/mailer_config.json`
- Keep this file secure (default permissions: user-only read/write)
- Use app-specific passwords instead of main account passwords
- Consider using environment variables for sensitive data in production

## Example Email

The daily report email looks like:

```
📊 VoidTally Daily Report
2026-05-11

╔══════════════════════════════════════╗
║ Void Time        │ 23m 45s          ║
║ Sessions         │ 5                ║
║ LOC Added        │ +234             ║
║ LOC Deleted      │ -87              ║
╚══════════════════════════════════════╝

Net LOC Change: +147 lines

Session Details:
┌────────────────────────────────────────
│ aider
│ ⏱️ 8m 32s void time | 📝 +120/-45 LOC | 🕐 14:23:10
├────────────────────────────────────────
│ claude-cli
│ ⏱️ 5m 18s void time | 📝 +67/-23 LOC | 🕐 16:45:22
└────────────────────────────────────────
```

(Actual email is HTML formatted with colors and styling)
