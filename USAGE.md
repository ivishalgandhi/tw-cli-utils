# tw-cli Usage Guide

## Running tw-cli

Since you're using `uv`, here are the commands to run tw-cli:

### 1. View Kanban Board

```bash
uv run tw-cli view kanban
```

This shows all your pending tasks in a kanban-style board with columns:
- 📋 Backlog (pending tasks not started)
- ▶️ In Progress (tasks you've started with `task <id> start`)
- ⏸ Waiting (tasks with status:waiting)
- ✅ Completed (recently completed tasks)
- 🚫 Blocked (tasks with +blocked tag, if any)

### 2. Interactive Shell Mode

```bash
uv run tw-cli shell
```

In shell mode you can:

```
# Switch view modes
.mode kanban
.mode table
.mode markdown
.mode list

# Change kanban grouping
.mode kanban:status     # Default - group by status
.mode kanban:priority   # Group by priority (High/Medium/Low)
.mode kanban:project    # Group by project
.mode kanban:tag        # Group by tags

# Run any taskwarrior command
task +work status:pending
task project:home due:today
task priority:H

# Exit
.exit
```

### 3. Other View Modes

```bash
# Table view
uv run tw-cli view table

# Markdown view
uv run tw-cli view markdown

# List view
uv run tw-cli view list
```

### 4. Filter Specific Tasks

You can pass taskwarrior filters:

```bash
# View only work tasks in kanban
uv run tw-cli view kanban --cmd "task +work"

# View high priority tasks
uv run tw-cli view table --cmd "task priority:H"

# View tasks due today
uv run tw-cli view kanban --cmd "task due:today"
```

### 5. Change Kanban Grouping

```bash
# Group by priority
uv run tw-cli view kanban --group priority

# Group by project
uv run tw-cli view kanban --group project

# Group by tag (uses tag_prefix from config)
uv run tw-cli view kanban --group tag
```

## Configuration

Edit `~/.config/tw-cli/config.toml` (or copy from `example-config.toml`):

```toml
# Set default view
default_view = "kanban"

[kanban]
# Change grouping default
group_by = "status"  # or "priority", "project", "tag"

# Show completed tasks
show_completed = true
completed_days = 7

# Adjust column width
column_min_width = 40  # Make columns wider/narrower

# Maximum tasks per column
max_tasks_per_column = 20
```

## Tips

1. **To move tasks to "In Progress"**: Use `task <id> start`
2. **To mark complete**: Use `task <id> done`
3. **For blocked tasks**: Add tag with `task <id> modify +blocked`
4. **Wider columns**: Increase `column_min_width` in config if project names are long
5. **Quick updates**: Use shell mode for rapid task viewing and updates
