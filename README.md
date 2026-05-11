# VoidTally

A non-intrusive performance observation tool for AI CLI developers. VoidTally quantifies "The Void" - the time wasted waiting between user input and AI response.

## Features

- 🎯 **Zero-Impact Monitoring**: PTY proxy with 100% ANSI passthrough
- ⏱️ **Precise Timing**: TTLT (Time to Last Token) — measures from Enter to last AI output character
- 📊 **Rich TUI Dashboard**: Statistics, 7-day trends, and file details
- 📸 **Snapshot Attribution**: Accurate LOC tracking even without Git
- 🔍 **Smart Filtering**: Filter by tool and project for targeted analysis
- 🔒 **Privacy First**: All data stored locally, no cloud uploads


## Quick Start

### Installation

```bash
# Clone and setup
git clone https://github.com/Fzzzhan/void-tally.git
cd void-tally

# Install dependencies (optional, for enhanced dashboard)
pip install rich>=13.0.0

# Make executable
chmod +x voidtally.py
```

**Requirements:**
- Python 3.7+ (standard library only for core features)
- `rich>=13.0.0` (optional, for colorful dashboard)

### Basic Usage

```bash
# Monitor AI CLI tool
python3 voidtally.py run aider
python3 voidtally.py run claude

# GitHub Copilot CLI (gh copilot)
python3 voidtally.py run gh copilot suggest
python3 voidtally.py run gh copilot explain

# View dashboard
python3 voidtally.py board

# Filter by tool
python3 voidtally.py board --tool aider
python3 voidtally.py board --tool gh-copilot   # GitHub Copilot sessions

# Filter by project
python3 voidtally.py board --project .
python3 voidtally.py board --project /path/to/project

# List tracked tools and projects
python3 voidtally.py tools
python3 voidtally.py projects

# Clear all data (with backup)
python3 voidtally.py clear
```

**Optional: Create symlink for easier access**
```bash
sudo ln -s $(pwd)/voidtally.py /usr/local/bin/voidtally
voidtally run aider
voidtally board
```

## Dashboard Features

The TUI dashboard displays:

- **📊 Overall Statistics**: Total sessions, void time, LOC changed, efficiency
- **📈 7-Day Void Time Trend**: ASCII bar chart showing daily wait time patterns
- **📅 Today's Activity**: Current day sessions, LOC, and attribution methods
- **📋 Recent Sessions**: Last 10 sessions with tool, void time, and file changes
- **📄 File Details**: Per-file LOC statistics from latest session

All panels support filtering by `--tool` and `--project` for targeted analysis.

## How It Works

VoidTally uses **PTY (pseudo-terminal) proxy technology** to transparently monitor AI CLI tools:

1. **PTY Proxy**: Creates pseudo-terminal to intercept stdin/stdout without modifying the target CLI
2. **Void Observer**: Measures **TTLT (Time to Last Token)** — from Enter key to the last AI output character per turn
3. **Snapshot System**: Takes before/after snapshots of source files to calculate exact LOC changes
4. **Attribution Methods**:
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
- ✅ **GitHub Copilot CLI** — `voidtally run gh copilot` *(automatically stored as `gh-copilot`)*
- ✅ **Codex CLI** — `voidtally run codex`
- ✅ **Any AI CLI** — VoidTally works with all terminal-based tools

> **Note on `gh copilot`**: Because `gh` is the GitHub CLI (not an AI tool by itself), VoidTally automatically maps `gh copilot …` to the tool name `gh-copilot` so it appears correctly on the dashboard. Use `voidtally board --tool gh-copilot` to filter specifically for Copilot sessions.

## Troubleshooting

**Dashboard colors not showing:**
```bash
pip install rich>=13.0.0
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
  "gen_duration_ms": 30000,
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
  "attribution_method": "snapshot"
}
```

## Filtering

VoidTally supports flexible filtering for targeted analysis:

```bash
# By tool
voidtally board --tool aider
voidtally board --tool claude
voidtally board --tool gh-copilot   # GitHub Copilot (gh copilot)

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

## Links

- 🐛 [Report Issues](https://github.com/Fzzzhan/void-tally/issues)
- 💡 [Feature Requests](https://github.com/Fzzzhan/void-tally/discussions)

---

**VoidTally** - Stop losing time in The Void. Start tracking your AI efficiency today! 🚀
