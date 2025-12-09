"""
Base view class for all display modes
"""
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime, timedelta

from rich.console import Console
from rich.style import Style

from ..models import Task, TaskPriority
from ..config import Config, get_config


class BaseView(ABC):
    """Abstract base class for task views"""
    
    def __init__(self, config: Config = None):
        """
        Initialize the view
        
        Args:
            config: Configuration object (uses global config if not provided)
        """
        self.config = config or get_config()
        self.console = Console()
    
    @abstractmethod
    def render(self, tasks: List[Task]):
        """
        Render tasks in this view
        
        Args:
            tasks: List of tasks to render
        """
        pass
    
    def get_priority_color(self, priority: TaskPriority) -> str:
        """Get color for a priority level"""
        if priority == TaskPriority.HIGH:
            return self.config.colors.priority_high
        elif priority == TaskPriority.MEDIUM:
            return self.config.colors.priority_medium
        elif priority == TaskPriority.LOW:
            return self.config.colors.priority_low
        else:
            return self.config.colors.priority_none
    
    def get_urgency_color(self, urgency: float) -> str:
        """Get color for an urgency value"""
        if urgency >= self.config.colors.urgency_critical:
            return self.config.colors.urgency_critical_color
        elif urgency >= self.config.colors.urgency_high:
            return self.config.colors.urgency_high_color
        elif urgency >= self.config.colors.urgency_medium:
            return self.config.colors.urgency_medium_color
        else:
            return self.config.colors.urgency_low_color
    
    def get_status_color(self, task: Task) -> str:
        """Get color for a task based on its status"""
        if task.is_active:
            return self.config.colors.status_active
        elif task.is_blocked:
            return self.config.colors.status_blocked
        elif task.status == "waiting":
            return self.config.colors.status_waiting
        elif task.status == "completed":
            return self.config.colors.status_completed
        else:
            return self.config.colors.status_pending
    
    def format_date(self, dt: datetime) -> str:
        """Format a datetime for display"""
        if not dt:
            return ""
        
        # Make now timezone-aware if dt is timezone-aware
        now = datetime.now()
        if dt.tzinfo is not None:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            # Convert both to same timezone for comparison
            if dt.tzinfo != timezone.utc:
                dt = dt.astimezone(timezone.utc)
        
        diff = dt - now
        
        # If it's today, show time
        if dt.date() == now.date():
            return f"Today {dt.strftime('%H:%M')}"
        
        # If it's tomorrow
        elif diff.days == 1:
            return "Tomorrow"
        
        # If it's yesterday (for completed tasks)
        elif diff.days == -1:
            return "Yesterday"
        
        # If it's within a week
        elif 0 < diff.days < 7:
            return dt.strftime("%A")  # Day name
        
        # If it's past (negative days)
        elif diff.days < 0:
            days_ago = abs(diff.days)
            if days_ago == 1:
                return "1 day ago"
            elif days_ago < 7:
                return f"{days_ago} days ago"
            elif days_ago < 30:
                weeks = days_ago // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                return dt.strftime("%Y-%m-%d")
        
        # Otherwise, show date
        else:
            return dt.strftime("%Y-%m-%d")
    
    def format_tags(self, tags: List[str], max_length: int = 50) -> str:
        """Format tags for display"""
        if not tags:
            return ""
        
        tag_str = " ".join(f"+{tag}" for tag in tags)
        if len(tag_str) > max_length:
            tag_str = tag_str[:max_length - 3] + "..."
        return tag_str
    
    def truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    def get_priority_icon(self, priority: TaskPriority) -> str:
        """Get an icon/indicator for priority"""
        if priority == TaskPriority.HIGH:
            return "🔴"
        elif priority == TaskPriority.MEDIUM:
            return "🟡"
        elif priority == TaskPriority.LOW:
            return "🔵"
        return ""
    
    def get_status_icon(self, task: Task) -> str:
        """Get an icon for task status"""
        if task.status == "completed":
            return "✓"
        elif task.is_active:
            return "▶"
        elif task.status == "waiting":
            return "⏸"
        elif task.is_blocked:
            return "🚫"
        else:
            return "○"
    
    def format_duration(self, days: int) -> str:
        """Format a duration in days to human readable format"""
        if days == 0:
            return "today"
        elif days == 1:
            return "tomorrow"
        elif days == -1:
            return "yesterday"
        elif days < -365:
            years = abs(days) // 365
            return f"{years}y ago"
        elif days < -30:
            months = abs(days) // 30
            return f"{months}mo ago"
        elif days < -7:
            weeks = abs(days) // 7
            return f"{weeks}w ago"
        elif days < 0:
            return f"{abs(days)}d ago"
        elif days < 7:
            return f"{days}d"
        elif days < 30:
            weeks = days // 7
            return f"{weeks}w"
        elif days < 365:
            months = days // 30
            return f"{months}mo"
        else:
            years = days // 365
            return f"{years}y"
