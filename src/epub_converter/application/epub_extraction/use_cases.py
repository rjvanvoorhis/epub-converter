"""Use cases for EPUB extraction domain.

Use cases implement application-specific business logic by orchestrating
domain entities and repositories.
"""

from pathlib import Path

from epub_converter.domain.epub_extraction.interfaces import EPUBRepository
from epub_converter.domain.epub_extraction.value_objects import ChapterId, FilePath

from .dtos import (
    ChapterDto,
    ExtractChapterInput,
    ExtractChapterOutput,
    LoadEPUBInput,
    LoadEPUBOutput,
)


class LoadEPUBUseCase:
    """Use case for loading and analyzing an EPUB file."""

    def __init__(self, epub_repository: EPUBRepository) -> None:
        """Initialize the use case with a repository.

        Args:
            epub_repository: The repository for accessing EPUB files.
        """
        self.epub_repository = epub_repository

    def execute(self, input_dto: LoadEPUBInput) -> LoadEPUBOutput:
        """Execute the use case.

        Args:
            input_dto: The input data.

        Returns:
            The loaded EPUB file data as an output DTO.

        Raises:
            FileNotFoundError: If the EPUB file does not exist.
            ValueError: If the file is not a valid EPUB.
        """
        file_path = FilePath(Path(input_dto.file_path))
        epub_file = self.epub_repository.load(file_path)

        chapters = [
            ChapterDto(
                id=chapter.id.value,
                title=chapter.title,
                order=chapter.order,
                word_count=chapter.get_word_count(),
            )
            for chapter in epub_file.chapters
        ]

        return LoadEPUBOutput(
            title=epub_file.metadata.title,
            author=epub_file.metadata.author,
            language=epub_file.metadata.language,
            identifier=epub_file.metadata.identifier,
            total_chapters=len(epub_file.chapters),
            total_word_count=epub_file.get_total_word_count(),
            chapters=chapters,
        )


class ExtractChapterUseCase:
    """Use case for extracting a specific chapter from an EPUB file."""

    def __init__(self, epub_repository: EPUBRepository) -> None:
        """Initialize the use case with a repository.

        Args:
            epub_repository: The repository for accessing EPUB files.
        """
        self.epub_repository = epub_repository

    def execute(self, input_dto: ExtractChapterInput) -> ExtractChapterOutput:
        """Execute the use case.

        Args:
            input_dto: The input data.

        Returns:
            The extracted chapter data as an output DTO.

        Raises:
            FileNotFoundError: If the EPUB file does not exist.
            ValueError: If the chapter is not found.
        """
        file_path = FilePath(Path(input_dto.file_path))
        epub_file = self.epub_repository.load(file_path)

        chapter_id = ChapterId(input_dto.chapter_id)
        chapter = epub_file.get_chapter_by_id(chapter_id)

        if chapter is None:
            raise ValueError(f"Chapter with ID {input_dto.chapter_id} not found")

        return ExtractChapterOutput(
            chapter_id=chapter.id.value,
            title=chapter.title,
            content=chapter.content,
            word_count=chapter.get_word_count(),
        )
