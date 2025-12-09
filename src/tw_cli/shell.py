"""
Interactive shell mode - similar to DuckDB CLI
"""
import sys
import readline
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table as RichTable

from .taskwarrior import TaskWarriorClient, TaskWarriorError
from .config import get_config
from .models import GroupBy
from .views.table import TableView
from .views.markdown import MarkdownView
from .views.list import ListView


class InteractiveShell:
    """Interactive shell for tw-cli"""
    
    def __init__(self):
        self.console = Console()
        self.config = get_config()
        self.client = TaskWarriorClient()
        self.current_view = self.config.default_view
        self.current_group_by = self.config.kanban.group_by
        self.running = True
        
        # Setup readline for history
        if self.config.shell.enable_history:
            self._setup_history()
    
    def _setup_history(self):
        """Setup command history"""
        try:
            from pathlib import Path
            history_file = Path(self.config.shell.history_file).expanduser()
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load history
            if history_file.exists():
                readline.read_history_file(str(history_file))
            
            # Save on exit
            import atexit
            atexit.register(readline.write_history_file, str(history_file))
        except Exception as e:
            # Silently fail if history setup fails
            pass
    
    def show_welcome(self):
        """Show welcome message"""
        if not self.config.shell.show_welcome:
            return
        
        welcome = """
# 🎯 tw-cli Interactive Shell

**View your Taskwarrior tasks with beautiful visualizations**

### Commands

• `.mode <view>` — Switch view (kanban, table, markdown, list)
• `.mode kanban:<group>` — Set grouping (status, priority, project, tag)
• `.help` — Show this help message
• `.config` — Show current configuration
• `.exit` / `.quit` / `.q` — Exit shell

### Tips

Type any Taskwarrior command to see results in current view mode.
Example: `task +work`, `task project:home status:pending`

**Current mode:** `{mode}`
        """.format(mode=self.current_view)
        
        self.console.print(Panel(
            Markdown(welcome.strip()), 
            border_style="bold cyan",
            padding=(1, 2)
        ))
        self.console.print()
    
    def run(self):
        """Run the interactive shell"""
        self.show_welcome()
        
        while self.running:
            try:
                # Get input with styled prompt
                prompt_text = f"\n[bold cyan]tw-cli[/bold cyan] [dim]({self.current_view})[/dim] › "
                self.console.print(prompt_text, end="")
                line = input().strip()
                
                if not line:
                    continue
                
                # Handle command
                self.handle_command(line)
            
            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Interrupted.[/yellow] [dim]Use .exit or .quit to exit cleanly.[/dim]")
                continue
            except EOFError:
                self.console.print("\n[yellow]Goodbye![/yellow]")
                break
    
    def handle_command(self, line: str):
        """Handle a command line"""
        # Check if it's a dot command
        if line.startswith('.'):
            self.handle_dot_command(line)
        else:
            # It's a taskwarrior command
            self.execute_taskwarrior_command(line)
    
    def handle_dot_command(self, line: str):
        """Handle dot commands"""
        parts = line.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command in ['.exit', '.quit', '.q']:
            self.console.print("[yellow]Goodbye![/yellow]")
            self.running = False
        
        elif command == '.help':
            self.show_welcome()
        
        elif command == '.mode':
            if not args:
                self.console.print(f"[yellow]Current mode: {self.current_view}[/yellow]")
                self.console.print("Available modes: kanban, table, markdown, list")
                self.console.print("Kanban grouping: kanban:status, kanban:priority, kanban:project, kanban:tag")
            else:
                self.switch_mode(args)
        
        elif command == '.config':
            self.show_config()
        
        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            self.console.print("Type .help for available commands")
    
    def switch_mode(self, mode: str):
        """Switch view mode"""
        # Check for kanban grouping
        if ':' in mode:
            view_mode, group = mode.split(':', 1)
            if view_mode == 'kanban':
                try:
                    self.current_group_by = GroupBy(group)
                    self.current_view = 'kanban'
                    self.console.print(f"[green]✓[/green] Switched to [bold cyan]kanban[/bold cyan] view, grouped by [bold]{group}[/bold]")
                except ValueError:
                    self.console.print(f"[red]✗[/red] Invalid grouping: [bold]{group}[/bold]")
                    self.console.print("[dim]Available groupings:[/dim] status, priority, project, tag")
            else:
                self.console.print(f"[red]✗[/red] Grouping only supported for kanban mode")
        else:
            if mode in ['kanban', 'table', 'markdown', 'list']:
                self.current_view = mode
                icon = {"kanban": "📊", "table": "📋", "markdown": "📝", "list": "📃"}.get(mode, "")
                self.console.print(f"[green]✓[/green] {icon} Switched to [bold cyan]{mode}[/bold cyan] view")
            else:
                self.console.print(f"[red]✗[/red] Unknown mode: [bold]{mode}[/bold]")
                self.console.print("[dim]Available modes:[/dim] kanban, table, markdown, list")
    
    def show_config(self):
        """Show current configuration"""
        from rich.table import Table as RichTable
        
        config_table = RichTable(title="Current Configuration", title_style="bold cyan", box=None)
        config_table.add_column("Setting", style="bold")
        config_table.add_column("Value", style="cyan")
        
        config_table.add_row("View Mode", self.current_view)
        if self.current_view == 'kanban':
            config_table.add_row("Kanban Grouping", self.current_group_by.value)
        config_table.add_row("Config File", "~/.config/tw-cli/config.toml")
        
        self.console.print()
        self.console.print(config_table)
        self.console.print()
    
    def execute_taskwarrior_command(self, command: str):
        """Execute a taskwarrior command and render results"""
        try:
            # Execute command
            tasks = self.client.execute_command(command)
            
            # Render in current view
            if self.current_view == 'kanban':
                view = TableView(layout="kanban", group_by=self.current_group_by, config=self.config)
                view.render(tasks)
            elif self.current_view == 'table':
                view = TableView(config=self.config)
                view.render(tasks)
            elif self.current_view == 'markdown':
                view = MarkdownView(config=self.config)
                view.render(tasks)
            elif self.current_view == 'list':
                view = ListView(config=self.config)
                view.render(tasks)
        
        except TaskWarriorError as e:
            self.console.print(f"\n[red]✗ Taskwarrior Error:[/red] {e}\n")
        except Exception as e:
            self.console.print(f"\n[red]✗ Unexpected Error:[/red] {e}\n")
            self.console.print("[dim]Run with --debug for full traceback[/dim]\n")


def start_shell():
    """Start the interactive shell"""
    shell = InteractiveShell()
    shell.run()
