"""
Jira-CLI backend implementation
"""
import json
import subprocess
from typing import List, Optional, Dict, Any
from datetime import datetime
from dateutil import parser as date_parser

from .base import BaseBackend
from ..models import Task


class JiraBackendError(Exception):
    """Exception raised for Jira-CLI command errors"""
    pass


class JiraBackend(BaseBackend):
    """Backend implementation for Jira-CLI"""
    
    def __init__(self, config):
        """Initialize Jira backend"""
        super().__init__(config)
        self.command = config.command or "jira"
        self.field_mapping = config.field_mapping or self._get_default_mapping()
        self.verify_installation()
    
    def _get_default_mapping(self) -> Dict[str, str]:
        """Get default Jira field mapping"""
        return {
            "id": "key",
            "uuid": "id",
            "description": "fields.summary",
            "status": "fields.status.name",
            "project": "fields.project.key",
            "priority": "fields.priority.name",
            "tags": "fields.labels",
            "due": "fields.duedate",
            "entry": "fields.created",
            "modified": "fields.updated"
        }
    
    def verify_installation(self) -> bool:
        """Verify that Jira-CLI is installed"""
        try:
            result = subprocess.run(
                [self.command, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise JiraBackendError(f"Jira-CLI is not properly installed or configured")
            return True
        except FileNotFoundError:
            raise JiraBackendError(
                f"Jira-CLI not found: {self.command}\n"
                "Install from: https://github.com/ankitpokhrel/jira-cli"
            )
        except subprocess.TimeoutExpired:
            raise JiraBackendError("Jira-CLI command timed out")
    
    def execute_command(self, command: str) -> List[Task]:
        """
        Execute a jira-cli command and return parsed tasks
        
        Args:
            command: Jira-CLI command (e.g., "jira issue list --plain")
        
        Returns:
            List of Task objects
        """
        # Parse command
        cmd_parts = command.strip().split()
        if not cmd_parts:
            raise JiraBackendError("Empty command")
        
        # If command doesn't start with jira, prepend it
        if cmd_parts[0] != self.command:
            cmd_parts = [self.command] + cmd_parts
        
        # Ensure we get JSON output
        if "--json" not in cmd_parts and "-j" not in cmd_parts:
            cmd_parts.append("--json")
        
        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                raise JiraBackendError(f"Command failed: {error_msg}")
            
            # Parse JSON output
            if not result.stdout.strip():
                return []
            
            jira_data = json.loads(result.stdout)
            return self._parse_jira_issues(jira_data)
            
        except subprocess.TimeoutExpired:
            raise JiraBackendError("Command timed out")
        except json.JSONDecodeError as e:
            raise JiraBackendError(f"Failed to parse Jira data: {e}")
        except Exception as e:
            raise JiraBackendError(f"Unexpected error: {e}")
    
    def _parse_jira_issues(self, jira_data: Any) -> List[Task]:
        """
        Parse Jira issues into Task objects
        
        Args:
            jira_data: Jira API response (can be list or dict with 'issues' key)
        
        Returns:
            List of Task objects
        """
        # Handle different response formats
        if isinstance(jira_data, dict):
            if "issues" in jira_data:
                issues = jira_data["issues"]
            elif "values" in jira_data:
                issues = jira_data["values"]
            else:
                # Single issue
                issues = [jira_data]
        elif isinstance(jira_data, list):
            issues = jira_data
        else:
            return []
        
        tasks = []
        for issue in issues:
            try:
                task = self._convert_issue_to_task(issue)
                if task:
                    tasks.append(task)
            except Exception as e:
                print(f"Warning: Failed to parse Jira issue {issue.get('key', 'unknown')}: {e}")
                continue
        
        return tasks
    
    def _convert_issue_to_task(self, issue: Dict[str, Any]) -> Optional[Task]:
        """
        Convert a Jira issue to a Task object using field mapping
        
        Args:
            issue: Jira issue dictionary
        
        Returns:
            Task object or None
        """
        task_data = {}
        
        # Map fields using configuration
        for task_field, jira_path in self.field_mapping.items():
            value = self.map_field(issue, jira_path)
            
            # Special handling for certain fields
            if task_field == "id" and value:
                # Jira keys like "PROJ-123" - extract number or use key
                task_data["id"] = self._extract_id(value)
            elif task_field == "uuid" and value:
                task_data["uuid"] = str(value)
            elif task_field == "status" and value:
                # Map Jira status to taskwarrior-like status
                task_data["status"] = self._map_status(value)
            elif task_field == "priority" and value:
                # Map Jira priority to single letter (H/M/L)
                task_data["priority"] = self._map_priority(value)
            elif task_field == "tags" and value:
                # Ensure tags is a list
                if isinstance(value, list):
                    task_data["tags"] = value
                else:
                    task_data["tags"] = [str(value)]
            elif task_field in ["due", "entry", "modified"] and value:
                # Parse dates
                task_data[task_field] = self._parse_date(value)
            elif value is not None:
                task_data[task_field] = value
        
        # Set defaults for required fields
        if "uuid" not in task_data:
            task_data["uuid"] = task_data.get("id", "unknown")
        if "description" not in task_data:
            task_data["description"] = "No summary"
        if "status" not in task_data:
            task_data["status"] = "pending"
        if "tags" not in task_data:
            task_data["tags"] = []
        if "depends" not in task_data:
            task_data["depends"] = []
        
        # Calculate urgency (simple version)
        task_data["urgency"] = self._calculate_urgency(task_data)
        
        # Set virtual tags
        task_data["is_active"] = task_data["status"] == "pending"
        task_data["is_blocked"] = False
        task_data["is_blocking"] = False
        
        return Task(**task_data)
    
    def _extract_id(self, key: str) -> int:
        """Extract numeric ID from Jira key like PROJ-123"""
        import re
        match = re.search(r'(\d+)$', str(key))
        if match:
            return int(match.group(1))
        # Fallback: use hash of the key
        return abs(hash(key)) % 10000
    
    def _map_status(self, jira_status: str) -> str:
        """Map Jira status to taskwarrior status"""
        status_lower = str(jira_status).lower()
        
        if any(word in status_lower for word in ["done", "closed", "resolved", "complete"]):
            return "completed"
        elif any(word in status_lower for word in ["progress", "doing", "active"]):
            return "pending"
        elif any(word in status_lower for word in ["wait", "blocked", "hold"]):
            return "waiting"
        else:
            return "pending"
    
    def _map_priority(self, jira_priority: str) -> Optional[str]:
        """Map Jira priority to single letter"""
        priority_lower = str(jira_priority).lower()
        
        if any(word in priority_lower for word in ["highest", "critical", "blocker"]):
            return "H"
        elif any(word in priority_lower for word in ["high"]):
            return "H"
        elif any(word in priority_lower for word in ["medium", "normal"]):
            return "M"
        elif any(word in priority_lower for word in ["low", "minor"]):
            return "L"
        else:
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        try:
            return date_parser.parse(date_str)
        except:
            return None
    
    def _calculate_urgency(self, task_data: Dict[str, Any]) -> float:
        """Calculate urgency score for a task"""
        urgency = 0.0
        
        # Priority boost
        priority = task_data.get("priority")
        if priority == "H":
            urgency += 6.0
        elif priority == "M":
            urgency += 3.9
        elif priority == "L":
            urgency += 1.8
        
        # Due date boost
        if task_data.get("due"):
            try:
                days_until = (task_data["due"] - datetime.now(task_data["due"].tzinfo)).days
                if days_until < 0:
                    urgency += 12.0  # Overdue
                elif days_until <= 7:
                    urgency += 8.0  # Due soon
                elif days_until <= 14:
                    urgency += 4.0
            except:
                pass
        
        # Project presence
        if task_data.get("project"):
            urgency += 1.0
        
        # Tags presence
        if task_data.get("tags"):
            urgency += 1.0
        
        return round(urgency, 1)
    
    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        """
        Get all Jira issues
        
        Args:
            include_completed: If True, include completed/closed issues
        
        Returns:
            List of tasks
        """
        # Jira-CLI command to list issues
        if include_completed:
            return self.execute_command(f"{self.command} issue list --plain")
        else:
            # Exclude done/closed status
            return self.execute_command(f"{self.command} issue list --plain --status='~Done,Closed'")
