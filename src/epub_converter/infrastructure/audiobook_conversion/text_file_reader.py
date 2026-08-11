"""Service for reading chapter text files from a directory."""

from pathlib import Path
from typing import NamedTuple


class TextFileChapter(NamedTuple):
    """Represents a chapter read from a text file."""

    order: int
    title: str
    content: str
    file_path: Path


class TextFileReaderService:
    """Service for reading chapter text files from a directory."""

    def read_chapters(self, text_directory: Path) -> list[TextFileChapter]:
        """Read all text files from a directory as chapters.

        Files are sorted alphabetically. Each file becomes a chapter
        with the filename (minus extension) as the title.

        Args:
            text_directory: Directory containing .txt files

        Returns:
            List of chapters sorted by filename
        """
        chapters = []

        # Get all .txt files and sort them
        txt_files = sorted(text_directory.glob("*.txt"))

        for order, file_path in enumerate(txt_files):
            # Read the file content
            content = file_path.read_text(encoding="utf-8")

            # Use filename (without extension) as title
            title = file_path.stem

            chapters.append(
                TextFileChapter(
                    order=order, title=title, content=content, file_path=file_path
                )
            )

        return chapters

    def get_total_word_count(self, chapters: list[TextFileChapter]) -> int:
        """Calculate total word count across all chapters.

        Args:
            chapters: List of chapters

        Returns:
            Total word count
        """
        total = 0
        for chapter in chapters:
            # Simple word count: split by whitespace
            total += len(chapter.content.split())
        return total
