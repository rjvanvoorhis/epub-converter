"""Value objects for EPUB extraction domain.

Value objects are immutable objects that have no identity beyond their attributes.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class FilePath:
    """Represents an immutable file path."""

    value: Path

    def __post_init__(self) -> None:
        """Validate the file path."""
        if not isinstance(self.value, Path):
            raise ValueError("FilePath value must be a Path instance")

    def exists(self) -> bool:
        """Check if the path exists."""
        return self.value.exists()

    def __str__(self) -> str:
        """Return string representation of the path."""
        return str(self.value)


@dataclass(frozen=True)
class Metadata:
    """Represents immutable EPUB metadata."""

    title: str
    author: Optional[str] = None
    language: Optional[str] = None
    identifier: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate metadata."""
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")


@dataclass(frozen=True)
class ChapterId:
    """Unique identifier for a chapter."""

    value: int

    def __post_init__(self) -> None:
        """Validate chapter ID."""
        if self.value < 0:
            raise ValueError("Chapter ID must be non-negative")
