# VoidTally

A non-intrusive performance observation tool for AI CLI developers. VoidTally quantifies "The Void" - the time wasted waiting between user input and AI response - to calculate the real ROI of AI-assisted development.

## Features

- 🎯 **Zero-Impact Monitoring**: PTY proxy with 100% ANSI passthrough
- ⏱️ **Precise Timing**: Sub-millisecond accuracy for void time measurement
- 📊 **Rich TUI Dashboard**: Beautiful visualization with statistics and ROI analysis
- 🔍 **Git Integration**: Automatic LOC tracking and code change attribution
- 🔒 **Privacy First**: All data stored locally, no cloud uploads
- 🎨 **Smart Fallback**: Works with or without rich library

## VoidTally vs WakaTime

**VoidTally** and **WakaTime** are **complementary tools**, not competitors:

- **VoidTally**: Specialized for AI CLI tools - measures "The Void" (AI wait time) and calculates ROI
- **WakaTime**: General time tracking - measures overall coding activity across editors/projects

**Key Insight**: VoidTally fills a unique gap that general time trackers like WakaTime cannot address - quantifying AI assistance efficiency.

👉 **For a detailed comparison**, see [COMPARISON.md](./COMPARISON.md)

**When to use both**:
- Use **VoidTally** to measure AI CLI efficiency (Aider, Claude-cli)
- Use **WakaTime** to track overall coding time and project allocation
- Together, they provide a complete picture of AI-assisted development productivity

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/void_tally.git
cd void_tally

# Install dependencies (optional, for enhanced dashboard)
pip install -r requirements.txt

# Make it executable
chmod +x voidtally.py
```

**Dependencies:**
- Python 3.7+ (standard library only for core features)
- `rich>=13.0.0` (optional, for enhanced TUI dashboard)

### Basic Usage

**Method 1: Direct execution (recommended for testing)**

```bash
python3 voidtally.py run <command> [args]
python3 voidtally.py board
```

**Method 2: Create symlink (recommended for daily use)**

```bash
# Linux/macOS
sudo ln -s $(pwd)/voidtally.py /usr/local/bin/voidtally
voidtally run <command> [args]
voidtally board
```

**Method 3: Install as package**

```bash
pip install -e .
voidtally run <command> [args]
voidtally board
```

## Usage Examples

### 1. Monitor AI CLI Tools

```bash
# With Aider
python3 voidtally.py run aider

# With any Python script
python3 voidtally.py run python3 my_script.py

# With interactive Python
python3 voidtally.py run python3

# With any command
python3 voidtally.py run echo "Hello World"
```

### 2. View Dashboard

```bash
# Show statistics dashboard
python3 voidtally.py board
```

The dashboard displays:
- **Total Void Time**: Cumulative waiting time
- **Net LOC**: Code lines added/deleted/net change
- **Efficiency**: LOC per minute of void time
- **Today's Activity**: Current day statistics
- **Recent Sessions**: Last 10 sessions with details
- **ROI Analysis**: Investment return calculation with interpretation

### 3. Additional Commands

```bash
# List all tracked tools
python3 voidtally.py tools

# List all tracked projects
python3 voidtally.py projects

# Filter dashboard by tool
python3 voidtally.py board --tool aider
python3 voidtally.py board --tool copilot

# Filter dashboard by project
python3 voidtally.py board --project /home/user/my-project
python3 voidtally.py board --project $(pwd)

# Combine filters (tool + project)
python3 voidtally.py board --tool aider --project /home/user/my-project

# Clear all data (with automatic backup)
python3 voidtally.py clear
```

**Filtering Options**:
- `--tool <name>`: Show statistics for specific AI tool (e.g., aider, copilot)
- `--project <path>`: Show statistics for specific project directory
- Both filters can be combined to narrow down results

**Note**: The `clear` command:
- Shows current statistics before deletion
- Requires confirmation (type 'y' to proceed)
- Automatically creates a backup in `~/.voidtally/data.jsonl.backup_YYYYMMDD_HHMMSS`
- Can be safely reverted by restoring the backup file

### 4. Testing VoidTally

Create a test script to simulate AI behavior:

```bash
# Create test script
cat > test_sim.py << 'EOF'
#!/usr/bin/env python3
import time
import sys

# Simulate void time (AI thinking)
time.sleep(0.5)

# Simulate AI output
print("Generating code...")
time.sleep(0.2)

# Create a file (simulating code generation)
with open("generated.py", "w") as f:
    f.write("def hello():\n")
    f.write("    print('Hello from AI')\n")

print("✓ Generated: generated.py")
EOF

# Run with VoidTally
python3 voidtally.py run python3 test_sim.py

# View results
python3 voidtally.py board
```

### 5. Real-World AI CLI Integration

Install and use with actual AI tools:

```bash
python3 voidtally.py run aider

# GitHub Copilot CLI (requires subscription)
python3 voidtally.py run copilot

# Claude CLI
python3 voidtally.py run claude 

# Or any other AI CLI tool
python3 voidtally.py run your-ai-tool
```

**Supported AI CLI Tools:**
- ✅ **Aider** - AI pair programming in terminal
- ✅ **GitHub Copilot CLI** (`copilot`) - GitHub's AI assistant
- ✅ **Claude CLI** - Anthropic's Claude in terminal
- ✅ **Pi CLI** - Inflection AI's assistant
- ✅ **Any AI CLI** - VoidTally works with all terminal-based AI tools

## How It Works

VoidTally uses PTY (pseudo-terminal) proxy technology to transparently monitor AI CLI tools without modifying them:

1. **The Void Observer**: Measures time from Enter key to first AI token (TTFT - Time To First Token)
2. **Latency Tracking**: Records generation duration from first token to completion
3. **Value Mapping**: Tracks code changes via git integration (Phase 3)
4. **ROI Calculation**: Quantifies productivity gain vs. time spent waiting

## Architecture

- **PTY Proxy**: Zero-impact forwarding with full ANSI support
- **State Machine**: Precise timing with <200ms error tolerance
- **Local Storage**: All data saved to `~/.voidtally/data.jsonl`
- **Privacy First**: No cloud uploads, 100% local processing

## Troubleshooting

### Command Not Found

If you see an error like:

```
❌ Error: Command 'your-command' not found in PATH
```

**Solutions:**

1. **Verify the command exists:**
   ```bash
   which your-command
   ```

2. **Install the command:**
   ```bash
   # For Aider
   pip install aider-chat

   # For other tools, follow their installation instructions
   ```

3. **Test with available commands:**
   ```bash
   python3 voidtally.py run echo "test"
   python3 voidtally.py run date
   python3 voidtally.py run python3 --version
   ```

### Dashboard Not Showing Colors

If the dashboard displays in plain text without colors:

```bash
# Install rich library for enhanced TUI
pip install rich>=13.0.0
```

The dashboard will automatically use the enhanced mode when rich is available, or fall back to plain text mode otherwise.

### No Git Statistics

If you see `loc_added: 0` and `loc_deleted: 0`:

1. **Make sure you're in a git repository:**
   ```bash
   git status
   ```

2. **Ensure files are tracked:**
   ```bash
   git add <files>
   ```

3. **Check that files were actually modified:**
   The tool only tracks changes between git HEAD and working directory.


## Data Format

All data is stored locally in `~/.voidtally/data.jsonl` (JSONL format):

```json
{
  "timestamp": "2026-05-09T11:45:00Z",
  "tool": "aider",
  "void_duration_ms": 1250,
  "gen_duration_ms": 30000,
  "loc_added": 45,
  "loc_deleted": 12,
  "project_path": "/home/user/project",
  "void_count": 3,
  "avg_void_ms": 416.67,
  "min_void_ms": 200.0,
  "max_void_ms": 800.0,
  "changed_files": ["src/main.py", "src/utils.py"],
  "files_changed_count": 2,
  "file_changes": [
    {
      "path": "src/main.py",
      "loc_added": 30,
      "loc_deleted": 8,
      "loc_net": 22
    },
    {
      "path": "src/utils.py",
      "loc_added": 15,
      "loc_deleted": 4,
      "loc_net": 11
    }
  ]
}
```

### Field Descriptions

- `timestamp`: ISO 8601 UTC timestamp
- `tool`: Command name being monitored
- `void_duration_ms`: Total time waiting for AI (milliseconds)
- `gen_duration_ms`: Total generation time after first token
- `loc_added`: Total lines of code added
- `loc_deleted`: Total lines of code deleted
- `project_path`: Working directory path
- `void_count`: Number of void periods in session
- `changed_files`: List of files modified during session
- `file_changes`: Detailed per-file LOC statistics

## ROI Calculation

VoidTally calculates ROI (Return on Investment) based on total code changes:

```
ROI = (AI Total Output × Human Coding Constant - Cumulative Wait Time) / Cumulative Wait Time × 100%
```

Where:
- **AI Total Output**: `loc_added + loc_deleted` (both adding and deleting code are valuable work)
- **Human Coding Constant**: 1.0 min/LOC (conservative estimate)
- **Cumulative Wait Time**: Total void time in minutes

**Why add deleted lines?** Deleting code is positive work - refactoring, optimization, and cleanup are essential development activities.

**Example:**
- AI changes 100 LOC (+60 added, -40 deleted) in 1 minute of void time
- AI equivalent output = 100 minutes (human would take 100 minutes for these changes)
- ROI = (100 - 1) / 1 × 100% = **9900%**

This means the AI saved you **99 times** the time you spent waiting!

## Project Structure

```
void_tally/
├── voidtally.py          # Main CLI entry point
├── void_observer.py      # PTY proxy core (Phase 1)
├── void_tracker.py       # Latency tracking state machine (Phase 1)
├── void_storage.py       # Data persistence (Phase 1)
├── void_watcher.py       # File system monitoring (Phase 2)
├── void_git.py           # Git diff integration (Phase 3)
├── void_dashboard.py     # Rich TUI dashboard (Phase 4)
├── test_phase1.py        # Phase 1 acceptance tests
├── test_phase2.py        # Phase 2 acceptance tests
├── test_phase3.py        # Phase 3 acceptance tests
├── test_phase4.py        # Phase 4 acceptance tests
├── requirements.txt      # Dependencies
├── setup.py              # Package setup
├── CLAUDE.md             # Development guidelines
├── prd.md                # Product requirements
└── PHASE*_REPORT.md      # Phase completion reports
```

## Advanced Usage

### Custom Ignore Patterns

Edit the ignore patterns in `void_watcher.py` to customize which files to track:

```python
self.ignore_patterns = [
    '.git', '__pycache__', 'node_modules',
    '.venv', 'venv', '.pytest_cache',
    '.mypy_cache', '.tox', 'dist', 'build',
    '.eggs', '*.egg-info'
]
```

### Analyzing Historical Data

```bash
# View all sessions
cat ~/.voidtally/data.jsonl | jq '.'

# Find high-ROI sessions
cat ~/.voidtally/data.jsonl | jq 'select(.loc_added > 50)'

# Calculate total time saved
cat ~/.voidtally/data.jsonl | jq -s 'map(.void_duration_ms) | add'
```

### Integration with CI/CD

```bash
# Run tests with VoidTally monitoring
python3 voidtally.py run pytest tests/

# Monitor build scripts
python3 voidtally.py run npm run build
```

## Performance

- **Timing Precision**: < 1ms error (far exceeding 200ms requirement)
- **Memory Overhead**: Minimal (state machine only)
- **CPU Overhead**: Negligible (passive monitoring)
- **Storage**: ~500 bytes per session (JSONL format)


## Contributing

Contributions are welcome! Please:

1. Read `CLAUDE.md` for development guidelines
2. Run all test suites before submitting
3. Follow the existing code style
4. Add tests for new features

## Acknowledgments

- Inspired by the need to quantify AI-assisted development efficiency
- Built with zero external dependencies for core features (Phase 1-3)
- Enhanced with `rich` library for beautiful TUI (Phase 4)

## License

MIT

## Support

- 🐛 Issues: Report bugs via GitHub Issues
- 💡 Feature Requests: Open a discussion on GitHub

---

**VoidTally** - Stop losing time in The Void. Start measuring your AI ROI today! 🚀
