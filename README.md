<p align="center">
  <img src="assets/logo.png" alt="VoidTally logo" width="220">
</p>

# VoidTally

A non-intrusive performance observation tool for AI CLI developers. VoidTally quantifies "The Void" - the time wasted waiting between user input and AI response.

## Features

- 🎯 **Zero-Impact Monitoring**: PTY proxy with 100% ANSI passthrough
- ⏱️ **Precise Timing**: Measures TTLT (Time to Last Token) — from Enter (submit) to the last AI output character
- 📊 **Rich TUI Dashboard**: Statistics, 7-day trends, and file details
- 📧 **Email Reports**: Automated daily void time reports with HTML formatting
- 📸 **Snapshot Attribution**: Accurate LOC tracking even without Git
- 🔍 **Smart Filtering**: Filter by tool and project for targeted analysis
- 🔒 **Privacy First**: All data stored locally, no cloud uploads


## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Fzzzhan/void-tally.git
cd void-tally

# Install with pip (editable mode for development)
pip install -e .

# Or install from PyPI
pip install voidtally
```

**Requirements:**
- Python 3.7+
- `rich>=10.0.0` (auto-installed)

### Basic Usage

```bash
# Monitor AI CLI tool
voidtally run aider
voidtally run claude

# GitHub Copilot CLI (standalone snap binary)
voidtally run copilot

# GitHub Copilot via gh extension (if using gh copilot)
voidtally run gh copilot suggest
voidtally run gh copilot explain

# View dashboard
voidtally board

# Filter by tool
voidtally board --tool aider
voidtally board --tool copilot      # GitHub Copilot (snap binary)
voidtally board --tool gh-copilot   # GitHub Copilot (gh extension)

# Filter by project
voidtally board --project .
voidtally board --project /path/to/project

# List tracked tools and projects
voidtally tools
voidtally projects

# Clear all data (with backup)
voidtally clear

# Email notifications
voidtally config email    # Configure email settings
voidtally send-report     # Send daily report now
voidtally schedule        # Set up automatic daily reports
```

## Dashboard Features

The TUI dashboard displays:

- **📊 Overall Statistics**: Total sessions, void time, LOC changed, efficiency
- **📈 7-Day Void Time Trend**: ASCII bar chart showing daily wait time patterns
- **📅 Today's Activity**: Current day sessions, LOC, and attribution methods
- **📋 Recent Sessions**: Last 10 sessions with tool, void time, and file changes
- **📄 File Details**: Per-file LOC statistics from latest session

All panels support filtering by `--tool` and `--project` for targeted analysis.

## Email Notifications

VoidTally can send automated daily email reports with your void time statistics.

### Setup

**1. Configure Email Settings**

```bash
voidtally config email
```

You'll be prompted to enter:
- Recipient email address
- SMTP server (e.g., `smtp.gmail.com` for Gmail)
- SMTP port (default: 587)
- SMTP username and password
- Daily send time (default: 20:00)

**Note for Gmail users**: Use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

**2. Test the Configuration**

```bash
voidtally send-report
```

This sends today's report immediately to verify your settings.

**3. Enable Automatic Daily Reports**

```bash
voidtally schedule
```

This will:
- **Linux/macOS**: Show instructions to add a cron job
- **Windows**: Show instructions to create a Task Scheduler task

### Email Report Contents

Each daily report includes:
- ⏱️ Total void time (formatted as hours/minutes/seconds)
- 📊 Number of sessions
- 📝 LOC added/deleted/net change
- 📋 Individual session details with timestamps

Reports are sent as HTML emails with color-coded statistics and session breakdowns.

For detailed setup instructions, see [EMAIL_NOTIFICATION.md](EMAIL_NOTIFICATION.md).

## How It Works

VoidTally uses **PTY (pseudo-terminal) proxy technology** to transparently monitor AI CLI tools:

1. **PTY Proxy**: Creates pseudo-terminal to intercept stdin/stdout without modifying the target CLI
2. **Void Observer**: Measures void time as TTLT — from Enter (submit request) to the last AI output character. The measurement is finalized when the user starts typing again, or automatically after the AI goes idle.
3. **Auto-finalize**: If AI output stops for 5 seconds with no further tokens, void time is recorded and the state resets. If no AI token arrives within 5 minutes of pressing Enter (e.g. session left open overnight), the interaction is discarded to prevent inflated measurements.
4. **Snapshot System**: Takes before/after snapshots of source files to calculate exact LOC changes
5. **Attribution Methods**:
   - **📸 Snapshot** (accurate): Uses file snapshots - works without Git
   - **🔀 Git** (fallback): Uses `git diff` when available
   - **❓ Unknown**: Legacy data without attribution

## Architecture

- **PTY Proxy**: Zero-impact I/O forwarding with full ANSI support
- **State Machine**: Precise timing with <1ms error
- **Snapshot Manager**: File-based diff calculation without Git dependency
- **Local Storage**: JSONL format (~500 bytes per session)
- **Privacy First**: No cloud uploads, 100% local processing

## Supported AI CLI Tools

- ✅ **Aider** — `voidtally run aider`
- ✅ **Claude CLI** — `voidtally run claude`
- ✅ **GitHub Copilot CLI** — `voidtally run copilot` *(snap binary, stored as `copilot`)* or `voidtally run gh copilot suggest` / `voidtally run gh copilot explain` *(gh extension, stored as `gh-copilot`)*
- ✅ **Codex CLI** — `voidtally run codex`
- ✅ **Any AI CLI** — VoidTally works with all terminal-based tools

> **Note on GitHub Copilot**: The standalone snap binary (`copilot`) is stored directly as `copilot`. If you use the `gh` extension instead (`gh copilot …`), VoidTally automatically maps it to `gh-copilot` so it isn't filtered out as a generic `gh` command. Use `voidtally board --tool copilot` or `--tool gh-copilot` depending on how you invoke it.

## Troubleshooting

**Dashboard colors not showing:**
```bash
pip install rich>=10.0.0
```

**No LOC statistics:**
- Files are tracked automatically via snapshot system
- Works in both Git and non-Git directories
- Check that files were actually modified during session


## Data Format

All sessions stored in `~/.voidtally/data.jsonl`:

```json
{
  "timestamp": "2026-05-10T14:30:00Z",
  "tool": "aider",
  "void_duration_ms": 1250,
  "loc_added": 45,
  "loc_deleted": 12,
  "project_path": "/home/user/project",
  "void_count": 3,
  "changed_files": ["src/main.py"],
  "file_changes": [
    {
      "path": "src/main.py",
      "loc_added": 30,
      "loc_deleted": 8,
      "loc_net": 22
    }
  ],
  "attribution_method": "snapshot",
  "session_id": "aider_2026-05-10T14:30:00"
}
```

## Filtering

VoidTally supports flexible filtering for targeted analysis:

```bash
# By tool
voidtally board --tool aider
voidtally board --tool claude
voidtally board --tool copilot      # GitHub Copilot (snap binary)
voidtally board --tool gh-copilot   # GitHub Copilot (gh extension)

# By project (all formats work)
voidtally board --project .
voidtally board --project ./
voidtally board --project /absolute/path

# Combined
voidtally board --tool aider --project .
```

**Path normalization**: VoidTally automatically converts relative paths (`.`, `./`) to absolute paths for consistent matching.

**Tool name mapping**: Some CLI tools use a wrapper command. VoidTally maps these automatically so they appear as meaningful AI tool names on the dashboard:

| Command | Stored as |
|---------|-----------|
| `copilot …` | `copilot` |
| `gh copilot …` | `gh-copilot` |
| `aider …` | `aider` |
| `claude …` | `claude` |

## Performance

- **Timing Precision**: < 1ms error
- **Memory Overhead**: Minimal (state machine + snapshots)
- **CPU Overhead**: Negligible (passive monitoring)
- **Storage**: ~500 bytes per session

## License

MIT

## Citation

If you use VoidTally in your project, please cite:

```
Fengze Han. (2025). VoidTally: Void Time Tracker for AI CLI Tools.
https://github.com/Fzzzhan/void-tally
```

## Links

- 🐛 [Report Issues](https://github.com/Fzzzhan/void-tally/issues)
- 💡 [Feature Requests](https://github.com/Fzzzhan/void-tally/discussions)

---
