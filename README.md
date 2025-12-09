# tw-cli

Enhanced Taskwarrior CLI with beautiful views - kanban boards, tables, and more.

## Features

- **Kanban Board** - Visual task organization with status columns
- **Table View** - Sortable columns with rich formatting
- **List View** - Compact task listing with icons
- **Markdown Export** - GitHub-flavored markdown tables
- **Interactive Shell** - Like DuckDB CLI for tasks

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## Quick Start

### View Tasks as Kanban Board

```bash
tw-cli view kanban
```

### View Tasks as Table

```bash
tw-cli view table
```

### Interactive Shell

```bash
tw-cli shell
```

Shell commands:
- `.mode <view>` - Switch between kanban, table, list, markdown
- `.mode kanban:priority` - Group kanban by priority, project, or tag
- `.help` - Show help
- `.exit` - Exit

### Run Taskwarrior Filters

```bash
tw-cli view kanban --cmd "task +work"
tw-cli view table --cmd "task project:home status:pending"
```

## View Modes

### Kanban Board
- **Backlog** - Pending tasks (not started)
- **In Progress** - Tasks with `start` timestamp (`task <id> start`)
- **Waiting** - Tasks with `status:waiting`
- **Completed** - Recently completed (last 7 days)
- **Blocked** - Tasks with blocking dependencies

Alternative groupings: priority, project, tag

### Table View
- Sortable columns with rich formatting
- Color-coded by priority and urgency
- Overdue indicators

### List View
- Compact with icons and colors
- Inline metadata

### Markdown Export
- GitHub-flavored markdown tables
- Detailed task lists grouped by project

## Configuration

**Config file location:**
- Linux/macOS: `~/.config/tw-cli/config.toml`
- WSL: `~/.config/tw-cli/config.toml` (same as Linux)
- Windows: `%USERPROFILE%\\.config\\tw-cli\\config.toml`

**Note:** tw-cli respects your Taskwarrior configuration in `~/.taskrc`, including context settings. If you have a context defined (e.g., `task context work`), tw-cli will honor it.

### Black & White Mode

To remove all colors, set in `~/.config/tw-cli/config.toml`:

```toml
[colors]
enabled = false  # Disables ALL colors for clean terminal output
```

Or customize with neutral colors - see `example-config.toml` for full black & white preset.

## Backend Support

tw-cli uses a **pluggable backend architecture** to work with different CLI tools beyond Taskwarrior.

### Supported Backends

| Backend | Status | Command | Description |
|---------|--------|---------|-------------|
| **Taskwarrior** | ✅ Full Support | `task` | Default backend, all features work |
| **Jira-CLI** | ✅ Ready | `jira` | Full integration with field mapping |
| **Custom** | ⚙️ Configurable | Any | Define your own JSON-based CLI tool |

### Configuration

#### TaskWarrior (Default)

```toml
[backend]
type = "taskwarrior"
command = "task"
```

#### Jira-CLI Integration

```toml
[backend]
type = "jira"
command = "jira"
export_format = "json"

# Optional: Custom field mapping (defaults provided)
[backend.field_mapping]
id = "key"                      # Jira issue key (e.g., PROJ-123)
uuid = "id"                     # Jira issue ID
description = "fields.summary"  # Issue summary
status = "fields.status.name"   # Status (maps to pending/completed/waiting)
project = "fields.project.key"  # Project key
priority = "fields.priority.name"  # Priority (maps to H/M/L)
tags = "fields.labels"          # Jira labels
due = "fields.duedate"          # Due date
entry = "fields.created"        # Created date
modified = "fields.updated"     # Updated date
```

### Jira-CLI Setup

1. **Install Jira-CLI:**
   ```bash
   # macOS
   brew install ankitpokhrel/tap/jira-cli
   
   # Or download from https://github.com/ankitpokhrel/jira-cli/releases
   ```

2. **Configure Jira-CLI:**
   ```bash
   jira init
   # Follow prompts to set up Jira server and credentials
   ```

3. **Configure tw-cli:**
   ```bash
   # Edit ~/.config/tw-cli/config.toml
   [backend]
   type = "jira"
   command = "jira"
   ```

4. **Use tw-cli with Jira:**
   ```bash
   tw-cli view kanban          # View Jira issues as kanban
   tw-cli view table           # View Jira issues as table
   tw-cli shell                # Interactive shell with Jira
   ```

### Field Mapping

The backend uses **dot notation** to extract fields from JSON responses:

```toml
[backend.field_mapping]
description = "fields.summary"  # Extracts data["fields"]["summary"]
project = "fields.project.key"  # Extracts data["fields"]["project"]["key"]
```

### Status and Priority Mapping

**Jira Status → tw-cli:**
- Done/Closed/Resolved/Complete → `completed`
- In Progress/Doing/Active → `pending`
- Waiting/Blocked/On Hold → `waiting`
- Others → `pending`

**Jira Priority → tw-cli:**
- Highest/Critical/Blocker → `H`
- High → `H`
- Medium/Normal → `M`
- Low/Minor → `L`

### Custom Backend Example

```toml
[backend]
type = "custom"
command = "your-cli-tool"
export_format = "json"

[backend.field_mapping]
id = "ticket_number"
description = "title"
status = "state"
# ... define your mappings
```

### Example Configurations

```toml
default_view = "kanban"

[kanban]
group_by = "status"  # status, priority, project, tag
show_completed = true
completed_days = 7

[table]
columns = ["id", "description", "project", "tags", "due", "priority", "urgency"]
default_sort = "urgency"

[colors]
# For black & white mode, use:
priority_high = "white bold"
priority_medium = "white"
priority_low = "white dim"
priority_none = "white dim"

status_active = "white bold"
status_pending = "white"
status_waiting = "white dim"
status_completed = "dim"
status_blocked = "white bold"

urgency_critical_color = "white bold"
urgency_high_color = "white bold"
urgency_medium_color = "white"
urgency_low_color = "white dim"
```

See `example-config.toml` for all available options.

## Requirements

- Python 3.8+
- Taskwarrior
- Rich library

## License

MIT

[colors]
priority_high = "red"
priority_medium = "yellow"
priority_low = "blue"
```

See [example-config.toml](example-config.toml) for full configuration options.

## Requirements

- Python 3.8+
- Taskwarrior installed and configured
- Terminal with color support

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

## License

MIT
