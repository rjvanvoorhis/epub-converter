"""Data Transfer Objects (DTOs) for EPUB extraction use cases.

DTOs represent input and output contracts between layers.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LoadEPUBInput:
    """Input DTO for loading an EPUB file."""

    file_path: Path


@dataclass
class ChapterDto:
    """DTO representing a chapter."""

    id: int
    title: str
    order: int
    word_count: int


@dataclass
class LoadEPUBOutput:
    """Output DTO for loading an EPUB file."""

    title: str
    author: Optional[str]
    language: Optional[str]
    identifier: Optional[str]
    total_chapters: int
    total_word_count: int
    chapters: list[ChapterDto]


@dataclass
class ExtractChapterInput:
    """Input DTO for extracting a specific chapter."""

    file_path: Path
    chapter_id: int


@dataclass
class ExtractChapterOutput:
    """Output DTO for extracted chapter."""

    chapter_id: int
    title: str
    content: str
    word_count: int
