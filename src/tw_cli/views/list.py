"""
Enhanced list view with rich formatting
"""
from typing import List
from rich.text import Text

from .base import BaseView
from ..models import Task


class ListView(BaseView):
    """Enhanced list view with colors and icons"""
    
    def render(self, tasks: List[Task]):
        """Render tasks as an enhanced list"""
        if not tasks:
            from rich.panel import Panel
            self.console.print()
            self.console.print(Panel(
                "[yellow]No tasks found[/yellow]\n\nTry adjusting your filter or run: [cyan]task add 'Your first task'[/cyan]",
                border_style="yellow",
                padding=(1, 2)
            ))
            self.console.print()
            return
        
        # Sort by urgency
        sorted_tasks = sorted(tasks, key=lambda t: t.urgency, reverse=True)
        
        # Count stats
        overdue = sum(1 for t in tasks if t.is_overdue)
        due_soon = sum(1 for t in tasks if t.is_due_soon and not t.is_overdue)
        
        self.console.print()  # Top margin
        for i, task in enumerate(sorted_tasks, 1):
            self._render_task(task)
            # Add spacing after high priority groups
            if i < len(sorted_tasks) and task.urgency >= 10 and sorted_tasks[i].urgency < 10:
                self.console.print()
        
        # Show stats
        stats_parts = [f"Total: {len(tasks)} tasks"]
        if overdue:
            stats_parts.append(f"[red]{overdue} overdue[/red]")
        if due_soon:
            stats_parts.append(f"[yellow]{due_soon} due soon[/yellow]")
        
        self.console.print(f"\n[dim]{' • '.join(stats_parts)}[/dim]\n")
    
    def _render_task(self, task: Task):
        """Render a single task"""
        line = Text()
        
        # ID with better formatting
        if self.config.list.show_ids:
            line.append(f"[{task.id or '?':>3}] ", style="dim cyan")
        
        # Status icon with color
        if task.status == "completed":
            line.append("✓ ", style="green")
        elif task.is_active:
            line.append("▶ ", style="yellow")
        elif task.status == "waiting":
            line.append("⏸ ", style="blue")
        elif task.is_blocked:
            line.append("🚫 ", style="red")
        else:
            line.append("○ ", style="dim")
        
        # Priority icon
        pri_icon = self.get_priority_icon(task.priority)
        if pri_icon:
            line.append(f"{pri_icon} ")
        
        # Overdue indicator
        if task.is_overdue:
            line.append("⚠ ", style="red bold")
        
        # Description
        desc = task.description
        if self.config.list.truncate_description:
            desc = self.truncate(desc, self.config.list.max_description_length)
        
        urgency_color = self.get_urgency_color(task.urgency)
        line.append(desc, style=urgency_color)
        
        # Project
        if task.project:
            line.append(f" ({task.project})", style="blue dim")
        
        # Tags - better formatting
        if task.tags:
            tags_display = self.format_tags(task.tags, max_length=40)
            line.append(f" {tags_display}", style="magenta dim")
        
        # Due date with better icon
        if task.due:
            due_str = " 📅  " + self.format_date(task.due)
            due_style = "red bold" if task.is_overdue else "yellow" if task.is_due_soon else "cyan dim"
            line.append(due_str, style=due_style)
        
        # Urgency with better styling
        urg_style = "red bold" if task.urgency >= 15 else "yellow" if task.urgency >= 10 else "dim"
        line.append(f" [{task.urgency:.1f}]", style=urg_style)
        
        self.console.print(line)
