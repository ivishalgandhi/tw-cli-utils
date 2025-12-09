"""
Base backend interface for CLI tools
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import Task


class BaseBackend(ABC):
    """Abstract base class for backend implementations"""
    
    def __init__(self, config):
        """
        Initialize backend with configuration
        
        Args:
            config: BackendConfig instance from configuration
        """
        self.config = config
    
    @abstractmethod
    def verify_installation(self) -> bool:
        """
        Verify that the backend CLI tool is installed and accessible
        
        Returns:
            bool: True if installed, raises exception otherwise
        """
        pass
    
    @abstractmethod
    def execute_command(self, command: str) -> List[Task]:
        """
        Execute a command and return list of tasks
        
        Args:
            command: Command string to execute
            
        Returns:
            List[Task]: Parsed tasks from command output
        """
        pass
    
    @abstractmethod
    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        """
        Get all tasks from the backend
        
        Args:
            include_completed: Whether to include completed tasks
            
        Returns:
            List[Task]: All tasks
        """
        pass
    
    def map_field(self, data: dict, field_path: str) -> Optional[any]:
        """
        Extract field value using dot notation path
        
        Args:
            data: Dictionary to extract from
            field_path: Dot-separated path like "fields.summary"
            
        Returns:
            Value at path or None
        """
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
                
            if value is None:
                return None
        
        return value
