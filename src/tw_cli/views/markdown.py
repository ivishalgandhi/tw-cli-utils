"""
Markdown formatted view for export
"""
from typing import List
from datetime import datetime
from collections import defaultdict

from rich.console import Console

from .base import BaseView
from ..models import Task, TaskStatus


class MarkdownView(BaseView):
    """Markdown formatted output"""
    
    def render(self, tasks: List[Task]):
        """Render tasks as markdown"""
        if not tasks:
            print("\nNo tasks found\n")
            return
        
        output = []
        
        # Add metadata if configured
        if self.config.markdown.include_metadata:
            output.append("---")
            output.append(f"generated: {datetime.now().isoformat()}")
            output.append(f"total_tasks: {len(tasks)}")
            output.append("---")
            output.append("")
        
        # Add title
        output.append("# Tasks")
        output.append("")
        
        # Add summary statistics
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        pending = total - completed
        overdue = sum(1 for t in tasks if t.is_overdue)
        
        output.append(f"**Summary:** {total} tasks ({pending} pending, {completed} completed")
        if overdue:
            output.append(f", {overdue} overdue)")
        else:
            output.append(")")
        output.append("")
        
        # Generate GitHub Flavored Markdown table
        output.append("## Task Summary (Table)")
        output.append("")
        output.extend(self._generate_markdown_table(tasks))
        output.append("")
        
        # Add detailed task list
        output.append("## Detailed Task List")
        output.append("")
        
        if self.config.markdown.group_by_project:
            # Group by project
            grouped = self._group_by_project(tasks)
            for project, project_tasks in grouped.items():
                output.append(f"### {project}")
                output.append("")
                for task in project_tasks:
                    output.append(self._format_task_markdown(task))
                output.append("")
        else:
            # Flat list
            for task in tasks:
                output.append(self._format_task_markdown(task))
        
        # Print output with spacing
        markdown_text = "\n".join(output)
        print(f"\n{markdown_text}\n")
    
    def _generate_markdown_table(self, tasks: List[Task]) -> List[str]:
        """Generate a GitHub Flavored Markdown table"""
        table_lines = []
        
        # Table header
        table_lines.append("| ID | Status | Priority | Description | Project | Tags | Due | Urgency |")
        table_lines.append("|---:|:------:|:--------:|:------------|:--------|:-----|:----|--------:|")
        
        # Table rows
        for task in tasks:
            # Status emoji
            if task.status == TaskStatus.COMPLETED:
                status = "✅"
            elif task.is_active:
                status = "▶️"
            elif task.status == TaskStatus.WAITING:
                status = "⏸"
            elif task.is_blocked:
                status = "🚫"
            else:
                status = "📋"
            
            # Priority
            priority = task.priority if task.priority else "-"
            
            # Description (no truncation)
            desc = task.description
            
            # Project
            project = task.project if task.project else "-"
            
            # Tags
            tags = ", ".join(task.tags[:3]) if task.tags else "-"
            if len(task.tags) > 3:
                tags += f" +{len(task.tags) - 3}"
            
            # Due date
            due = task.due.strftime("%Y-%m-%d") if task.due else "-"
            
            # Urgency
            urgency = f"{task.urgency:.1f}"
            
            # Task ID
            task_id = str(task.id) if task.id else "-"
            
            # Build row
            row = f"| {task_id} | {status} | {priority} | {desc} | {project} | {tags} | {due} | {urgency} |"
            table_lines.append(row)
        
        return table_lines
    
    def _group_by_project(self, tasks: List[Task]) -> dict:
        """Group tasks by project"""
        grouped = defaultdict(list)
        
        for task in tasks:
            project = task.project or "Inbox"
            grouped[project].append(task)
        
        # Sort projects
        return dict(sorted(grouped.items()))
    
    def _format_task_markdown(self, task: Task) -> str:
        """Format a single task as markdown"""
        use_checkbox = self.config.markdown.use_checkboxes
        
        # Checkbox or bullet
        if use_checkbox:
            checkbox = "[x]" if task.status == TaskStatus.COMPLETED else "[ ]"
            line = f"- {checkbox} "
        else:
            line = "- "
        
        # Description
        line += task.description
        
        # Metadata on same line
        metadata = []
        if task.project:
            metadata.append(f"project:{task.project}")
        if task.priority:
            metadata.append(f"priority:{task.priority}")
        
        if task.due:
            metadata.append(f"due:{task.due.strftime('%Y-%m-%d')}")
        
        if task.tags:
            metadata.append(f"tags:{','.join(task.tags)}")
        
        if task.id:
            metadata.append(f"id:{task.id}")
        
        if metadata:
            line += f" `[{' | '.join(metadata)}]`"
        
        return line
