"""Unit tests for audiobook conversion application layer.

Tests use case orchestration using mock implementations of domain protocols.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from epub_converter.application.audiobook_conversion.use_cases import (
    ConvertEPUBToAudiobookUseCase,
    ListVoiceProfilesUseCase,
)
from epub_converter.application.audiobook_conversion.dtos import (
    ConvertEPUBToAudiobookInput,
    ConvertEPUBToAudiobookOutput,
    ListVoiceProfilesOutput,
)
from epub_converter.domain.audiobook_conversion.value_objects import (
    AudioProfile,
    AudioProfileId,
)
from epub_converter.domain.epub_extraction.value_objects import (
    ChapterId,
    FilePath,
    Metadata,
)
from epub_converter.domain.epub_extraction.entities import Chapter, EPUBFile

from tests.conftest import (
    MockEPUBRepository,
    MockVoiceBoxService,
    MockTextChunker,
    MockAudioProcessor,
    MockAudiobookRepository,
)


class TestListVoiceProfilesUseCase:
    """Test listing voice profiles use case."""

    def test_list_voice_profiles_success(self) -> None:
        """Test successfully listing voice profiles."""
        mock_voicebox = MockVoiceBoxService()
        mock_voicebox.add_profile(
            AudioProfile(
                id=AudioProfileId("voice_1"),
                name="Deep Voice",
                language="en",
                description="A deep male voice"
            )
        )

        use_case = ListVoiceProfilesUseCase(mock_voicebox)
        output = use_case.execute()

        assert isinstance(output, ListVoiceProfilesOutput)
        assert output.profile_count == 1
        assert output.profiles[0]["id"] == "voice_1"
        assert output.profiles[0]["name"] == "Deep Voice"
        assert output.profiles[0]["language"] == "en"

    def test_list_voice_profiles_empty(self) -> None:
        """Test listing when no profiles configured."""
        mock_voicebox = MockVoiceBoxService()

        use_case = ListVoiceProfilesUseCase(mock_voicebox)
        output = use_case.execute()

        assert output.profile_count == 2  # Default profiles
        assert all(p["id"] in ["voice_1", "voice_2"] for p in output.profiles)

    def test_list_voice_profiles_multiple(self) -> None:
        """Test listing multiple voice profiles."""
        mock_voicebox = MockVoiceBoxService()

        for i in range(3):
            mock_voicebox.add_profile(
                AudioProfile(
                    id=AudioProfileId(f"voice_{i}"),
                    name=f"Voice {i}",
                    language="en",
                    description=f"Test voice {i}"
                )
            )

        use_case = ListVoiceProfilesUseCase(mock_voicebox)
        output = use_case.execute()

        assert output.profile_count == 3

    def test_list_voice_profiles_calls_service(self) -> None:
        """Test that use case calls VoiceBox service."""
        mock_voicebox = MockVoiceBoxService()

        use_case = ListVoiceProfilesUseCase(mock_voicebox)
        use_case.execute()

        assert mock_voicebox.was_get_profiles_called()


class TestConvertEPUBToAudiobookUseCase:
    """Test converting EPUB to audiobook use case."""

    def test_convert_epub_to_audiobook_success(self, tmp_path: Path) -> None:
        """Test successful EPUB to audiobook conversion."""
        # Create temporary EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub content")

        # Setup mocks
        mock_epub_repo = MockEPUBRepository()
        mock_voicebox = MockVoiceBoxService()
        mock_chunker = MockTextChunker()
        mock_audio_proc = MockAudioProcessor()
        mock_audiobook_repo = MockAudiobookRepository()

        # Configure mock audio processor durations
        mock_audio_proc.set_audio_duration(
            Path("/tmp/chapter_0.mp3"), 200.0
        )
        mock_audio_proc.set_audio_duration(
            Path("/tmp/chapter_1.mp3"), 250.0
        )

        use_case = ConvertEPUBToAudiobookUseCase(
            epub_repository=mock_epub_repo,
            voicebox_service=mock_voicebox,
            text_chunker=mock_chunker,
            audio_processor=mock_audio_proc,
            audiobook_repository=mock_audiobook_repo,
        )

        with TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "output.mp3"

            input_dto = ConvertEPUBToAudiobookInput(
                epub_file_path=epub_file,
                output_file_path=output_file,
                voice_profile_id="voice_1",
                language="en",
                chunk_size=45000
            )

            output = use_case.execute(input_dto)

            assert isinstance(output, ConvertEPUBToAudiobookOutput)
            assert output.output_file_path == output_file
            assert output.chapter_count == 2
            assert output.voice_profile_id == "voice_1"
            # Check that output file was created
            assert output_file.exists()

    def test_convert_epub_invalid_epub_path(self) -> None:
        """Test conversion with invalid EPUB path."""
        use_case = ConvertEPUBToAudiobookUseCase(
            epub_repository=MockEPUBRepository(),
            voicebox_service=MockVoiceBoxService(),
            text_chunker=MockTextChunker(),
            audio_processor=MockAudioProcessor(),
            audiobook_repository=MockAudiobookRepository(),
        )

        with pytest.raises(ValueError, match="EPUB file not found"):
            ConvertEPUBToAudiobookInput(
                epub_file_path=Path("/nonexistent/book.epub"),
                output_file_path=Path("/tmp/output.mp3"),
                voice_profile_id="voice_1"
            )

    def test_convert_epub_invalid_chunk_size(self, tmp_path: Path) -> None:
        """Test conversion with invalid chunk size."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        with pytest.raises(ValueError, match="chunk_size must be positive"):
            ConvertEPUBToAudiobookInput(
                epub_file_path=epub_file,
                output_file_path=tmp_path / "output.mp3",
                voice_profile_id="voice_1",
                chunk_size=-1
            )

    def test_convert_epub_calls_voicebox_for_each_chunk(self, tmp_path: Path) -> None:
        """Test that use case calls VoiceBox for each chunk."""
        # Create temporary EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub content")

        mock_epub_repo = MockEPUBRepository()
        mock_voicebox = MockVoiceBoxService()
        mock_chunker = MockTextChunker()
        mock_audio_proc = MockAudioProcessor()
        mock_audiobook_repo = MockAudiobookRepository()

        # Configure audio processor
        mock_audio_proc.set_audio_duration(
            Path("/tmp/chapter_0.mp3"), 200.0
        )
        mock_audio_proc.set_audio_duration(
            Path("/tmp/chapter_1.mp3"), 250.0
        )

        use_case = ConvertEPUBToAudiobookUseCase(
            epub_repository=mock_epub_repo,
            voicebox_service=mock_voicebox,
            text_chunker=mock_chunker,
            audio_processor=mock_audio_proc,
            audiobook_repository=mock_audiobook_repo,
        )

        with TemporaryDirectory() as temp_dir:
            input_dto = ConvertEPUBToAudiobookInput(
                epub_file_path=epub_file,
                output_file_path=Path(temp_dir) / "output.mp3",
                voice_profile_id="voice_1",
                chunk_size=10000  # Small size to force multiple chunks
            )

            use_case.execute(input_dto)

            # Verify VoiceBox was called
            generate_calls = mock_voicebox.get_generate_calls()
            assert len(generate_calls) > 0

            # Verify all calls have correct profile and language
            for text, profile_id, language, engine in generate_calls:
                assert profile_id == "voice_1"
                assert language == "en"
                assert engine == "kokoro"
                assert len(text) > 0

    def test_convert_epub_calls_text_chunker(self, tmp_path: Path) -> None:
        """Test that use case calls text chunker for each chapter."""
        # Create temporary EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub content")

        mock_epub_repo = MockEPUBRepository()
        mock_voicebox = MockVoiceBoxService()
        mock_chunker = MockTextChunker()
        mock_audio_proc = MockAudioProcessor()
        mock_audiobook_repo = MockAudiobookRepository()

        # Configure audio processor
        mock_audio_proc.set_audio_duration(
            Path("/tmp/chapter_0.mp3"), 200.0
        )
        mock_audio_proc.set_audio_duration(
            Path("/tmp/chapter_1.mp3"), 250.0
        )

        use_case = ConvertEPUBToAudiobookUseCase(
            epub_repository=mock_epub_repo,
            voicebox_service=mock_voicebox,
            text_chunker=mock_chunker,
            audio_processor=mock_audio_proc,
            audiobook_repository=mock_audiobook_repo,
        )

        with TemporaryDirectory() as temp_dir:
            input_dto = ConvertEPUBToAudiobookInput(
                epub_file_path=epub_file,
                output_file_path=Path(temp_dir) / "output.mp3",
                voice_profile_id="voice_1",
                chunk_size=45000
            )

            use_case.execute(input_dto)

            # Verify chunker was called for each chapter
            chunk_calls = mock_chunker.get_chunk_calls()
            assert len(chunk_calls) == 2  # Two chapters

    def test_convert_epub_calls_audio_processor_merge(self, tmp_path: Path) -> None:
        """Test that use case calls audio processor to merge files."""
        # Create temporary EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub content")

        mock_epub_repo = MockEPUBRepository()
        mock_voicebox = MockVoiceBoxService()
        mock_chunker = MockTextChunker()
        mock_audio_proc = MockAudioProcessor()
        mock_audiobook_repo = MockAudiobookRepository()

        # Configure audio processor
        mock_audio_proc.set_audio_duration(
            Path("/tmp/chapter_0.mp3"), 200.0
        )
        mock_audio_proc.set_audio_duration(
            Path("/tmp/chapter_1.mp3"), 250.0
        )

        use_case = ConvertEPUBToAudiobookUseCase(
            epub_repository=mock_epub_repo,
            voicebox_service=mock_voicebox,
            text_chunker=mock_chunker,
            audio_processor=mock_audio_proc,
            audiobook_repository=mock_audiobook_repo,
        )

        with TemporaryDirectory() as temp_dir:
            input_dto = ConvertEPUBToAudiobookInput(
                epub_file_path=epub_file,
                output_file_path=Path(temp_dir) / "output.mp3",
                voice_profile_id="voice_1",
            )

            use_case.execute(input_dto)

            # Verify audio processor merge was called
            merge_calls = mock_audio_proc.get_merge_calls()
            # Should have: merges for each chapter + final merge
            assert len(merge_calls) >= 3  # At least 2 chapter merges + 1 final

    def test_convert_epub_saves_audiobook_metadata(self, tmp_path: Path) -> None:
        """Test that use case completes conversion successfully."""
        # Create temporary EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub content")

        mock_epub_repo = MockEPUBRepository()
        mock_voicebox = MockVoiceBoxService()
        mock_chunker = MockTextChunker()
        mock_audio_proc = MockAudioProcessor()
        mock_audiobook_repo = MockAudiobookRepository()

        # Configure audio processor
        mock_audio_proc.set_audio_duration(
            Path("/tmp/chapter_0.mp3"), 200.0
        )
        mock_audio_proc.set_audio_duration(
            Path("/tmp/chapter_1.mp3"), 250.0
        )

        use_case = ConvertEPUBToAudiobookUseCase(
            epub_repository=mock_epub_repo,
            voicebox_service=mock_voicebox,
            text_chunker=mock_chunker,
            audio_processor=mock_audio_proc,
            audiobook_repository=mock_audiobook_repo,
        )

        with TemporaryDirectory() as temp_dir:
            input_dto = ConvertEPUBToAudiobookInput(
                epub_file_path=epub_file,
                output_file_path=Path(temp_dir) / "output.mp3",
                voice_profile_id="voice_1",
            )

            # Should complete without error
            output = use_case.execute(input_dto)

            # Verify output is valid
            assert output.output_file_path.exists()
            assert output.chapter_count == 2


class TestConvertEPUBToAudiobookInputDTO:
    """Test input DTO for EPUB to audiobook conversion."""

    def test_valid_input_dto(self, tmp_path: Path) -> None:
        """Test creating valid input DTO."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        input_dto = ConvertEPUBToAudiobookInput(
            epub_file_path=epub_file,
            output_file_path=tmp_path / "output.mp3",
            voice_profile_id="voice_1",
            language="en",
            chunk_size=45000
        )

        assert input_dto.epub_file_path == epub_file
        assert input_dto.language == "en"
        assert input_dto.chunk_size == 45000

    def test_input_dto_default_values(self, tmp_path: Path) -> None:
        """Test input DTO with default values."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        input_dto = ConvertEPUBToAudiobookInput(
            epub_file_path=epub_file,
            output_file_path=tmp_path / "output.mp3",
            voice_profile_id="voice_1"
        )

        assert input_dto.language == "en"
        assert input_dto.chunk_size == 45000

    def test_input_dto_nonexistent_epub_raises_error(self, tmp_path: Path) -> None:
        """Test that nonexistent EPUB raises error."""
        with pytest.raises(ValueError, match="EPUB file not found"):
            ConvertEPUBToAudiobookInput(
                epub_file_path=tmp_path / "nonexistent.epub",
                output_file_path=tmp_path / "output.mp3",
                voice_profile_id="voice_1"
            )

    def test_input_dto_negative_chunk_size_raises_error(self, tmp_path: Path) -> None:
        """Test that negative chunk size raises error."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub")

        with pytest.raises(ValueError, match="chunk_size must be positive"):
            ConvertEPUBToAudiobookInput(
                epub_file_path=epub_file,
                output_file_path=tmp_path / "output.mp3",
                voice_profile_id="voice_1",
                chunk_size=-100
            )


class TestConvertEPUBToAudiobookOutputDTO:
    """Test output DTO for EPUB to audiobook conversion."""

    def test_valid_output_dto(self, tmp_path: Path) -> None:
        """Test creating valid output DTO."""
        output_file = tmp_path / "output.mp3"

        output_dto = ConvertEPUBToAudiobookOutput(
            output_file_path=output_file,
            total_duration_seconds=3600.0,
            chapter_count=10,
            voice_profile_id="voice_1"
        )

        assert output_dto.output_file_path == output_file
        assert output_dto.total_duration_seconds == 3600.0
        assert output_dto.chapter_count == 10

    def test_output_dto_zero_duration_raises_error(self, tmp_path: Path) -> None:
        """Test that zero duration raises error."""
        with pytest.raises(ValueError, match="total_duration_seconds must be positive"):
            ConvertEPUBToAudiobookOutput(
                output_file_path=tmp_path / "output.mp3",
                total_duration_seconds=0,
                chapter_count=10,
                voice_profile_id="voice_1"
            )

    def test_output_dto_zero_chapter_count_raises_error(self, tmp_path: Path) -> None:
        """Test that zero chapter count raises error."""
        with pytest.raises(ValueError, match="chapter_count must be positive"):
            ConvertEPUBToAudiobookOutput(
                output_file_path=tmp_path / "output.mp3",
                total_duration_seconds=3600.0,
                chapter_count=0,
                voice_profile_id="voice_1"
            )


class TestListVoiceProfilesOutputDTO:
    """Test output DTO for listing voice profiles."""

    def test_valid_list_profiles_output(self) -> None:
        """Test creating valid list profiles output."""
        profiles = [
            {
                "id": "voice_1",
                "name": "Voice 1",
                "language": "en",
                "description": "Test voice"
            }
        ]

        output_dto = ListVoiceProfilesOutput(profiles=profiles)

        assert output_dto.profile_count == 1
        assert output_dto.profiles[0]["id"] == "voice_1"

    def test_empty_profiles_list(self) -> None:
        """Test with empty profiles list."""
        output_dto = ListVoiceProfilesOutput(profiles=[])

        assert output_dto.profile_count == 0
        assert len(output_dto.profiles) == 0
