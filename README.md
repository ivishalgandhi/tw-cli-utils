# tw-cli - Enhanced Taskwarrior CLI

A modern, beautiful CLI interface for Taskwarrior with multiple view modes (kanban, table, markdown) using Rich, inspired by DuckDB CLI.

## Features

- 🎨 **Multiple View Modes**: Kanban, Table, Markdown, List
- 🔄 **Direct Taskwarrior Integration**: Run any taskwarrior command with enhanced output
- 🎯 **Flexible Column Grouping**: Group kanban by status, priority, project, or custom tags
- 🖥️ **Interactive Shell**: Similar to DuckDB CLI with dot commands
- ⚙️ **Highly Configurable**: Customize views, colors, and layouts

## Installation

```bash
cd /Users/vishal/src/tw_cli_utils
pip install -e .
```

## Quick Start

### Interactive Shell Mode

```bash
tw-cli shell
```

In the shell:
```
# Switch view modes
.mode kanban
.mode table
.mode markdown

# Run taskwarrior commands - output rendered in current mode
task +work status:pending
task project:home due:today
task priority:H

# Change kanban grouping
.mode kanban:priority
.mode kanban:project

# Show help
.help

# Exit
.exit
```

### Direct Command Mode

```bash
# View specific tasks in kanban
tw-cli view kanban -- task +work

# View in table mode
tw-cli view table -- task project:home
```

## View Modes

### Kanban

**Column Assignment (Status Grouping):**
- **Backlog** - All pending tasks (not started)
- **In Progress** - Tasks that have been started with `task <id> start` (have a `start` timestamp)
- **Waiting** - Tasks with `status:waiting`
- **Completed** - Recently completed (last 7 days by default)
- **Blocked** - Tasks with `+blocked` tag (shown only if any exist)

**To move a task to "In Progress":**
```bash
task <id> start
```

This sets the `start` timestamp. To stop working on it:
```bash
task <id> stop
```

**Task Overflow Handling:**
- By default, shows max 20 tasks per column (configurable in `config.toml`)
- When there are more, shows truncated list with "... and X more tasks" indicator
- Prevents screen overflow with large task lists

**Alternative groupings:** Priority, Project, Tag, Custom

- **Default grouping**: By status (Backlog → In Progress → Waiting → Completed)
- **Alternative groupings**: Priority, Project, Tag, Custom
- Configure via `.mode kanban:status` or config file

### Table
- Sortable columns with rich formatting
- Color-coded by priority and urgency
- Responsive column widths

### Markdown
- Export-ready format
- Hierarchical by project
- Checkbox-style lists

### List
- Enhanced list view with colors and icons
- Inline tags and metadata

## Configuration

Create `~/.config/tw-cli/config.toml`:

```toml
default_view = "kanban"

[kanban]
group_by = "status"  # or "priority", "project", "tag", "custom"
show_completed = true
completed_days = 7

[table]
columns = ["id", "description", "project", "tags", "due", "priority"]
default_sort = "urgency"

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
