"""Command definitions for CLI.

Commands are framework-agnostic and define how to interact with use cases
and present results to the user.
"""

from typing import Any, Protocol


class Command(Protocol):
    """Interface for CLI commands.

    Commands are presentation-layer abstractions that invoke use cases
    and format output without depending on a specific CLI framework.
    """

    @property
    def name(self) -> str:
        """Return the command name."""
        ...

    @property
    def description(self) -> str:
        """Return the command description."""
        ...

    def execute(self, *args: Any, **kwargs: Any) -> str:
        """Execute the command.

        Args:
            *args: Positional arguments passed from CLI.
            **kwargs: Named arguments passed from CLI.

        Returns:
            Formatted output string for the user.

        Raises:
            ValueError: If arguments are invalid.
            RuntimeError: If execution fails.
        """
        ...
