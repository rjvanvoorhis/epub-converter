"""Entities for EPUB extraction domain.

Entities have identity and mutable state over their lifetime.
"""

from dataclasses import dataclass, field
from typing import Optional

from .value_objects import ChapterId, FilePath, Metadata


@dataclass
class Chapter:
    """Represents a chapter in an EPUB file."""

    id: ChapterId
    title: str
    content: str
    order: int

    def is_valid(self) -> bool:
        """Validate chapter integrity."""
        return bool(self.title.strip()) and self.order >= 0

    def get_word_count(self) -> int:
        """Calculate word count for this chapter."""
        return len(self.content.split())


@dataclass
class EPUBFile:
    """Aggregate root for EPUB extraction domain.

    Represents an EPUB file with its metadata and chapters.
    """

    file_path: FilePath
    metadata: Metadata
    chapters: list[Chapter] = field(default_factory=list)

    def add_chapter(self, chapter: Chapter) -> None:
        """Add a chapter to the EPUB file.

        Args:
            chapter: The chapter to add.

        Raises:
            ValueError: If the chapter is invalid.
        """
        if not chapter.is_valid():
            raise ValueError(f"Invalid chapter: {chapter.title}")
        self.chapters.append(chapter)

    def get_total_word_count(self) -> int:
        """Calculate total word count across all chapters."""
        return sum(chapter.get_word_count() for chapter in self.chapters)

    def get_chapter_by_id(self, chapter_id: ChapterId) -> Optional[Chapter]:
        """Retrieve a chapter by ID.

        Args:
            chapter_id: The ID of the chapter to retrieve.

        Returns:
            The chapter if found, None otherwise.
        """
        for chapter in self.chapters:
            if chapter.id == chapter_id:
                return chapter
        return None

    def is_valid(self) -> bool:
        """Validate the entire EPUB file.

        Returns:
            True if the EPUB file is valid, False otherwise.
        """
        if not self.file_path.exists():
            return False
        return all(chapter.is_valid() for chapter in self.chapters)
