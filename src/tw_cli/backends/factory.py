"""
Backend factory for creating appropriate backend based on configuration
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import BackendConfig

from .base import BaseBackend
from .taskwarrior import TaskWarriorBackend
from .jira import JiraBackend


class UnsupportedBackendError(Exception):
    """Raised when backend type is not supported"""
    pass


def create_backend(config: 'BackendConfig') -> BaseBackend:
    """
    Create appropriate backend based on configuration
    
    Args:
        config: BackendConfig instance with backend settings
    
    Returns:
        BaseBackend: Instantiated backend (TaskWarrior, Jira, etc.)
    
    Raises:
        UnsupportedBackendError: If backend type is not supported
    
    Example:
        >>> from tw_cli.config import load_config
        >>> config = load_config()
        >>> backend = create_backend(config.backend)
        >>> tasks = backend.get_all_tasks()
    """
    backend_type = config.type.lower()
    
    if backend_type == "taskwarrior":
        return TaskWarriorBackend(config)
    elif backend_type == "jira":
        return JiraBackend(config)
    elif backend_type == "custom":
        # For custom backends, default to Jira-like behavior
        # Users can extend by subclassing JiraBackend
        return JiraBackend(config)
    else:
        raise UnsupportedBackendError(
            f"Unsupported backend type: {backend_type}\n"
            f"Supported types: taskwarrior, jira, custom"
        )
