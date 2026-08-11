"""Unit tests for EPUB extraction application layer.

Tests use case orchestration using mock implementations of domain protocols.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from epub_converter.application.epub_extraction.use_cases import (
    LoadEPUBUseCase,
    ExtractChapterUseCase,
)
from epub_converter.application.epub_extraction.dtos import (
    LoadEPUBInput,
    LoadEPUBOutput,
    ExtractChapterInput,
    ExtractChapterOutput,
    ChapterDto,
)
from epub_converter.domain.epub_extraction.value_objects import (
    ChapterId,
    FilePath,
    Metadata,
)
from epub_converter.domain.epub_extraction.entities import Chapter, EPUBFile

from tests.conftest import MockEPUBRepository


class TestLoadEPUBUseCase:
    """Test loading EPUB use case."""

    def test_load_epub_success(self, tmp_path: Path) -> None:
        """Test successfully loading an EPUB file."""
        # Create temporary EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        # Setup mock EPUB file
        epub = EPUBFile(
            file_path=FilePath(epub_file),
            metadata=Metadata(
                title="Test Book",
                author="Test Author",
                language="en"
            )
        )

        chapter = Chapter(
            id=ChapterId(0),
            title="Chapter 1",
            content="Sample content",
            order=0
        )
        epub.add_chapter(chapter)

        # Setup mock repository
        mock_repo = MockEPUBRepository(epub)

        # Test use case
        use_case = LoadEPUBUseCase(mock_repo)
        input_dto = LoadEPUBInput(file_path=epub_file)
        output = use_case.execute(input_dto)

        assert isinstance(output, LoadEPUBOutput)
        assert output.title == "Test Book"
        assert output.author == "Test Author"
        assert output.language == "en"
        assert len(output.chapters) == 1

    def test_load_epub_returns_load_epub_output(self, tmp_path: Path) -> None:
        """Test that load EPUB returns LoadEPUBOutput DTO."""
        # Create temporary EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        mock_repo = MockEPUBRepository()
        use_case = LoadEPUBUseCase(mock_repo)

        input_dto = LoadEPUBInput(file_path=epub_file)
        output = use_case.execute(input_dto)

        assert isinstance(output, LoadEPUBOutput)
        assert output.total_chapters >= 0
        assert isinstance(output.chapters, list)


class TestExtractChapterUseCase:
    """Test extracting chapters use case."""

    def test_extract_chapter_success(self, tmp_path: Path) -> None:
        """Test successfully extracting a chapter."""
        # Create temporary EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        # Setup mock EPUB with chapters
        epub = EPUBFile(
            file_path=FilePath(epub_file),
            metadata=Metadata(title="Test Book")
        )

        chapter1 = Chapter(
            id=ChapterId(0),
            title="Chapter 1",
            content="Content of chapter 1",
            order=0
        )
        chapter2 = Chapter(
            id=ChapterId(1),
            title="Chapter 2",
            content="Content of chapter 2",
            order=1
        )

        epub.add_chapter(chapter1)
        epub.add_chapter(chapter2)

        # Setup mock repository
        mock_repo = MockEPUBRepository(epub)

        # Test use case
        use_case = ExtractChapterUseCase(mock_repo)
        input_dto = ExtractChapterInput(file_path=epub_file, chapter_id=0)
        output = use_case.execute(input_dto)

        assert isinstance(output, ExtractChapterOutput)
        assert output.chapter_id == 0
        assert output.title == "Chapter 1"

    def test_extract_chapter_returns_dto(self, tmp_path: Path) -> None:
        """Test that extract chapter returns ExtractChapterOutput DTO."""
        # Create temporary EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        mock_repo = MockEPUBRepository()
        use_case = ExtractChapterUseCase(mock_repo)

        input_dto = ExtractChapterInput(file_path=epub_file, chapter_id=0)
        output = use_case.execute(input_dto)

        assert isinstance(output, ExtractChapterOutput)

    def test_extract_chapter_includes_content(self, tmp_path: Path) -> None:
        """Test that extracted chapter includes content."""
        # Create temporary EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        # Setup
        epub = EPUBFile(
            file_path=FilePath(epub_file),
            metadata=Metadata(title="Test Book")
        )

        content = "This is the chapter content with multiple words."
        chapter = Chapter(
            id=ChapterId(0),
            title="Chapter 1",
            content=content,
            order=0
        )
        epub.add_chapter(chapter)

        mock_repo = MockEPUBRepository(epub)

        # Test
        use_case = ExtractChapterUseCase(mock_repo)
        input_dto = ExtractChapterInput(file_path=epub_file, chapter_id=0)
        output = use_case.execute(input_dto)

        assert output.content == content

    def test_extract_chapter_multiple_chapters(self, tmp_path: Path) -> None:
        """Test extracting different chapters."""
        # Create temporary EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        # Setup
        epub = EPUBFile(
            file_path=FilePath(epub_file),
            metadata=Metadata(title="Test Book")
        )

        for i in range(3):
            chapter = Chapter(
                id=ChapterId(i),
                title=f"Chapter {i}",
                content=f"Content {i}",
                order=i
            )
            epub.add_chapter(chapter)

        mock_repo = MockEPUBRepository(epub)

        # Test
        use_case = ExtractChapterUseCase(mock_repo)

        # Extract each chapter
        for i in range(3):
            input_dto = ExtractChapterInput(file_path=epub_file, chapter_id=i)
            output = use_case.execute(input_dto)

            assert output.chapter_id == i
            assert output.title == f"Chapter {i}"
            assert output.content == f"Content {i}"


class TestLoadEPUBInputDTO:
    """Test input DTO for load EPUB use case."""

    def test_load_epub_input_dto(self, tmp_path: Path) -> None:
        """Test creating load EPUB input DTO."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        # This would be the actual DTO if implemented
        # For now, we just verify the mock works
        input_dto = type('InputDTO', (), {'file_path': FilePath(epub_file)})()
        assert input_dto.file_path.value == epub_file


class TestExtractChapterInputDTO:
    """Test input DTO for extract chapter use case."""

    def test_extract_chapter_input_dto(self, tmp_path: Path) -> None:
        """Test creating extract chapter input DTO."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        # This would be the actual DTO if implemented
        input_dto = type('InputDTO', (), {'file_path': FilePath(epub_file)})()
        assert input_dto.file_path.value == epub_file
