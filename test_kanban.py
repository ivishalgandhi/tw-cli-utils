#!/usr/bin/env python3
"""
Quick test script for the improved kanban view
"""

from src.tw_cli.views.kanban import KanbanView
from src.tw_cli.taskwarrior import TaskWarriorClient
from src.tw_cli.config import get_config

def main():
    # Get tasks
    client = TaskWarriorClient()
    tasks = client.get_all_tasks()
    
    # Filter to pending only
    tasks = [t for t in tasks if t.status == "pending"]
    
    # Get config
    config = get_config()
    
    # Create kanban view
    view = KanbanView(config=config)
    
    # Render
    print("\n" + "="*80)
    print("IMPROVED KANBAN VIEW (inspired by kanban-python)")
    print("="*80 + "\n")
    
    view.render(tasks)
    
    print("\n" + "="*80)
    print(f"Total tasks: {len(tasks)}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
