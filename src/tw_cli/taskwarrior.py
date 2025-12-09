"""
Taskwarrior command executor and interface
"""
import json
import subprocess
from typing import List, Optional
from pathlib import Path

from .models import Task


class TaskWarriorError(Exception):
    """Exception raised for Taskwarrior command errors"""
    pass


class TaskWarriorClient:
    """Client for executing Taskwarrior commands and parsing results"""
    
    def __init__(self):
        """Initialize the Taskwarrior client"""
        self._verify_installation()
        self._context_filter = self._get_context_filter()
    
    def _get_context_filter(self) -> Optional[str]:
        """Get the active context filter from taskwarrior"""
        try:
            import os
            env = os.environ.copy()
            
            result = subprocess.run(
                ["task", "context", "show"],
                capture_output=True,
                text=True,
                timeout=5,
                env=env
            )
            
            if result.returncode == 0 and result.stdout:
                # Parse output to get read filter
                # Format: "Context 'name' with filter 'xxx' is currently applied"
                for line in result.stdout.split('\n'):
                    if 'read filter:' in line.lower():
                        # Extract filter between quotes
                        import re
                        match = re.search(r"'([^']+)'", line)
                        if match:
                            return match.group(1)
            return None
        except:
            return None
    
    def _verify_installation(self):
        """Verify that Taskwarrior is installed"""
        try:
            result = subprocess.run(
                ["task", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise TaskWarriorError("Taskwarrior is not properly installed")
        except FileNotFoundError:
            raise TaskWarriorError(
                "Taskwarrior not found. Please install it first:\n"
                "  macOS: brew install task\n"
                "  Ubuntu: sudo apt install taskwarrior"
            )
        except subprocess.TimeoutExpired:
            raise TaskWarriorError("Taskwarrior command timed out")
    
    def execute_command(self, command: str) -> List[Task]:
        """
        Execute a taskwarrior command and return parsed tasks
        
        Args:
            command: Taskwarrior command (e.g., "task +work status:pending")
        
        Returns:
            List of Task objects
        
        Raises:
            TaskWarriorError: If command execution fails
        """
        # Parse command - if it starts with "task", use it as-is
        # Otherwise prepend "task"
        cmd_parts = command.strip().split()
        if not cmd_parts:
            raise TaskWarriorError("Empty command")
        
        if cmd_parts[0] != "task":
            cmd_parts = ["task"] + cmd_parts
        
        # If there's an active context and no explicit filter, add context filter
        # This is needed because 'task export' doesn't respect context automatically
        if self._context_filter and len(cmd_parts) == 1:
            # Only 'task' command, add context filter
            cmd_parts.append(self._context_filter)
        
        # Append "export" to get JSON output
        cmd_parts.append("export")
        
        try:
            # Preserve environment to respect ~/.taskrc and context settings
            import os
            env = os.environ.copy()
            
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                raise TaskWarriorError(f"Command failed: {error_msg}")
            
            # Parse JSON output
            if not result.stdout.strip():
                return []  # No tasks found
            
            task_data = json.loads(result.stdout)
            return self._parse_tasks(task_data)
            
        except subprocess.TimeoutExpired:
            raise TaskWarriorError("Command timed out")
        except json.JSONDecodeError as e:
            raise TaskWarriorError(f"Failed to parse task data: {e}")
        except Exception as e:
            raise TaskWarriorError(f"Unexpected error: {e}")
    
    def _parse_tasks(self, task_data: List[dict]) -> List[Task]:
        """
        Parse raw task data into Task objects
        
        Args:
            task_data: List of task dictionaries from JSON export
        
        Returns:
            List of Task objects
        """
        tasks = []
        for data in task_data:
            try:
                # Normalize the data
                normalized = self._normalize_task_data(data)
                task = Task(**normalized)
                tasks.append(task)
            except Exception as e:
                # Log warning but continue processing other tasks
                print(f"Warning: Failed to parse task {data.get('uuid', 'unknown')}: {e}")
                continue
        
        return tasks
    
    def _normalize_task_data(self, data: dict) -> dict:
        """
        Normalize task data to match our Task model
        
        Args:
            data: Raw task data from Taskwarrior
        
        Returns:
            Normalized dictionary
        """
        normalized = data.copy()
        
        # Convert date strings to datetime objects
        date_fields = ['entry', 'modified', 'start', 'end', 'due', 'until', 'wait', 'scheduled']
        for field in date_fields:
            if field in normalized and normalized[field]:
                # Taskwarrior dates are in ISO format with timezone
                try:
                    from dateutil import parser
                    normalized[field] = parser.parse(normalized[field])
                except:
                    normalized[field] = None
        
        # Handle tags (ensure it's a list)
        if 'tags' not in normalized:
            normalized['tags'] = []
        
        # Handle urgency (ensure it's a float)
        if 'urgency' in normalized:
            normalized['urgency'] = float(normalized['urgency'])
        else:
            normalized['urgency'] = 0.0
        
        # Handle depends (convert to list if needed)
        if 'depends' in normalized:
            if isinstance(normalized['depends'], str):
                normalized['depends'] = [normalized['depends']]
        else:
            normalized['depends'] = []
        
        # Check for virtual tags
        tags = normalized.get('tags', [])
        normalized['is_active'] = 'ACTIVE' in tags
        normalized['is_blocked'] = 'BLOCKED' in tags
        normalized['is_blocking'] = 'BLOCKING' in tags
        
        return normalized
    
    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        """
        Get all tasks
        
        Args:
            include_completed: If True, include completed tasks
        
        Returns:
            List of tasks
        """
        if include_completed:
            return self.execute_command("task status:pending,completed")
        else:
            return self.execute_command("task status:pending")
