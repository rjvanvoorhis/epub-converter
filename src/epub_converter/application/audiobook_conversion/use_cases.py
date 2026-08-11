"""Use cases for audiobook conversion application layer.

Use cases orchestrate domain logic and coordinate between different layers.
"""

from pathlib import Path

from epub_converter.domain.audiobook_conversion.interfaces import (
    AudiobookRepository,
    AudioProcessor,
    TextChunker,
    VoiceBoxService,
)
from epub_converter.domain.audiobook_conversion.value_objects import AudioFile
from epub_converter.domain.epub_extraction.interfaces import EPUBRepository
from epub_converter.presentation.text_utils import (
    strip_html_tags,
    normalize_text_characters,
)

from .dtos import (
    ConvertEPUBToAudiobookInput,
    ConvertEPUBToAudiobookOutput,
    ListVoiceProfilesOutput,
)


class ConvertEPUBToAudiobookUseCase:
    """Use case for converting an EPUB file to an audiobook.

    This orchestrates the entire conversion process:
    1. Load the EPUB file
    2. Extract chapters and text
    3. Chunk text into manageable pieces
    4. Generate speech for each chunk using VoiceBox
    5. Merge audio files into final output
    """

    def __init__(
        self,
        epub_repository: EPUBRepository,
        voicebox_service: VoiceBoxService,
        text_chunker: TextChunker,
        audio_processor: AudioProcessor,
        audiobook_repository: AudiobookRepository,
    ) -> None:
        """Initialize the use case with dependencies.

        Args:
            epub_repository: Repository for loading EPUB files.
            voicebox_service: Service for generating audio.
            text_chunker: Service for chunking text.
            audio_processor: Service for processing audio files.
            audiobook_repository: Repository for saving audiobooks.
        """
        self._epub_repository = epub_repository
        self._voicebox_service = voicebox_service
        self._text_chunker = text_chunker
        self._audio_processor = audio_processor
        self._audiobook_repository = audiobook_repository

    def execute(
        self, input_dto: ConvertEPUBToAudiobookInput
    ) -> ConvertEPUBToAudiobookOutput:
        """Execute the EPUB/text to audiobook conversion.

        Supports both EPUB files (with HTML stripping) and text directories.

        Args:
            input_dto: Input containing file paths and voice settings.

        Returns:
            Output with the generated audiobook path and metadata.

        Raises:
            ValueError: If input is invalid.
            RuntimeError: If conversion fails at any step.
        """
        # Prepare output directory
        output_dir = input_dto.output_file_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get chapters from either EPUB or text directory
        if input_dto.epub_file_path is not None:
            chapters_to_process = self._load_chapters_from_epub(
                input_dto.epub_file_path
            )
        else:
            chapters_to_process = self._load_chapters_from_text_directory(
                input_dto.text_directory_path
            )

        # Process each chapter
        chapter_audio_files: list[Path] = []

        for chapter_index, chapter in enumerate(chapters_to_process):
            # Clean the text (HTML stripping and character normalization)
            clean_content = normalize_text_characters(strip_html_tags(chapter["content"]))

            # Chunk the chapter text
            chunks = self._text_chunker.chunk_text(
                clean_content, input_dto.chunk_size
            )

            # Generate audio for each chunk
            chunk_audio_files: list[Path] = []
            for chunk in chunks:
                audio_data = self._voicebox_service.generate_speech(
                    chunk.text,
                    input_dto.voice_profile_id,
                    input_dto.language,
                    input_dto.engine,
                )

                # Save chunk audio
                chunk_path = (
                    output_dir / f"chapter_{chapter_index}_chunk_{chunk.sequence}.mp3"
                )
                chunk_path.write_bytes(audio_data)
                chunk_audio_files.append(chunk_path)

            # Merge chapter chunks into single chapter audio
            if chunk_audio_files:
                chapter_path = output_dir / f"chapter_{chapter_index}.mp3"
                self._audio_processor.merge_audio_files(chunk_audio_files, chapter_path)
                chapter_audio_files.append(chapter_path)

                # Clean up chunk files
                for chunk_file in chunk_audio_files[:-1]:
                    chunk_file.unlink()

        # Merge all chapter audio files into final audiobook
        self._audio_processor.merge_audio_files(
            chapter_audio_files, input_dto.output_file_path
        )

        # Clean up chapter files
        for chapter_file in chapter_audio_files:
            if chapter_file.exists():
                chapter_file.unlink()

        # Calculate total duration
        total_duration = self._audio_processor.get_audio_duration(
            input_dto.output_file_path
        )

        return ConvertEPUBToAudiobookOutput(
            output_file_path=input_dto.output_file_path,
            total_duration_seconds=total_duration,
            chapter_count=len(chapters_to_process),
            voice_profile_id=input_dto.voice_profile_id,
        )

    def _load_chapters_from_epub(
        self, epub_path: Path
    ) -> list[dict[str, str]]:
        """Load and extract chapters from an EPUB file.

        Args:
            epub_path: Path to the EPUB file

        Returns:
            List of chapters with 'title' and 'content' keys
        """
        from epub_converter.domain.epub_extraction.value_objects import FilePath

        epub_file = self._epub_repository.load(FilePath(epub_path))

        chapters = []
        for chapter in epub_file.chapters:
            chapters.append({"title": chapter.title, "content": chapter.content})

        return chapters

    def _load_chapters_from_text_directory(
        self, text_dir: Path
    ) -> list[dict[str, str]]:
        """Load chapters from a directory of text files.

        Args:
            text_dir: Path to directory containing .txt files

        Returns:
            List of chapters with 'title' and 'content' keys
        """
        from epub_converter.infrastructure.audiobook_conversion.text_file_reader import (
            TextFileReaderService,
        )

        reader = TextFileReaderService()
        file_chapters = reader.read_chapters(text_dir)

        chapters = []
        for file_chapter in file_chapters:
            chapters.append({"title": file_chapter.title, "content": file_chapter.content})

        return chapters


class ListVoiceProfilesUseCase:
    """Use case for listing available voice profiles."""

    def __init__(self, voicebox_service: VoiceBoxService) -> None:
        """Initialize the use case.

        Args:
            voicebox_service: Service for retrieving voice profiles.
        """
        self._voicebox_service = voicebox_service

    def execute(self) -> ListVoiceProfilesOutput:
        """Execute the list voice profiles use case.

        Returns:
            Output containing available voice profiles.

        Raises:
            RuntimeError: If unable to retrieve profiles.
        """
        profiles = self._voicebox_service.get_available_profiles()

        profiles_data = [
            {
                "id": profile.id.value,
                "name": profile.name,
                "language": profile.language,
                "description": profile.description,
            }
            for profile in profiles
        ]

        return ListVoiceProfilesOutput(profiles=profiles_data)
