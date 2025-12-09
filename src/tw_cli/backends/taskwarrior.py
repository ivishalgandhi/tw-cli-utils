"""
TaskWarrior backend implementation
"""
from typing import List
from .base import BaseBackend
from ..models import Task
from ..taskwarrior import TaskWarriorClient, TaskWarriorError


class TaskWarriorBackend(BaseBackend):
    """Backend implementation for Taskwarrior"""
    
    def __init__(self, config):
        """Initialize TaskWarrior backend"""
        super().__init__(config)
        self.client = TaskWarriorClient()
    
    def verify_installation(self) -> bool:
        """Verify Taskwarrior is installed"""
        # Client already verifies in __init__
        return True
    
    def execute_command(self, command: str) -> List[Task]:
        """Execute taskwarrior command"""
        return self.client.execute_command(command)
    
    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        """Get all tasks from Taskwarrior"""
        return self.client.get_all_tasks(include_completed)
