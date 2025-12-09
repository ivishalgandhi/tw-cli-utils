"""
Backend abstraction layer for different CLI tools
"""
from .base import BaseBackend
from .taskwarrior import TaskWarriorBackend
from .jira import JiraBackend
from .factory import create_backend

__all__ = [
    "BaseBackend",
    "TaskWarriorBackend", 
    "JiraBackend",
    "create_backend"
]
