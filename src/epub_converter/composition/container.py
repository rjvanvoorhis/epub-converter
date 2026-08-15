"""Dependency injection container and application composition.

This module handles all dependency injection and wiring to create
fully configured use case instances.
"""

from pathlib import Path

from epub_converter.application.audiobook_conversion.use_cases import (
    ConvertEPUBToAudiobookUseCase,
    ListVoiceProfilesUseCase,
)
from epub_converter.application.epub_extraction.use_cases import (
    ExtractChapterUseCase,
    LoadEPUBUseCase,
)
from epub_converter.infrastructure.audiobook_conversion.audio_processor import (
    FFmpegAudioProcessor,
)
from epub_converter.infrastructure.audiobook_conversion.fastkoko_service import (
    FastKokoApiService,
)
from epub_converter.infrastructure.audiobook_conversion.repository import (
    AudiobookFileRepository,
)
from epub_converter.infrastructure.audiobook_conversion.voicebox_service import (
    TextChunkerService,
    VoiceBoxApiService,
)
from epub_converter.infrastructure.epub_extraction.repositories import (
    EbookLibEPUBRepository,
)
from epub_converter.presentation.cli.audiobook_conversion_commands import (
    ConvertEPUBToAudiobookCommand,
    ListVoiceProfilesCommand,
)
from epub_converter.presentation.cli.controller import CLIController
from epub_converter.presentation.cli.epub_extraction_commands import (
    ExtractChapterCommand,
    LoadEPUBCommand,
)


class Container:
    """Dependency injection container.

    Manages the creation and wiring of all application dependencies.
    """

    def __init__(
        self,
        tts_provider: str = "fastkoko",
        voicebox_url: str = "http://127.0.0.1:17493",
        fastkoko_url: str = "http://127.0.0.1:8880",
    ) -> None:
        """Initialize the container and wire dependencies.

        Args:
            tts_provider: Which TTS backend to use ('voicebox' or
                'fastkoko').
            voicebox_url: Base URL for the VoiceBox API service.
            fastkoko_url: Base URL for the FastKoko API service.

        Raises:
            ValueError: If tts_provider is not a recognized backend.
        """
        # EPUB Extraction Infrastructure
        self._epub_repository = EbookLibEPUBRepository()

        # EPUB Extraction Use Cases
        self._load_epub_use_case = LoadEPUBUseCase(self._epub_repository)
        self._extract_chapter_use_case = ExtractChapterUseCase(self._epub_repository)

        # Audiobook Conversion Infrastructure
        if tts_provider == "voicebox":
            self._tts_provider = VoiceBoxApiService(base_url=voicebox_url)
        elif tts_provider == "fastkoko":
            self._tts_provider = FastKokoApiService(base_url=fastkoko_url)
        else:
            raise ValueError(
                f"Unknown tts_provider: {tts_provider!r} (expected 'voicebox' or 'fastkoko')"
            )
        self._text_chunker = TextChunkerService()
        self._audio_processor = FFmpegAudioProcessor()
        self._audiobook_repository = AudiobookFileRepository(
            Path.home() / ".epub-converter" / "audiobooks"
        )

        # Audiobook Conversion Use Cases
        self._convert_audiobook_use_case = ConvertEPUBToAudiobookUseCase(
            epub_repository=self._epub_repository,
            tts_provider=self._tts_provider,
            text_chunker=self._text_chunker,
            audio_processor=self._audio_processor,
            audiobook_repository=self._audiobook_repository,
        )
        self._list_voices_use_case = ListVoiceProfilesUseCase(
            tts_provider=self._tts_provider
        )

        # CLI Controller
        self._cli_controller = CLIController()
        self._setup_cli_commands()

    def _setup_cli_commands(self) -> None:
        """Set up and register all CLI commands."""
        # EPUB Extraction Commands
        load_epub_cmd = LoadEPUBCommand(self._load_epub_use_case)
        extract_chapter_cmd = ExtractChapterCommand(self._extract_chapter_use_case)

        self._cli_controller.register_command(load_epub_cmd)
        self._cli_controller.register_command(extract_chapter_cmd)

        # Audiobook Conversion Commands
        convert_audiobook_cmd = ConvertEPUBToAudiobookCommand(
            self._convert_audiobook_use_case
        )
        list_voices_cmd = ListVoiceProfilesCommand(self._list_voices_use_case)

        self._cli_controller.register_command(convert_audiobook_cmd)
        self._cli_controller.register_command(list_voices_cmd)

    @property
    def cli_controller(self) -> CLIController:
        """Get the CLI controller.

        Returns:
            The configured CLI controller.
        """
        return self._cli_controller

    @property
    def load_epub_use_case(self) -> LoadEPUBUseCase:
        """Get the load EPUB use case.

        Returns:
            The configured use case.
        """
        return self._load_epub_use_case

    @property
    def convert_audiobook_use_case(self) -> ConvertEPUBToAudiobookUseCase:
        """Get the convert EPUB to audiobook use case.

        Returns:
            The configured use case.
        """
        return self._convert_audiobook_use_case

    @property
    def extract_chapter_use_case(self) -> ExtractChapterUseCase:
        """Get the extract chapter use case.

        Returns:
            The configured use case.
        """
        return self._extract_chapter_use_case

    @property
    def list_voice_profiles_use_case(self) -> ListVoiceProfilesUseCase:
        """Get the list voice profiles use case.

        Returns:
            The configured use case.
        """
        return self._list_voices_use_case
