#!/usr/bin/env python3
"""
Example: Create a custom view for tw-cli
"""
from typing import List
from rich.panel import Panel
from rich.text import Text
from rich import box

from tw_cli.views.base import BaseView
from tw_cli.models import Task


class CompactView(BaseView):
    """A compact single-line view for each task"""
    
    def render(self, tasks: List[Task]):
        """Render tasks in compact format"""
        if not tasks:
            self.console.print("\n[yellow]No tasks found[/yellow]\n")
            return
        
        # Sort by urgency
        sorted_tasks = sorted(tasks, key=lambda t: t.urgency, reverse=True)
        
        lines = []
        self.console.print()
        
        for task in sorted_tasks:
            line = Text()
            
            # ID
            line.append(f"{task.id:>3}. ", style="dim")
            
            # Urgency indicator (bar graph)
            urgency_level = min(int(task.urgency / 5), 5)  # 0-5 bars
            bars = "█" * urgency_level + "░" * (5 - urgency_level)
            urgency_color = self.get_urgency_color(task.urgency)
            line.append(f"[{bars}] ", style=urgency_color)
            
            # Description
            desc = self.truncate(task.description, 60)
            line.append(desc, style="white")
            
            # Priority badge
            if task.priority:
                pri_color = self.get_priority_color(task.priority)
                line.append(f" [{task.priority}]", style=f"{pri_color} bold")
            
            # Due date
            if task.due:
                due_str = self.format_date(task.due)
                due_style = "red bold" if task.is_overdue else "yellow"
                line.append(f" 📅{due_str}", style=due_style)
            
            self.console.print(line)
        
        self.console.print(f"\n[dim]Total: {len(tasks)} tasks[/dim]\n")


# Example usage
if __name__ == "__main__":
    from tw_cli.taskwarrior import TaskWarriorClient
    from tw_cli.config import get_config
    
    client = TaskWarriorClient()
    config = get_config()
    
    # Get tasks
    tasks = client.execute_command("task status:pending limit:15")
    
    # Render with custom view
    view = CompactView(config=config)
    view.render(tasks)
