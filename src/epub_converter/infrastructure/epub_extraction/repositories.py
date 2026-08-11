"""Concrete repository implementations for EPUB extraction.

These implementations handle actual file I/O and parsing logic.
"""

from pathlib import Path

from epub_converter.domain.epub_extraction.entities import Chapter, EPUBFile
from epub_converter.domain.epub_extraction.interfaces import EPUBRepository
from epub_converter.domain.epub_extraction.value_objects import (
    ChapterId,
    FilePath,
    Metadata,
)


class EbookLibEPUBRepository(EPUBRepository):
    """Concrete repository implementation using the ebooklib library."""

    def load(self, file_path: FilePath) -> EPUBFile:
        """Load an EPUB file using ebooklib.

        Args:
            file_path: Path to the EPUB file.

        Returns:
            The loaded EPUB file as an aggregate root.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a valid EPUB.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"EPUB file not found: {file_path}")

        try:
            import ebooklib
            from ebooklib import epub
        except ImportError:
            raise RuntimeError(
                "ebooklib is required. Install it with: pip install ebooklib"
            )

        try:
            book = epub.read_epub(str(file_path.value))
        except Exception as e:
            raise ValueError(f"Failed to read EPUB file: {e}")

        # Extract metadata
        title = book.get_metadata("DC", "title")
        title_str = title[0][0] if title else "Unknown"

        author = book.get_metadata("DC", "creator")
        author_str = author[0][0] if author else None

        language = book.get_metadata("DC", "language")
        language_str = language[0][0] if language else None

        identifier = book.get_metadata("DC", "identifier")
        identifier_str = identifier[0][0] if identifier else None

        metadata = Metadata(
            title=title_str,
            author=author_str,
            language=language_str,
            identifier=identifier_str,
        )

        # Create aggregate root
        epub_file = EPUBFile(file_path=file_path, metadata=metadata)

        # Extract chapters
        chapter_order = 0
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapter_id = ChapterId(chapter_order)
                chapter_title = item.get_name() or f"Chapter {chapter_order}"
                chapter_content = item.get_body_content().decode(
                    "utf-8", errors="ignore"
                )

                chapter = Chapter(
                    id=chapter_id,
                    title=chapter_title,
                    content=chapter_content,
                    order=chapter_order,
                )
                epub_file.add_chapter(chapter)
                chapter_order += 1

        return epub_file

    def save(self, epub_file: EPUBFile, file_path: FilePath) -> None:
        """Save an EPUB file to disk.

        Note: This is a stub implementation. Full EPUB writing would require
        more complex logic to properly structure EPUB files.

        Args:
            epub_file: The EPUB file to save.
            file_path: Path where to save the EPUB file.
        """
        raise NotImplementedError(
            "EPUB writing is not yet implemented. "
            "Current implementation supports reading EPUB files."
        )
