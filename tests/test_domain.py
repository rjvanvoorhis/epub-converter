"""Unit tests for EPUB converter domain layer.

Tests the domain entities and value objects without any external dependencies.
"""

import pytest
from pathlib import Path

from epub_converter.domain.audiobook_conversion.value_objects import (
    AudioFile,
    AudioProfile,
    AudioProfileId,
    TextChunk,
)
from epub_converter.domain.audiobook_conversion.entities import (
    ChapterAudiobook,
    Audiobook,
)
from epub_converter.domain.epub_extraction.value_objects import (
    FilePath,
    Metadata,
    ChapterId,
)
from epub_converter.domain.epub_extraction.entities import Chapter, EPUBFile


class TestAudioProfileId:
    """Test AudioProfileId value object."""

    def test_create_valid_profile_id(self) -> None:
        """Test creating a valid audio profile ID."""
        profile_id = AudioProfileId("voice_123")
        assert profile_id.value == "voice_123"

    def test_profile_id_immutable(self) -> None:
        """Test that profile ID is immutable."""
        profile_id = AudioProfileId("voice_123")
        with pytest.raises(AttributeError):
            profile_id.value = "voice_456"  # type: ignore

    def test_profile_id_equality(self) -> None:
        """Test that profile IDs with same value are equal."""
        id1 = AudioProfileId("voice_123")
        id2 = AudioProfileId("voice_123")
        assert id1 == id2

    def test_profile_id_inequality(self) -> None:
        """Test that profile IDs with different values are not equal."""
        id1 = AudioProfileId("voice_123")
        id2 = AudioProfileId("voice_456")
        assert id1 != id2


class TestAudioProfile:
    """Test AudioProfile value object."""

    def test_create_audio_profile(self) -> None:
        """Test creating an audio profile."""
        profile_id = AudioProfileId("voice_123")
        profile = AudioProfile(
            id=profile_id,
            name="Deep Voice",
            language="en",
            description="A deep male voice"
        )
        assert profile.id == profile_id
        assert profile.name == "Deep Voice"
        assert profile.language == "en"

    def test_audio_profile_immutable(self) -> None:
        """Test that audio profile is immutable."""
        profile = AudioProfile(
            id=AudioProfileId("voice_123"),
            name="Deep Voice",
            language="en",
            description="A deep male voice"
        )
        with pytest.raises(AttributeError):
            profile.name = "Changed"  # type: ignore


class TestTextChunk:
    """Test TextChunk value object."""

    def test_create_valid_text_chunk(self) -> None:
        """Test creating a valid text chunk."""
        chunk = TextChunk(
            sequence=0,
            text="This is some text content.",
            start_char=0,
            end_char=26
        )
        assert chunk.sequence == 0
        assert chunk.character_count() == 26

    def test_text_chunk_negative_sequence_raises_error(self) -> None:
        """Test that negative sequence raises error."""
        with pytest.raises(ValueError, match="Sequence must be non-negative"):
            TextChunk(
                sequence=-1,
                text="Content",
                start_char=0,
                end_char=7
            )

    def test_text_chunk_empty_text_raises_error(self) -> None:
        """Test that empty text raises error."""
        with pytest.raises(ValueError, match="Text chunk cannot be empty"):
            TextChunk(
                sequence=0,
                text="   ",
                start_char=0,
                end_char=3
            )

    def test_text_chunk_invalid_range_raises_error(self) -> None:
        """Test that invalid char range raises error."""
        with pytest.raises(ValueError, match="start_char must be less than end_char"):
            TextChunk(
                sequence=0,
                text="Content",
                start_char=10,
                end_char=5
            )

    def test_text_chunk_immutable(self) -> None:
        """Test that text chunk is immutable."""
        chunk = TextChunk(
            sequence=0,
            text="Content",
            start_char=0,
            end_char=7
        )
        with pytest.raises(AttributeError):
            chunk.text = "Changed"  # type: ignore


class TestAudioFile:
    """Test AudioFile value object."""

    def test_create_valid_audio_file(self) -> None:
        """Test creating a valid audio file."""
        temp_path = Path("/tmp/audio.mp3")
        audio_file = AudioFile(
            chunk_sequence=0,
            file_path=temp_path,
            duration_seconds=120.5
        )
        assert audio_file.chunk_sequence == 0
        assert audio_file.duration_seconds == 120.5

    def test_audio_file_negative_sequence_raises_error(self) -> None:
        """Test that negative sequence raises error."""
        with pytest.raises(ValueError, match="chunk_sequence must be non-negative"):
            AudioFile(
                chunk_sequence=-1,
                file_path=Path("/tmp/audio.mp3"),
                duration_seconds=120.0
            )

    def test_audio_file_non_positive_duration_raises_error(self) -> None:
        """Test that non-positive duration raises error."""
        with pytest.raises(ValueError, match="duration_seconds must be positive"):
            AudioFile(
                chunk_sequence=0,
                file_path=Path("/tmp/audio.mp3"),
                duration_seconds=0
            )

    def test_audio_file_immutable(self) -> None:
        """Test that audio file is immutable."""
        audio_file = AudioFile(
            chunk_sequence=0,
            file_path=Path("/tmp/audio.mp3"),
            duration_seconds=120.0
        )
        with pytest.raises(AttributeError):
            audio_file.duration_seconds = 200.0  # type: ignore


class TestChapterAudiobook:
    """Test ChapterAudiobook entity."""

    def test_create_chapter_audiobook(self) -> None:
        """Test creating a chapter audiobook."""
        chapter_audio = ChapterAudiobook(
            chapter_index=0,
            chapter_title="Chapter 1",
            profile_id=AudioProfileId("voice_123")
        )
        assert chapter_audio.chapter_index == 0
        assert chapter_audio.chapter_title == "Chapter 1"
        assert len(chapter_audio.audio_files) == 0

    def test_add_audio_file_in_sequence(self) -> None:
        """Test adding audio files in proper sequence."""
        chapter_audio = ChapterAudiobook(
            chapter_index=0,
            chapter_title="Chapter 1"
        )

        audio_file_0 = AudioFile(0, Path("/tmp/chunk_0.mp3"), 120.0)
        audio_file_1 = AudioFile(1, Path("/tmp/chunk_1.mp3"), 150.0)

        chapter_audio.add_audio_file(audio_file_0)
        chapter_audio.add_audio_file(audio_file_1)

        assert len(chapter_audio.audio_files) == 2
        assert chapter_audio.audio_files[0].chunk_sequence == 0
        assert chapter_audio.audio_files[1].chunk_sequence == 1

    def test_add_audio_file_out_of_sequence_raises_error(self) -> None:
        """Test that adding audio files out of sequence raises error."""
        chapter_audio = ChapterAudiobook(
            chapter_index=0,
            chapter_title="Chapter 1"
        )

        audio_file_0 = AudioFile(0, Path("/tmp/chunk_0.mp3"), 120.0)
        audio_file_2 = AudioFile(2, Path("/tmp/chunk_2.mp3"), 150.0)

        chapter_audio.add_audio_file(audio_file_0)
        with pytest.raises(ValueError, match="Expected sequence 1"):
            chapter_audio.add_audio_file(audio_file_2)

    def test_get_total_duration(self) -> None:
        """Test calculating total duration of chapter."""
        chapter_audio = ChapterAudiobook(
            chapter_index=0,
            chapter_title="Chapter 1"
        )

        audio_file_0 = AudioFile(0, Path("/tmp/chunk_0.mp3"), 120.0)
        audio_file_1 = AudioFile(1, Path("/tmp/chunk_1.mp3"), 150.0)

        chapter_audio.add_audio_file(audio_file_0)
        chapter_audio.add_audio_file(audio_file_1)

        assert chapter_audio.get_total_duration() == 270.0

    def test_is_complete_no_files(self) -> None:
        """Test is_complete when no files added."""
        chapter_audio = ChapterAudiobook(
            chapter_index=0,
            chapter_title="Chapter 1"
        )
        assert not chapter_audio.is_complete()

    def test_is_complete_with_files(self) -> None:
        """Test is_complete when files exist (mocked)."""
        # Note: In real scenario, would need actual files to check exists()
        # For this unit test, we're testing the logic
        chapter_audio = ChapterAudiobook(
            chapter_index=0,
            chapter_title="Chapter 1"
        )

        # Without actual files, is_complete will be False
        audio_file = AudioFile(0, Path("/tmp/nonexistent.mp3"), 120.0)
        chapter_audio.add_audio_file(audio_file)
        assert not chapter_audio.is_complete()


class TestAudiobook:
    """Test Audiobook aggregate root entity."""

    @pytest.fixture
    def sample_epub_file(self) -> EPUBFile:
        """Create a sample EPUB file for testing."""
        return EPUBFile(
            file_path=FilePath(Path("/tmp/sample.epub")),
            metadata=Metadata(
                title="Test Book",
                author="Test Author",
                language="en"
            ),
            chapters=[
                Chapter(
                    id=ChapterId(0),
                    title="Chapter 1",
                    content="Sample content",
                    order=0
                )
            ]
        )

    def test_create_audiobook(self, sample_epub_file: EPUBFile) -> None:
        """Test creating an audiobook."""
        audiobook = Audiobook(
            epub_file=sample_epub_file,
            profile_id=AudioProfileId("voice_123"),
            output_path=Path("/tmp/output.mp3")
        )
        assert audiobook.epub_file == sample_epub_file
        assert audiobook.profile_id.value == "voice_123"
        assert len(audiobook.chapter_audiobooks) == 0

    def test_add_chapter_audiobook(self, sample_epub_file: EPUBFile) -> None:
        """Test adding chapter audiobooks."""
        audiobook = Audiobook(
            epub_file=sample_epub_file,
            profile_id=AudioProfileId("voice_123"),
            output_path=Path("/tmp/output.mp3")
        )

        chapter_audio = ChapterAudiobook(
            chapter_index=0,
            chapter_title="Chapter 1"
        )
        audiobook.add_chapter_audiobook(chapter_audio)

        assert len(audiobook.chapter_audiobooks) == 1
        assert audiobook.chapter_audiobooks[0].chapter_index == 0

    def test_add_duplicate_chapter_audiobook_raises_error(
        self, sample_epub_file: EPUBFile
    ) -> None:
        """Test that adding duplicate chapter raises error."""
        audiobook = Audiobook(
            epub_file=sample_epub_file,
            profile_id=AudioProfileId("voice_123"),
            output_path=Path("/tmp/output.mp3")
        )

        chapter_audio_1 = ChapterAudiobook(chapter_index=0, chapter_title="Ch 1")
        chapter_audio_2 = ChapterAudiobook(chapter_index=0, chapter_title="Ch 1")

        audiobook.add_chapter_audiobook(chapter_audio_1)
        with pytest.raises(ValueError, match="Chapter 0 already exists"):
            audiobook.add_chapter_audiobook(chapter_audio_2)

    def test_get_chapter_audiobook(self, sample_epub_file: EPUBFile) -> None:
        """Test retrieving chapter audiobook by index."""
        audiobook = Audiobook(
            epub_file=sample_epub_file,
            profile_id=AudioProfileId("voice_123"),
            output_path=Path("/tmp/output.mp3")
        )

        chapter_audio = ChapterAudiobook(chapter_index=0, chapter_title="Ch 1")
        audiobook.add_chapter_audiobook(chapter_audio)

        retrieved = audiobook.get_chapter_audiobook(0)
        assert retrieved == chapter_audio

    def test_get_chapter_audiobook_not_found(self, sample_epub_file: EPUBFile) -> None:
        """Test getting non-existent chapter returns None."""
        audiobook = Audiobook(
            epub_file=sample_epub_file,
            profile_id=AudioProfileId("voice_123"),
            output_path=Path("/tmp/output.mp3")
        )

        retrieved = audiobook.get_chapter_audiobook(0)
        assert retrieved is None

    def test_get_total_duration(self, sample_epub_file: EPUBFile) -> None:
        """Test calculating total audiobook duration."""
        audiobook = Audiobook(
            epub_file=sample_epub_file,
            profile_id=AudioProfileId("voice_123"),
            output_path=Path("/tmp/output.mp3")
        )

        chapter_audio = ChapterAudiobook(chapter_index=0, chapter_title="Ch 1")
        chapter_audio.add_audio_file(AudioFile(0, Path("/tmp/chunk_0.mp3"), 120.0))
        chapter_audio.add_audio_file(AudioFile(1, Path("/tmp/chunk_1.mp3"), 150.0))

        audiobook.add_chapter_audiobook(chapter_audio)

        assert audiobook.get_total_duration() == 270.0

    def test_set_final_audio_path(self, sample_epub_file: EPUBFile) -> None:
        """Test setting final audio path."""
        audiobook = Audiobook(
            epub_file=sample_epub_file,
            profile_id=AudioProfileId("voice_123"),
            output_path=Path("/tmp/output.mp3")
        )

        final_path = Path("/tmp/final.mp3")
        audiobook.set_final_audio_path(final_path)
        assert audiobook.final_audio_path == final_path

    def test_is_complete_no_chapters(self, sample_epub_file: EPUBFile) -> None:
        """Test is_complete with no chapters."""
        audiobook = Audiobook(
            epub_file=sample_epub_file,
            profile_id=AudioProfileId("voice_123"),
            output_path=Path("/tmp/output.mp3")
        )
        assert not audiobook.is_complete()


class TestChapter:
    """Test Chapter entity."""

    def test_create_chapter(self) -> None:
        """Test creating a chapter."""
        chapter = Chapter(
            id=ChapterId(1),
            title="Chapter 1",
            content="Some content here",
            order=0
        )
        assert chapter.id.value == 1
        assert chapter.title == "Chapter 1"

    def test_is_valid_chapter(self) -> None:
        """Test chapter validation."""
        chapter = Chapter(
            id=ChapterId(1),
            title="Chapter 1",
            content="Content",
            order=0
        )
        assert chapter.is_valid()

    def test_is_invalid_chapter_empty_title(self) -> None:
        """Test chapter with empty title is invalid."""
        chapter = Chapter(
            id=ChapterId(1),
            title="   ",
            content="Content",
            order=0
        )
        assert not chapter.is_valid()

    def test_is_invalid_chapter_negative_order(self) -> None:
        """Test chapter with negative order is invalid."""
        chapter = Chapter(
            id=ChapterId(1),
            title="Chapter 1",
            content="Content",
            order=-1
        )
        assert not chapter.is_valid()

    def test_get_word_count(self) -> None:
        """Test word count calculation."""
        chapter = Chapter(
            id=ChapterId(1),
            title="Chapter 1",
            content="This is a test chapter with ten words in it.",
            order=0
        )
        assert chapter.get_word_count() == 10


class TestFilePath:
    """Test FilePath value object."""

    def test_create_file_path(self) -> None:
        """Test creating a file path."""
        path = FilePath(Path("/tmp/test.epub"))
        assert path.value == Path("/tmp/test.epub")

    def test_file_path_immutable(self) -> None:
        """Test that file path is immutable."""
        path = FilePath(Path("/tmp/test.epub"))
        with pytest.raises(AttributeError):
            path.value = Path("/tmp/other.epub")  # type: ignore

    def test_file_path_invalid_type_raises_error(self) -> None:
        """Test that non-Path input raises error."""
        with pytest.raises(ValueError, match="FilePath value must be a Path instance"):
            FilePath("/tmp/test.epub")  # type: ignore

    def test_file_path_string_representation(self) -> None:
        """Test string representation of file path."""
        path = FilePath(Path("/tmp/test.epub"))
        # Path representation varies by platform (/ vs \)
        assert "test.epub" in str(path)


class TestMetadata:
    """Test Metadata value object."""

    def test_create_metadata(self) -> None:
        """Test creating metadata."""
        metadata = Metadata(
            title="Test Book",
            author="Test Author",
            language="en",
            identifier="isbn123"
        )
        assert metadata.title == "Test Book"
        assert metadata.author == "Test Author"

    def test_metadata_empty_title_raises_error(self) -> None:
        """Test that empty title raises error."""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            Metadata(
                title="   ",
                author="Test Author"
            )

    def test_metadata_immutable(self) -> None:
        """Test that metadata is immutable."""
        metadata = Metadata(title="Test Book")
        with pytest.raises(AttributeError):
            metadata.title = "Changed"  # type: ignore


class TestEPUBFile:
    """Test EPUBFile aggregate root."""

    def test_create_epub_file(self) -> None:
        """Test creating an EPUB file."""
        epub = EPUBFile(
            file_path=FilePath(Path("/tmp/test.epub")),
            metadata=Metadata(title="Test Book")
        )
        assert epub.file_path.value == Path("/tmp/test.epub")
        assert len(epub.chapters) == 0

    def test_add_chapter(self) -> None:
        """Test adding a chapter."""
        epub = EPUBFile(
            file_path=FilePath(Path("/tmp/test.epub")),
            metadata=Metadata(title="Test Book")
        )

        chapter = Chapter(
            id=ChapterId(0),
            title="Chapter 1",
            content="Content",
            order=0
        )
        epub.add_chapter(chapter)

        assert len(epub.chapters) == 1
        assert epub.chapters[0].title == "Chapter 1"

    def test_add_invalid_chapter_raises_error(self) -> None:
        """Test that adding invalid chapter raises error."""
        epub = EPUBFile(
            file_path=FilePath(Path("/tmp/test.epub")),
            metadata=Metadata(title="Test Book")
        )

        invalid_chapter = Chapter(
            id=ChapterId(0),
            title="   ",  # Invalid: empty
            content="Content",
            order=0
        )

        with pytest.raises(ValueError, match="Invalid chapter"):
            epub.add_chapter(invalid_chapter)

    def test_get_total_word_count(self) -> None:
        """Test total word count calculation."""
        epub = EPUBFile(
            file_path=FilePath(Path("/tmp/test.epub")),
            metadata=Metadata(title="Test Book")
        )

        chapter1 = Chapter(
            id=ChapterId(0),
            title="Ch 1",
            content="This is chapter one",
            order=0
        )
        chapter2 = Chapter(
            id=ChapterId(1),
            title="Ch 2",
            content="This is chapter two more words",
            order=1
        )

        epub.add_chapter(chapter1)
        epub.add_chapter(chapter2)

        # Total words: 4 + 6 = 10
        assert epub.get_total_word_count() == 10

    def test_get_chapter_by_id(self) -> None:
        """Test retrieving chapter by ID."""
        epub = EPUBFile(
            file_path=FilePath(Path("/tmp/test.epub")),
            metadata=Metadata(title="Test Book")
        )

        chapter = Chapter(
            id=ChapterId(0),
            title="Chapter 1",
            content="Content",
            order=0
        )
        epub.add_chapter(chapter)

        retrieved = epub.get_chapter_by_id(ChapterId(0))
        assert retrieved == chapter

    def test_get_chapter_by_id_not_found(self) -> None:
        """Test getting non-existent chapter returns None."""
        epub = EPUBFile(
            file_path=FilePath(Path("/tmp/test.epub")),
            metadata=Metadata(title="Test Book")
        )

        retrieved = epub.get_chapter_by_id(ChapterId(0))
        assert retrieved is None
