"""Mock implementations of domain interfaces for testing.

These mocks are used in application and infrastructure layer tests.
They implement the domain protocols without external dependencies.
"""

from pathlib import Path
from typing import Any

from epub_converter.domain.audiobook_conversion.value_objects import (
    AudioFile,
    AudioProfile,
    AudioProfileId,
    TextChunk,
)
from epub_converter.domain.epub_extraction.entities import Chapter, EPUBFile
from epub_converter.domain.epub_extraction.value_objects import (
    ChapterId,
    FilePath,
    Metadata,
)


class MockEPUBRepository:
    """Mock EPUB repository implementation."""

    def __init__(self, epub_file: EPUBFile | None = None) -> None:
        """Initialize with optional pre-configured EPUB file."""
        self._epub_file = epub_file or self._create_default_epub()
        self._save_called = False
        self._saved_file: EPUBFile | None = None

    def _create_default_epub(self) -> EPUBFile:
        """Create a default EPUB file for testing."""
        epub = EPUBFile(
            file_path=FilePath(Path("/test/sample.epub")),
            metadata=Metadata(
                title="Test Book",
                author="Test Author",
                language="en"
            )
        )

        chapter1 = Chapter(
            id=ChapterId(0),
            title="Chapter 1",
            content="This is the content of chapter one. " * 100,
            order=0
        )
        chapter2 = Chapter(
            id=ChapterId(1),
            title="Chapter 2",
            content="This is the content of chapter two. " * 100,
            order=1
        )

        epub.add_chapter(chapter1)
        epub.add_chapter(chapter2)

        return epub

    def load(self, file_path: FilePath) -> EPUBFile:
        """Load an EPUB file (returns pre-configured file)."""
        return self._epub_file

    def save(self, epub_file: EPUBFile, file_path: FilePath) -> None:
        """Save an EPUB file (tracks call for testing)."""
        self._save_called = True
        self._saved_file = epub_file

    def was_save_called(self) -> bool:
        """Check if save was called."""
        return self._save_called

    def get_saved_file(self) -> EPUBFile | None:
        """Get the saved file."""
        return self._saved_file


class MockTTSProvider:
    """Mock TTS provider implementation."""

    def __init__(self, audio_data: bytes | None = None) -> None:
        """Initialize with optional audio data."""
        self._audio_data = audio_data or b"ID3" + b"\x00" * 1000  # Fake MP3
        self._generate_calls: list[tuple[str, str, str]] = []
        self._profiles: list[AudioProfile] = []
        self._profiles_called = False

    def add_profile(self, profile: AudioProfile) -> None:
        """Add a profile to return."""
        self._profiles.append(profile)

    def get_available_profiles(self) -> list[AudioProfile]:
        """Get available profiles."""
        self._profiles_called = True
        if not self._profiles:
            return [
                AudioProfile(
                    id=AudioProfileId("voice_1"),
                    name="Voice 1",
                    language="en",
                    description="Test voice 1"
                ),
                AudioProfile(
                    id=AudioProfileId("voice_2"),
                    name="Voice 2",
                    language="en",
                    description="Test voice 2"
                ),
            ]
        return self._profiles

    def generate_speech(
        self, text: str, profile_id: str, language: str, engine: str = "kokoro"
    ) -> bytes:
        """Generate speech (returns fake audio data)."""
        self._generate_calls.append((text, profile_id, language, engine))
        if not text.strip():
            raise ValueError("Text cannot be empty")
        if not profile_id.strip():
            raise ValueError("profile_id cannot be empty")
        return self._audio_data

    def get_generate_calls(self) -> list[tuple[str, str, str, str]]:
        """Get all generate calls for verification."""
        return self._generate_calls

    def was_get_profiles_called(self) -> bool:
        """Check if get_available_profiles was called."""
        return self._profiles_called

    def set_audio_data(self, data: bytes) -> None:
        """Set custom audio data for testing."""
        self._audio_data = data


class MockTextChunker:
    """Mock text chunker implementation."""

    def __init__(self, chunk_size: int = 45000) -> None:
        """Initialize with optional chunk size."""
        self._chunk_size = chunk_size
        self._chunk_calls: list[tuple[str, int]] = []

    def chunk_text(
        self, text: str, max_chunk_size: int = 45000
    ) -> list[TextChunk]:
        """Chunk text into manageable pieces."""
        self._chunk_calls.append((text, max_chunk_size))

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        if max_chunk_size <= 0:
            raise ValueError("max_chunk_size must be positive")

        chunks = []
        sequence = 0
        start_char = 0

        while start_char < len(text):
            end_char = min(start_char + max_chunk_size, len(text))

            # Try to break at word boundary
            if end_char < len(text):
                last_space = text.rfind(" ", start_char, end_char)
                if last_space > start_char:
                    end_char = last_space + 1

            chunk_text = text[start_char:end_char].strip()
            if chunk_text:
                chunks.append(
                    TextChunk(
                        sequence=sequence,
                        text=chunk_text,
                        start_char=start_char,
                        end_char=end_char,
                    )
                )
                sequence += 1

            start_char = end_char

        return chunks if chunks else [
            TextChunk(
                sequence=0,
                text=text.strip(),
                start_char=0,
                end_char=len(text),
            )
        ]

    def get_chunk_calls(self) -> list[tuple[str, int]]:
        """Get all chunk calls for verification."""
        return self._chunk_calls


class MockAudioProcessor:
    """Mock audio processor implementation."""

    def __init__(self) -> None:
        """Initialize the mock."""
        self._duration_calls: list[Path] = []
        self._merge_calls: list[tuple[list[Path], Path]] = []
        self._durations: dict[Path, float] = {}

    def set_audio_duration(self, audio_file: Path, duration: float) -> None:
        """Set the duration to return for an audio file."""
        self._durations[audio_file] = duration

    def get_audio_duration(self, audio_file: Path) -> float:
        """Get duration of an audio file."""
        self._duration_calls.append(audio_file)

        if not audio_file.exists():
            if audio_file in self._durations:
                return self._durations[audio_file]
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        return self._durations.get(audio_file, 120.0)

    def merge_audio_files(self, audio_files: list[Path], output_path: Path) -> None:
        """Merge audio files (creates empty file for testing)."""
        self._merge_calls.append((audio_files, output_path))

        if not audio_files:
            raise ValueError("audio_files cannot be empty")

        # Create the output file (empty for testing)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"ID3" + b"\x00" * 100)

        # Set a default duration for the merged file
        if output_path not in self._durations:
            # Calculate expected duration from source files
            total_duration = 0.0
            for audio_file in audio_files:
                if audio_file in self._durations:
                    total_duration += self._durations[audio_file]
                else:
                    total_duration += 100.0  # Default
            self._durations[output_path] = total_duration

    def get_merge_calls(self) -> list[tuple[list[Path], Path]]:
        """Get all merge calls for verification."""
        return self._merge_calls

    def get_duration_calls(self) -> list[Path]:
        """Get all duration calls for verification."""
        return self._duration_calls


class MockAudiobookRepository:
    """Mock audiobook repository implementation."""

    def __init__(self) -> None:
        """Initialize the mock."""
        self._saved_audiobooks: list[Any] = []

    def save_audiobook(self, audiobook: Any) -> None:
        """Save an audiobook (stores reference for testing)."""
        self._saved_audiobooks.append(audiobook)

    def get_audiobook(self, epub_path: Path) -> Any:
        """Retrieve an audiobook by EPUB path."""
        for audiobook in self._saved_audiobooks:
            if audiobook.epub_file.file_path.value == epub_path:
                return audiobook
        return None

    def get_saved_audiobooks(self) -> list[Any]:
        """Get all saved audiobooks for verification."""
        return self._saved_audiobooks


class MockLoadEPUBUseCase:
    """Mock load EPUB use case."""

    def __init__(self, epub_file: EPUBFile | None = None) -> None:
        """Initialize with optional EPUB file."""
        self._epub_file = epub_file or EPUBFile(
            file_path=FilePath(Path("/test/sample.epub")),
            metadata=Metadata(title="Test Book")
        )
        self._execute_called = False

    def execute(self, input_dto: Any) -> Any:
        """Execute the use case."""
        self._execute_called = True
        return self._epub_file

    def was_execute_called(self) -> bool:
        """Check if execute was called."""
        return self._execute_called


class MockExtractChapterUseCase:
    """Mock extract chapter use case."""

    def __init__(self, chapters: list[Chapter] | None = None) -> None:
        """Initialize with optional chapters."""
        if chapters is None:
            chapters = [
                Chapter(
                    id=ChapterId(0),
                    title="Chapter 1",
                    content="Sample content",
                    order=0
                )
            ]
        self._chapters = chapters
        self._execute_called = False

    def execute(self, input_dto: Any) -> Any:
        """Execute the use case."""
        self._execute_called = True
        return self._chapters

    def was_execute_called(self) -> bool:
        """Check if execute was called."""
        return self._execute_called


class MockConvertEPUBToAudiobookUseCase:
    """Mock convert EPUB to audiobook use case."""

    def __init__(self, output_dto: Any | None = None) -> None:
        """Initialize with optional output DTO."""
        self._output_dto = output_dto
        self._execute_called = False
        self._input_dto: Any = None

    def set_output_dto(self, output_dto: Any) -> None:
        """Set the output DTO to return."""
        self._output_dto = output_dto

    def execute(self, input_dto: Any) -> Any:
        """Execute the use case."""
        self._execute_called = True
        self._input_dto = input_dto

        if self._output_dto is None:
            raise RuntimeError("Output DTO not set on mock")

        return self._output_dto

    def was_execute_called(self) -> bool:
        """Check if execute was called."""
        return self._execute_called

    def get_input_dto(self) -> Any:
        """Get the input DTO that was passed to execute."""
        return self._input_dto


class MockListVoiceProfilesUseCase:
    """Mock list voice profiles use case."""

    def __init__(self, output_dto: Any | None = None) -> None:
        """Initialize with optional output DTO."""
        self._output_dto = output_dto
        self._execute_called = False

    def set_output_dto(self, output_dto: Any) -> None:
        """Set the output DTO to return."""
        self._output_dto = output_dto

    def execute(self) -> Any:
        """Execute the use case."""
        self._execute_called = True

        if self._output_dto is None:
            raise RuntimeError("Output DTO not set on mock")

        return self._output_dto

    def was_execute_called(self) -> bool:
        """Check if execute was called."""
        return self._execute_called
