"""Data Transfer Objects (DTOs) for audiobook conversion application layer.

DTOs are used to transfer data between layers without exposing domain entities.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ConvertEPUBToAudiobookInput:
    """Input DTO for converting EPUB to audiobook."""

    epub_file_path: Path
    output_file_path: Path
    voice_profile_id: str
    language: str = "en"
    chunk_size: int = 45000

    def __post_init__(self) -> None:
        """Validate input."""
        if not self.epub_file_path.exists():
            raise ValueError(f"EPUB file not found: {self.epub_file_path}")
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")


@dataclass
class ConvertEPUBToAudiobookOutput:
    """Output DTO for EPUB to audiobook conversion."""

    output_file_path: Path
    total_duration_seconds: float
    chapter_count: int
    voice_profile_id: str

    def __post_init__(self) -> None:
        """Validate output."""
        if self.total_duration_seconds <= 0:
            raise ValueError("total_duration_seconds must be positive")
        if self.chapter_count <= 0:
            raise ValueError("chapter_count must be positive")


@dataclass
class ListVoiceProfilesOutput:
    """Output DTO for listing available voice profiles."""

    profiles: list[dict]

    @property
    def profile_count(self) -> int:
        """Get the number of available profiles."""
        return len(self.profiles)
