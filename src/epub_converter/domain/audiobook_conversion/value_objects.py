"""Value objects for audiobook conversion domain.

Value objects are immutable objects that have no identity beyond their attributes.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioProfileId:
    """Unique identifier for an audio profile."""

    value: str


@dataclass(frozen=True)
class AudioProfile:
    """Represents a voice profile available from VoiceBox."""

    id: AudioProfileId
    name: str
    language: str
    description: str


@dataclass(frozen=True)
class TextChunk:
    """Represents a chunk of text to be converted to audio.

    Chunks are created by splitting longer texts to stay within
    API limits (typically 45K characters).
    """

    sequence: int
    text: str
    start_char: int
    end_char: int

    def __post_init__(self) -> None:
        """Validate chunk properties."""
        if self.sequence < 0:
            raise ValueError("Sequence must be non-negative")
        if not self.text.strip():
            raise ValueError("Text chunk cannot be empty")
        if self.start_char >= self.end_char:
            raise ValueError("start_char must be less than end_char")

    def character_count(self) -> int:
        """Get the character count of this chunk."""
        return len(self.text)


@dataclass(frozen=True)
class AudioFile:
    """Represents an audio file generated from a text chunk."""

    chunk_sequence: int
    file_path: Path
    duration_seconds: float

    def __post_init__(self) -> None:
        """Validate audio file properties."""
        if self.chunk_sequence < 0:
            raise ValueError("chunk_sequence must be non-negative")
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
