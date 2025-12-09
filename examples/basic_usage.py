#!/usr/bin/env python3
"""
Example usage of tw-cli library for programmatic access
"""
from tw_cli.taskwarrior import TaskWarriorClient
from tw_cli.views.kanban import KanbanView
from tw_cli.views.table import TableView
from tw_cli.views.list import ListView
from tw_cli.config import get_config
from tw_cli.models import GroupBy


def main():
    """Demonstrate programmatic usage"""
    
    # Initialize client
    client = TaskWarriorClient()
    config = get_config()
    
    print("=== Example 1: Kanban View ===\n")
    # Get pending tasks
    tasks = client.execute_command("task status:pending")
    
    # Render in kanban (default: grouped by status)
    kanban = KanbanView(config=config)
    kanban.render(tasks)
    
    print("\n\n=== Example 2: Kanban by Priority ===\n")
    # Kanban grouped by priority
    kanban_priority = KanbanView(group_by=GroupBy.PRIORITY, config=config)
    kanban_priority.render(tasks)
    
    print("\n\n=== Example 3: Table View ===\n")
    # Table view (sorted by urgency)
    table = TableView(config=config)
    table.render(tasks)
    
    print("\n\n=== Example 4: List View ===\n")
    # List view (sorted by urgency)
    list_view = ListView(config=config)
    list_view.render(tasks[:10])  # Show first 10
    
    print("\n\n=== Example 5: Filter by Project ===\n")
    # Filter tasks by project
    personal_tasks = client.execute_command("task project:personal")
    kanban.render(personal_tasks)
    
    print("\n\n=== Example 6: Due Today ===\n")
    # Tasks due today
    due_today = client.execute_command("task due:today")
    table.render(due_today)


if __name__ == "__main__":
    main()
