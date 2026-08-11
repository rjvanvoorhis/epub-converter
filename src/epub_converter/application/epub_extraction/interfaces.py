"""Interfaces (protocols) for EPUB extraction application layer.

These interfaces define contracts for infrastructure services that implement
application-specific logic.
"""

from typing import Protocol

from .dtos import (
    ExtractChapterInput,
    ExtractChapterOutput,
    LoadEPUBInput,
    LoadEPUBOutput,
)


class ILoadEPUBUseCase(Protocol):
    """Interface for the load EPUB use case."""

    def execute(self, input_dto: LoadEPUBInput) -> LoadEPUBOutput:
        """Load and analyze an EPUB file."""
        ...


class IExtractChapterUseCase(Protocol):
    """Interface for the extract chapter use case."""

    def execute(self, input_dto: ExtractChapterInput) -> ExtractChapterOutput:
        """Extract a specific chapter from an EPUB file."""
        ...
