"""
Data models for Taskwarrior tasks and filters
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status values"""
    PENDING = "pending"
    COMPLETED = "completed"
    DELETED = "deleted"
    WAITING = "waiting"
    RECURRING = "recurring"


class TaskPriority(str, Enum):
    """Task priority values"""
    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"
    NONE = ""


class Task(BaseModel):
    """Taskwarrior task model"""
    id: Optional[int] = None
    uuid: str
    description: str
    status: TaskStatus
    entry: datetime
    modified: Optional[datetime] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    due: Optional[datetime] = None
    until: Optional[datetime] = None
    wait: Optional[datetime] = None
    scheduled: Optional[datetime] = None
    recur: Optional[str] = None
    priority: Optional[TaskPriority] = None
    project: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    annotations: List[dict] = Field(default_factory=list)
    depends: List[str] = Field(default_factory=list)
    urgency: float = 0.0
    
    # Virtual tags (computed)
    is_active: bool = Field(default=False, alias="active")
    is_blocked: bool = Field(default=False, alias="blocked")
    is_blocking: bool = Field(default=False, alias="blocking")
    
    class Config:
        populate_by_name = True
        use_enum_values = True
    
    @property
    def has_tag(self) -> callable:
        """Helper to check for tag presence"""
        return lambda tag: tag.lstrip('+') in self.tags
    
    @property
    def age_days(self) -> int:
        """Days since task was created"""
        now = datetime.now()
        entry = self.entry
        # Handle timezone-aware datetimes
        if entry.tzinfo is not None:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            if entry.tzinfo != timezone.utc:
                entry = entry.astimezone(timezone.utc)
        return (now - entry).days
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if self.due and self.status == TaskStatus.PENDING:
            now = datetime.now()
            due = self.due
            if due.tzinfo is not None:
                from datetime import timezone
                now = datetime.now(timezone.utc)
                if due.tzinfo != timezone.utc:
                    due = due.astimezone(timezone.utc)
            return now > due
        return False
    
    @property
    def is_due_soon(self) -> bool:
        """Check if task is due within 3 days"""
        if self.due and self.status == TaskStatus.PENDING:
            now = datetime.now()
            due = self.due
            if due.tzinfo is not None:
                from datetime import timezone
                now = datetime.now(timezone.utc)
                if due.tzinfo != timezone.utc:
                    due = due.astimezone(timezone.utc)
            days_until = (due - now).days
            return 0 <= days_until <= 3
        return False
    
    def __str__(self) -> str:
        """String representation"""
        parts = [f"[{self.id or '?'}]", self.description]
        if self.project:
            parts.append(f"({self.project})")
        if self.tags:
            parts.append(f"+{' +'.join(self.tags)}")
        return " ".join(parts)


class GroupBy(str, Enum):
    """Kanban grouping strategies"""
    STATUS = "status"
    PRIORITY = "priority"
    PROJECT = "project"
    TAG = "tag"
    CUSTOM = "custom"
