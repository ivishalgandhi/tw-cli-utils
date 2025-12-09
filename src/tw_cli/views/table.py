"""
Rich table view with sortable columns and kanban layout
"""
from collections import defaultdict
from typing import List, Dict
from datetime import datetime
from itertools import zip_longest
from rich.table import Table as RichTable
from rich import box

from .base import BaseView
from ..models import Task, TaskStatus, GroupBy


class TableView(BaseView):
    """Table view with rich formatting - supports both regular and kanban layouts"""
    
    def __init__(self, sort_by: str = None, layout: str = "table", group_by: GroupBy = None, **kwargs):
        """
        Initialize table view
        
        Args:
            sort_by: Column to sort by (overrides config if provided)
            layout: Layout mode - "table" (default) or "kanban"
            group_by: Grouping strategy for kanban layout (overrides config if provided)
        """
        super().__init__(**kwargs)
        self.sort_by = sort_by or self.config.table.default_sort
        self.layout = layout
        self.group_by = group_by or self.config.kanban.group_by
    
    def render(self, tasks: List[Task]):
        """Render tasks based on layout mode"""
        if self.layout == "kanban":
            self._render_kanban(tasks)
        else:
            self._render_table(tasks)
    
    def _render_table(self, tasks: List[Task]):
        """Render tasks as a traditional table"""
        if not tasks:
            from rich.panel import Panel
            self.console.print()
            border_style = self.config.colors.border_style if self.config.colors.enabled else ""
            self.console.print(Panel(
                "[yellow]No tasks found[/yellow]\n\nTry adjusting your filter or run: [cyan]task add 'Your first task'[/cyan]",
                border_style=border_style,
                padding=(1, 2)
            ))
            self.console.print()
            return
        
        # Sort tasks
        sorted_tasks = self._sort_tasks(tasks)
        
        # Count stats
        overdue = sum(1 for t in tasks if t.is_overdue)
        due_soon = sum(1 for t in tasks if t.is_due_soon and not t.is_overdue)
        high_urgency = sum(1 for t in tasks if t.urgency >= 10)
        
        # Create table
        table = self._create_table()
        
        # Add rows
        for task in sorted_tasks:
            self._add_task_row(table, task)
        
        # Render with spacing
        self.console.print()
        self.console.print(table)
        
        # Show stats
        stats_parts = [f"Total: {len(tasks)} tasks"]
        if overdue:
            stats_parts.append(f"[red]{overdue} overdue[/red]")
        if due_soon:
            stats_parts.append(f"[yellow]{due_soon} due soon[/yellow]")
        if high_urgency:
            stats_parts.append(f"[bold]{high_urgency} high urgency[/bold]")
        
        self.console.print(f"\n[dim]{' • '.join(stats_parts)}[/dim]\n")
    
    def _sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by the configured column"""
        reverse = self.config.table.sort_order == "desc"
        
        if self.sort_by == "urgency":
            return sorted(tasks, key=lambda t: t.urgency, reverse=reverse)
        elif self.sort_by == "id":
            return sorted(tasks, key=lambda t: t.id or 0, reverse=reverse)
        elif self.sort_by == "due":
            return sorted(
                tasks,
                key=lambda t: t.due if t.due else (datetime.max if not reverse else datetime.min),
                reverse=reverse
            )
        elif self.sort_by == "priority":
            priority_order = {"H": 3, "M": 2, "L": 1, "": 0, None: 0}
            return sorted(
                tasks,
                key=lambda t: priority_order.get(t.priority or "", 0),
                reverse=reverse
            )
        elif self.sort_by == "project":
            return sorted(tasks, key=lambda t: t.project or "", reverse=reverse)
        elif self.sort_by == "description":
            return sorted(tasks, key=lambda t: t.description, reverse=reverse)
        else:
            return tasks
    
    def _create_table(self) -> RichTable:
        """Create the base table structure"""
        table = RichTable(
            show_header=True,
            header_style=self.config.colors.table_header if self.config.colors.enabled else "bold",
            box=box.SIMPLE if not self.config.table.show_grid else box.ROUNDED,
            show_lines=False,
            pad_edge=True,
            expand=True,  # Expand to full width
            padding=(0, 1),  # Horizontal padding for cells
        )
        
        # Add columns based on config
        columns = self.config.table.columns
        
        if "id" in columns:
            id_style = self.config.colors.column_id if self.config.colors.enabled else ""
            table.add_column("ID", justify="right", style=id_style, no_wrap=True, min_width=4, max_width=6)
        if "description" in columns:
            desc_style = self.config.colors.column_description if self.config.colors.enabled else ""
            table.add_column("Description", style=desc_style, no_wrap=False, ratio=3)  # Takes 3x space
        if "project" in columns:
            project_style = self.config.colors.column_project if self.config.colors.enabled else ""
            table.add_column("Project", style=project_style, no_wrap=True, ratio=1)
        if "tags" in columns:
            tags_style = self.config.colors.column_tags if self.config.colors.enabled else ""
            table.add_column("Tags", style=tags_style, no_wrap=False, ratio=1)
        if "due" in columns:
            due_col_style = self.config.colors.column_due if self.config.colors.enabled else ""
            table.add_column("Due", style=due_col_style, no_wrap=True, min_width=12, max_width=15)
        if "priority" in columns:
            table.add_column("Pri", justify="center", no_wrap=True, min_width=4, max_width=5)
        if "urgency" in columns:
            table.add_column("Urg", justify="right", no_wrap=True, min_width=5, max_width=6)
        if "status" in columns:
            table.add_column("Status", no_wrap=True, min_width=8, max_width=12)
        
        return table
    
    def _add_task_row(self, table: RichTable, task: Task):
        """Add a task as a row to the table"""
        columns = self.config.table.columns
        row = []
        
        if "id" in columns:
            row.append(str(task.id or "?"))
        
        if "description" in columns:
            # Apply styling based on urgency - don't truncate, let table handle it
            desc = task.description
            
            # Status icon from config
            if not self.config.colors.enabled:
                # Black & white mode - no icons
                icon = ""
            else:
                # Use configured colors
                if task.status == "completed":
                    icon = self.config.colors.icon_completed
                elif task.is_active:
                    icon = self.config.colors.icon_active
                elif task.status == "waiting":
                    icon = self.config.colors.icon_waiting
                elif task.is_blocked:
                    icon = self.config.colors.icon_blocked
                else:
                    icon = self.config.colors.icon_pending
            
            urgency_color = self.get_urgency_color(task.urgency) if self.config.colors.enabled else ""
            
            # Add overdue indicator
            if task.is_overdue and self.config.colors.enabled:
                indicator = self.config.colors.overdue_indicator
                desc = f"{indicator} {desc}"
            
            # Build description with or without icon/color
            if self.config.colors.enabled:
                desc_formatted = f"{icon} [{urgency_color}]{desc}[/{urgency_color}]"
            else:
                desc_formatted = f"{icon} {desc}".strip() if icon else desc
            
            row.append(desc_formatted)
        
        if "project" in columns:
            row.append(task.project or "")
        
        if "tags" in columns:
            row.append(self.format_tags(task.tags, max_length=20))
        
        if "due" in columns:
            if task.due:
                due_str = self.format_date(task.due)
                if self.config.colors.enabled:
                    if task.is_overdue:
                        due_style = self.config.colors.due_overdue
                    elif task.is_due_soon:
                        due_style = self.config.colors.due_soon
                    else:
                        due_style = self.config.colors.due_normal
                    row.append(f"[{due_style}]{due_str}[/{due_style}]")
                else:
                    row.append(due_str)
            else:
                row.append("")
        
        if "priority" in columns:
            if task.priority:
                if self.config.colors.enabled:
                    pri_color = self.get_priority_color(task.priority)
                    row.append(f"[{pri_color}]{task.priority}[/{pri_color}]")
                else:
                    row.append(task.priority)
            else:
                row.append("")
        
        if "urgency" in columns:
            if self.config.colors.enabled:
                urg_color = self.get_urgency_color(task.urgency)
                row.append(f"[{urg_color}]{task.urgency:.1f}[/{urg_color}]")
            else:
                row.append(f"{task.urgency:.1f}")
        
        if "status" in columns:
            status_color = self.get_status_color(task)
            row.append(f"[{status_color}]{task.status}[/{status_color}]")
        
        table.add_row(*row)
    
    # ============================================================================
    # KANBAN LAYOUT METHODS
    # ============================================================================
    
    def _render_kanban(self, tasks: List[Task]):
        """Render tasks as a kanban board (table-based layout)"""
        if not tasks:
            from rich.panel import Panel
            self.console.print()
            border_style = self.config.colors.border_style if self.config.colors.enabled else ""
            self.console.print(Panel(
                "[yellow]No tasks found[/yellow]\n\nTry adjusting your filter or run: [cyan]task add 'Your first task'[/cyan]",
                border_style=border_style,
                padding=(1, 2)
            ))
            self.console.print()
            return
        
        # Group tasks based on strategy
        columns_dict = self._group_tasks(tasks)
        
        # Create table-based kanban board
        kanban_table = self._create_kanban_table(columns_dict)
        
        # Render with spacing
        self.console.print()
        self.console.print(kanban_table)
        self.console.print()
    
    def _group_tasks(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """Group tasks based on the current grouping strategy"""
        if self.group_by == GroupBy.STATUS:
            return self._group_by_status(tasks)
        elif self.group_by == GroupBy.PRIORITY:
            return self._group_by_priority(tasks)
        elif self.group_by == GroupBy.PROJECT:
            return self._group_by_project_kanban(tasks)
        elif self.group_by == GroupBy.TAG:
            return self._group_by_tag(tasks)
        elif self.group_by == GroupBy.CUSTOM:
            return self._group_by_custom(tasks)
        else:
            return self._group_by_status(tasks)
    
    def _group_by_status(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """Group tasks by status (default kanban view)"""
        columns = {
            "Backlog": [],
            "In Progress": [],
            "Waiting": [],
            "Completed": [],
        }
        
        # Optionally add blocked column
        if any(task.is_blocked for task in tasks):
            columns["Blocked"] = []
        
        for task in tasks:
            if task.status == TaskStatus.COMPLETED:
                # Only show recently completed tasks
                if self.config.kanban.show_completed:
                    if task.end:
                        now = datetime.now()
                        end = task.end
                        if end.tzinfo is not None:
                            from datetime import timezone
                            now = datetime.now(timezone.utc)
                            if end.tzinfo != timezone.utc:
                                end = end.astimezone(timezone.utc)
                        days_ago = (now - end).days
                    else:
                        days_ago = 999
                    if days_ago <= self.config.kanban.completed_days:
                        columns["Completed"].append(task)
            elif task.is_blocked:
                columns["Blocked"].append(task)
            elif task.status == TaskStatus.WAITING:
                columns["Waiting"].append(task)
            elif task.start or task.is_active:  # Has 'start' timestamp or ACTIVE tag
                columns["In Progress"].append(task)
            elif task.status == TaskStatus.PENDING:
                columns["Backlog"].append(task)
        
        # Sort by urgency within each column
        for column_tasks in columns.values():
            column_tasks.sort(key=lambda t: t.urgency, reverse=True)
        
        return columns
    
    def _group_by_priority(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """Group tasks by priority"""
        from ..models import TaskPriority
        
        columns = {
            "High Priority": [],
            "Medium Priority": [],
            "Low Priority": [],
            "No Priority": [],
        }
        
        for task in tasks:
            if task.status == TaskStatus.COMPLETED:
                continue  # Skip completed in priority view
            
            if task.priority == TaskPriority.HIGH:
                columns["High Priority"].append(task)
            elif task.priority == TaskPriority.MEDIUM:
                columns["Medium Priority"].append(task)
            elif task.priority == TaskPriority.LOW:
                columns["Low Priority"].append(task)
            else:
                columns["No Priority"].append(task)
        
        # Sort by urgency within each column
        for column_tasks in columns.values():
            column_tasks.sort(key=lambda t: t.urgency, reverse=True)
        
        return columns
    
    def _group_by_project_kanban(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """Group tasks by project"""
        columns = defaultdict(list)
        
        for task in tasks:
            if task.status == TaskStatus.COMPLETED:
                continue  # Skip completed in project view
            
            project = task.project or "No Project"
            columns[project].append(task)
        
        # Sort columns by name
        sorted_columns = dict(sorted(columns.items()))
        
        # Sort tasks within columns by urgency
        for column_tasks in sorted_columns.values():
            column_tasks.sort(key=lambda t: t.urgency, reverse=True)
        
        return sorted_columns
    
    def _group_by_tag(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """Group tasks by tag prefix"""
        tag_prefix = self.config.kanban.tag_prefix or "area"
        columns = defaultdict(list)
        
        for task in tasks:
            if task.status == TaskStatus.COMPLETED:
                continue
            
            # Find matching tag
            matching_tag = None
            for tag in task.tags:
                if tag.startswith(f"{tag_prefix}."):
                    matching_tag = tag.replace(f"{tag_prefix}.", "")
                    break
            
            column_name = matching_tag or "Untagged"
            columns[column_name].append(task)
        
        # Sort columns by name
        sorted_columns = dict(sorted(columns.items()))
        
        # Sort tasks within columns by urgency
        for column_tasks in sorted_columns.values():
            column_tasks.sort(key=lambda t: t.urgency, reverse=True)
        
        return sorted_columns
    
    def _group_by_custom(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """Group tasks by custom column definitions"""
        # TODO: Implement custom columns from config
        # For now, fall back to status
        return self._group_by_status(tasks)
    
    def _create_kanban_table(self, columns_dict: Dict[str, List[Task]]) -> RichTable:
        """Create a table-based kanban board inspired by kanban-python"""
        # Create main table using rounded box with column lines only
        table = RichTable(
            show_header=True,
            header_style="bold",
            box=box.ROUNDED,
            show_lines=False,  # No horizontal lines between rows
            padding=(0, 1),
        )
        
        # Convert tasks to formatted strings for each column
        columns_formatted = {}
        for column_name, column_tasks in columns_dict.items():
            columns_formatted[column_name] = [
                self._format_task_for_kanban(task, 40) for task in column_tasks
            ]
        
        # Add columns with count and proper styling
        for column_name, task_strings in columns_formatted.items():
            count = len(task_strings)
            
            # Style based on column type - use config colors
            if not self.config.colors.enabled:
                header_style = "bold"
            elif "Progress" in column_name:
                header_style = self.config.colors.header_in_progress
            elif "Completed" in column_name:
                header_style = self.config.colors.header_completed
            elif "Blocked" in column_name:
                header_style = self.config.colors.header_blocked
            elif "Backlog" in column_name:
                header_style = self.config.colors.header_backlog
            elif "Waiting" in column_name:
                header_style = self.config.colors.header_waiting
            else:
                header_style = self.config.colors.header_default
            
            # Column header without task count
            header = column_name
            
            table.add_column(
                header,
                header_style=header_style,
                justify="left",
                overflow="fold",
                no_wrap=False,
                vertical="top",
                min_width=40,
            )
        
        # Use zip_longest to align tasks horizontally (like kanban-python does)
        for row_tasks in zip_longest(*columns_formatted.values(), fillvalue=""):
            table.add_row(*row_tasks)
        
        return table
    
    def _format_task_for_kanban(self, task: Task, column_width: int = 40) -> str:
        """Format task for kanban board cell (inspired by kanban-python)"""
        # Format ID with padding for alignment
        task_id = task.id or 0
        if self.config.colors.enabled:
            id_str = f"[cyan]{task_id:02d}[/cyan]" if task_id < 100 else f"[cyan]{task_id}[/cyan]"
        else:
            id_str = f"{task_id:02d}" if task_id < 100 else f"{task_id}"
        
        # Get primary tag (project or first tag)
        tag = ""
        if task.project:
            tag = f"[blue]{task.project}[/blue]" if self.config.colors.enabled else f"{task.project}"
        elif task.tags:
            # Get first tag or most relevant one
            tag_text = task.tags[0] if task.tags else ""
            tag = f"[orange3]{tag_text}[/orange3]" if self.config.colors.enabled else f"{tag_text}"
        else:
            tag = "[dim]--[/dim]" if self.config.colors.enabled else "--"
        
        # Truncate description to fit column width dynamically
        max_desc_len = max(15, column_width - 15)
        desc = task.description[:max_desc_len]
        if len(task.description) > max_desc_len:
            desc += "..."
        
        # Color based on urgency
        urgency_color = self.get_urgency_color(task.urgency) if self.config.colors.enabled else ""
        
        # Build task string: [ID] (TAG) Description
        if self.config.colors.enabled:
            task_str = f"[[{id_str}]] ({tag}) [{urgency_color}]{desc}[/{urgency_color}]"
        else:
            task_str = f"[[{id_str}]] ({tag}) {desc}"
        
        # Add urgency indicator if high
        if task.urgency >= 10:
            if self.config.colors.enabled:
                task_str += f" [red]|{task.urgency:.1f}|[/red]"
            else:
                task_str += f" |{task.urgency:.1f}|"
        
        # Add due date indicator if present
        if task.due:
            now = datetime.now()
            due = task.due
            if due.tzinfo is not None:
                from datetime import timezone
                now = datetime.now(timezone.utc)
                if due.tzinfo != timezone.utc:
                    due = due.astimezone(timezone.utc)
            days_left = (due - now).days
            
            if self.config.colors.enabled:
                if days_left < 0:
                    task_str += f" [red]|{days_left:02d}|[/red]"
                elif days_left <= 7:
                    task_str += f" [yellow]|{days_left:02d}|[/yellow]"
            else:
                task_str += f" |{days_left:02d}|"
        
        return task_str
