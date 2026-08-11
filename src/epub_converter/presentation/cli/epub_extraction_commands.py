"""EPUB extraction CLI commands."""

from pathlib import Path
from typing import Any

from epub_converter.application.epub_extraction.dtos import (
    ExtractChapterInput,
    LoadEPUBInput,
)
from epub_converter.application.epub_extraction.use_cases import (
    ExtractChapterUseCase,
    LoadEPUBUseCase,
)

from .commands import Command


class LoadEPUBCommand(Command):
    """Command to load and display EPUB file information."""

    def __init__(self, use_case: LoadEPUBUseCase) -> None:
        """Initialize the command with its use case.

        Args:
            use_case: The LoadEPUBUseCase instance.
        """
        self._use_case = use_case

    @property
    def name(self) -> str:
        """Return the command name."""
        return "load-epub"

    @property
    def description(self) -> str:
        """Return the command description."""
        return "Load and display information about an EPUB file"

    def execute(self, *args: Any, **kwargs: Any) -> str:
        """Load an EPUB file and display its information.

        Args:
            *args: Should contain the file path as the first argument.
            **kwargs: Alternative way to pass file_path.

        Returns:
            Formatted output with EPUB information.

        Raises:
            ValueError: If file path is not provided or invalid.
            FileNotFoundError: If the EPUB file does not exist.
        """
        if not args and "file_path" not in kwargs:
            raise ValueError("file_path argument is required")

        file_path = args[0] if args else kwargs.get("file_path")

        if isinstance(file_path, str):
            file_path = Path(file_path)

        input_dto = LoadEPUBInput(file_path=file_path)
        output_dto = self._use_case.execute(input_dto)

        # Format output
        lines = [
            f"EPUB: {output_dto.title}",
            f"Author: {output_dto.author or 'Unknown'}",
            f"Language: {output_dto.language or 'Unknown'}",
            f"ID: {output_dto.identifier or 'Unknown'}",
            f"Chapters: {output_dto.total_chapters}",
            f"Total Words: {output_dto.total_word_count}",
            "\nChapters:",
        ]

        for chapter in output_dto.chapters:
            lines.append(
                f"  [{chapter.id}] {chapter.title} (order: {chapter.order}, words: {chapter.word_count})"
            )

        return "\n".join(lines)


class ExtractChapterCommand(Command):
    """Command to extract a specific chapter from an EPUB file."""

    def __init__(self, use_case: ExtractChapterUseCase) -> None:
        """Initialize the command with its use case.

        Args:
            use_case: The ExtractChapterUseCase instance.
        """
        self._use_case = use_case

    @property
    def name(self) -> str:
        """Return the command name."""
        return "extract-chapter"

    @property
    def description(self) -> str:
        """Return the command description."""
        return "Extract a specific chapter from an EPUB file"

    def execute(self, *args: Any, **kwargs: Any) -> str:
        """Extract a chapter from an EPUB file.

        Args:
            *args: Should contain file_path and chapter_id.
            **kwargs: Alternative way to pass file_path and chapter_id.

        Returns:
            Formatted output with the extracted chapter content.

        Raises:
            ValueError: If required arguments are missing or invalid.
            FileNotFoundError: If the EPUB file does not exist.
        """
        if not args or len(args) < 2:
            if "file_path" not in kwargs or "chapter_id" not in kwargs:
                raise ValueError("file_path and chapter_id arguments are required")
            file_path = kwargs.get("file_path")
            chapter_id = kwargs.get("chapter_id")
        else:
            file_path = args[0]
            chapter_id = args[1]

        if isinstance(file_path, str):
            file_path = Path(file_path)

        if isinstance(chapter_id, str):
            chapter_id = int(chapter_id)

        input_dto = ExtractChapterInput(file_path=file_path, chapter_id=chapter_id)
        output_dto = self._use_case.execute(input_dto)

        # Format output
        lines = [
            f"Chapter {output_dto.chapter_id}: {output_dto.title}",
            f"Word Count: {output_dto.word_count}",
            "\nContent:",
            "-" * 80,
            output_dto.content,
            "-" * 80,
        ]

        return "\n".join(lines)
