"""
Main CLI entry point using Typer
"""
import sys
import typer
from typing import Optional
from pathlib import Path

from rich.console import Console

from . import __version__
from .shell import start_shell
from .backends import create_backend
from .backends.factory import UnsupportedBackendError
from .config import get_config
from .models import GroupBy
from .views.table import TableView
from .views.markdown import MarkdownView
from .views.list import ListView


app = typer.Typer(
    name="tw-cli",
    help="Enhanced Taskwarrior CLI with beautiful views (kanban, table, markdown, list)",
    add_completion=True,
)

console = Console()


@app.command()
def shell(
    backend: Optional[str] = typer.Option(None, "--backend", "-b", help="Backend to use: taskwarrior, jira (overrides config)"),
):
    """
    Start interactive shell mode (like DuckDB CLI)
    
    Examples:
        tw-cli shell --backend taskwarrior
        tw-cli shell -b jira
    """
    try:
        start_shell(backend_override=backend)
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def view(
    mode: str = typer.Argument("kanban", help="View mode: kanban, table, markdown, list"),
    command: Optional[str] = typer.Option(None, "--cmd", "-c", help="Command to execute (task/jira command)"),
    group_by: Optional[str] = typer.Option(None, "--group", "-g", help="Kanban grouping: status, priority, project, tag"),
    backend: Optional[str] = typer.Option(None, "--backend", "-b", help="Backend to use: taskwarrior, jira (overrides config)"),
):
    """
    Execute a command and display in specified view mode
    
    Examples:
        tw-cli view kanban --backend taskwarrior --cmd "task +work"
        tw-cli view table --backend jira
        tw-cli view kanban --group priority --backend taskwarrior
        tw-cli view table -b jira -c "jira issue list --plain --status='~Done'"
    """
    try:
        # Get config
        config = get_config()
        
        # Override backend type if provided via command line
        backend_config = config.backend
        if backend:
            # Create a modified backend config with the runtime override
            backend_config = backend_config.model_copy(update={"type": backend.lower()})
        
        # Create backend based on configuration (or override)
        backend_instance = create_backend(backend_config)
        
        # Default command if none provided
        if not command:
            command = "task" if backend_config.type == "taskwarrior" else f"{backend_config.command} issue list --plain"
        
        # Execute command via backend
        tasks = backend_instance.execute_command(command)
        
        # Render in requested view
        if mode == "kanban":
            group_by_enum = GroupBy(group_by) if group_by else None
            view_obj = TableView(layout="kanban", group_by=group_by_enum, config=config)
            view_obj.render(tasks)
        elif mode == "table":
            view_obj = TableView(config=config)
            view_obj.render(tasks)
        elif mode == "markdown":
            view_obj = MarkdownView(config=config)
            view_obj.render(tasks)
        elif mode == "list":
            view_obj = ListView(config=config)
            view_obj.render(tasks)
        else:
            console.print(f"[red]Unknown view mode: {mode}[/red]")
            console.print("Available modes: kanban, table, markdown, list")
            sys.exit(1)
    
    except UnsupportedBackendError as e:
        console.print(f"[red]Backend error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@app.command()
def version():
    """Show version information"""
    console.print(f"[cyan]tw-cli[/cyan] version [bold]{__version__}[/bold]")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    tw-cli - Enhanced Taskwarrior CLI
    
    Use 'tw-cli shell' to start interactive mode or 'tw-cli view' for one-off views.
    """
    # If no command provided, show help
    if ctx.invoked_subcommand is None:
        console.print("[cyan]tw-cli[/cyan] - Enhanced Taskwarrior CLI\n")
        console.print("Quick start:")
        console.print("  [green]tw-cli shell[/green]          Start interactive shell")
        console.print("  [green]tw-cli view kanban[/green]    View tasks in kanban mode")
        console.print("\nFor full help: [dim]tw-cli --help[/dim]")


if __name__ == "__main__":
    app()
