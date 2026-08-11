"""CLI response formatting utilities."""

from dataclasses import dataclass
from enum import Enum


class ResponseStatus(Enum):
    """Status of a CLI response."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class FormattedResponse:
    """Represents a formatted CLI response."""

    status: ResponseStatus
    message: str
    data: str | None = None

    def render(self) -> str:
        """Render the response for display.

        Returns:
            Formatted response string.
        """
        output_lines = [f"[{self.status.value.upper()}] {self.message}"]
        if self.data:
            output_lines.append("\n" + self.data)
        return "\n".join(output_lines)
