"""CLI controller - orchestrates command execution.

The controller handles routing commands and managing the CLI interface
without being tied to a specific CLI framework.
"""

from typing import Any

from .commands import Command


class CLIController:
    """Orchestrates CLI command execution and routing."""

    def __init__(self) -> None:
        """Initialize the controller."""
        self._commands: dict[str, Command] = {}

    def register_command(self, command: Command) -> None:
        """Register a command with the controller.

        Args:
            command: The command to register.
        """
        self._commands[command.name] = command

    def execute_command(self, command_name: str, *args: Any, **kwargs: Any) -> str:
        """Execute a registered command.

        Args:
            command_name: The name of the command to execute.
            *args: Positional arguments to pass to the command.
            **kwargs: Named arguments to pass to the command.

        Returns:
            The command output.

        Raises:
            ValueError: If the command is not found.
            RuntimeError: If command execution fails.
        """
        if command_name not in self._commands:
            raise ValueError(f"Unknown command: {command_name}")

        command = self._commands[command_name]
        return command.execute(*args, **kwargs)

    def get_available_commands(self) -> dict[str, str]:
        """Get all available commands with their descriptions.

        Returns:
            Dictionary mapping command names to descriptions.
        """
        return {cmd.name: cmd.description for cmd in self._commands.values()}
