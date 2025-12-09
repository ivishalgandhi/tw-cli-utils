"""
Configuration management for tw-cli
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from pydantic import BaseModel, Field
from .models import GroupBy


class KanbanColumn(BaseModel):
    """Custom kanban column definition"""
    name: str
    filter: str
    color: str = "white"


class KanbanConfig(BaseModel):
    """Kanban view configuration"""
    group_by: GroupBy = GroupBy.STATUS
    tag_prefix: Optional[str] = None
    show_completed: bool = True
    completed_days: int = 7
    max_tasks_per_column: int = 20
    column_min_width: int = 40
    columns: List[KanbanColumn] = Field(default_factory=list)


class TableConfig(BaseModel):
    """Table view configuration"""
    columns: List[str] = Field(
        default_factory=lambda: ["id", "description", "project", "tags", "due", "priority", "urgency"]
    )
    default_sort: str = "urgency"
    sort_order: str = "desc"
    page_size: int = 50
    show_grid: bool = True


class MarkdownConfig(BaseModel):
    """Markdown view configuration"""
    group_by_project: bool = True
    include_metadata: bool = True
    use_checkboxes: bool = True


class ListConfig(BaseModel):
    """List view configuration"""
    truncate_description: bool = False
    max_description_length: int = 80
    show_ids: bool = True


class ColorConfig(BaseModel):
    """Color scheme configuration"""
    # Priority colors
    priority_high: str = "red"
    priority_medium: str = "yellow"
    priority_low: str = "blue"
    priority_none: str = "white"
    
    # Status colors
    status_active: str = "green bold"
    status_pending: str = "cyan"
    status_waiting: str = "yellow"
    status_completed: str = "dim"
    status_blocked: str = "red"
    
    # Urgency thresholds and colors
    urgency_critical: float = 15.0
    urgency_high: float = 10.0
    urgency_medium: float = 5.0
    urgency_critical_color: str = "red bold"
    urgency_high_color: str = "red"
    urgency_medium_color: str = "yellow"
    urgency_low_color: str = "white"


class ShellConfig(BaseModel):
    """Shell configuration"""
    enable_history: bool = True
    history_file: str = "~/.config/tw-cli/history"
    enable_autocomplete: bool = True
    show_welcome: bool = True


class Config(BaseModel):
    """Main configuration"""
    default_view: str = "kanban"
    kanban: KanbanConfig = Field(default_factory=KanbanConfig)
    table: TableConfig = Field(default_factory=TableConfig)
    markdown: MarkdownConfig = Field(default_factory=MarkdownConfig)
    list: ListConfig = Field(default_factory=ListConfig)
    colors: ColorConfig = Field(default_factory=ColorConfig)
    shell: ShellConfig = Field(default_factory=ShellConfig)


def get_config_path() -> Path:
    """Get the configuration file path"""
    config_dir = Path.home() / ".config" / "tw-cli"
    return config_dir / "config.toml"


def load_config() -> Config:
    """
    Load configuration from file, or return defaults
    
    Returns:
        Config object
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        # Return default configuration
        return Config()
    
    try:
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)
        
        return Config(**config_data)
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}")
        print("Using default configuration")
        return Config()


def save_config(config: Config):
    """
    Save configuration to file
    
    Args:
        config: Config object to save
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict and write as TOML
    # Note: This is a basic implementation - for production you'd want tomli_w
    print(f"Config would be saved to: {config_path}")
    print("Note: Config saving not yet implemented - edit config.toml manually")


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance (singleton)"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
