"""CLI commands for audiobook conversion feature.

Commands are framework-agnostic and define how to interact with use cases
and present results to the user.
"""

from pathlib import Path
from typing import Any

from epub_converter.application.audiobook_conversion.use_cases import (
    ConvertEPUBToAudiobookUseCase,
    ListVoiceProfilesUseCase,
)
from epub_converter.application.audiobook_conversion.dtos import (
    ConvertEPUBToAudiobookInput,
)


class ConvertEPUBToAudiobookCommand:
    """Command to convert EPUB file to audiobook."""

    def __init__(self, use_case: ConvertEPUBToAudiobookUseCase) -> None:
        """Initialize the command.

        Args:
            use_case: The EPUB to audiobook conversion use case.
        """
        self._use_case = use_case

    @property
    def name(self) -> str:
        """Return the command name."""
        return "convert-epub-to-audiobook"

    @property
    def description(self) -> str:
        """Return the command description."""
        return "Convert an EPUB file to an audiobook in MP3 format"

    def execute(self, *args: Any, **kwargs: Any) -> str:
        """Execute the command.

        Args:
            *args: Positional arguments (not used).
            **kwargs: Named arguments:
                - input_path: Path to an EPUB file, or to a directory of
                  chapter .txt files (the output of the extract-chapters
                  command)
                - output_file: Path for output MP3 file
                - voice_profile_id: ID of voice profile to use
                - language: Language code (default: 'en')
                - chunk_size: Max characters per chunk (default: 45000)

        Returns:
            Formatted output string for the user.

        Raises:
            ValueError: If arguments are invalid.
            RuntimeError: If execution fails.
        """
        try:
            input_path = Path(kwargs.get("input_path"))
            output_file = Path(kwargs.get("output_file"))
            voice_profile_id = kwargs.get("voice_profile_id")
            language = kwargs.get("language", "en")
            chunk_size = int(kwargs.get("chunk_size", 45000))

            if not voice_profile_id:
                return "Error: voice_profile_id is required"

            input_dto = ConvertEPUBToAudiobookInput(
                epub_file_path=None if input_path.is_dir() else input_path,
                text_directory_path=input_path if input_path.is_dir() else None,
                output_file_path=output_file,
                voice_profile_id=voice_profile_id,
                language=language,
                chunk_size=chunk_size,
            )

            output_dto = self._use_case.execute(input_dto)

            return (
                f"Successfully converted EPUB to audiobook\n"
                f"Output: {output_dto.output_file_path}\n"
                f"Duration: {output_dto.total_duration_seconds:.1f} seconds\n"
                f"Chapters: {output_dto.chapter_count}\n"
                f"Voice Profile: {output_dto.voice_profile_id}"
            )

        except ValueError as e:
            return f"Error: Invalid input - {e}"
        except RuntimeError as e:
            return f"Error: Conversion failed - {e}"


class ListVoiceProfilesCommand:
    """Command to list available voice profiles."""

    def __init__(self, use_case: ListVoiceProfilesUseCase) -> None:
        """Initialize the command.

        Args:
            use_case: The list voice profiles use case.
        """
        self._use_case = use_case

    @property
    def name(self) -> str:
        """Return the command name."""
        return "list-voice-profiles"

    @property
    def description(self) -> str:
        """Return the command description."""
        return "List all available voice profiles from VoiceBox"

    def execute(self, *args: Any, **kwargs: Any) -> str:
        """Execute the command.

        Args:
            *args: Positional arguments (not used).
            **kwargs: Named arguments (not used).

        Returns:
            Formatted output string listing available profiles.

        Raises:
            RuntimeError: If execution fails.
        """
        try:
            output_dto = self._use_case.execute()

            if not output_dto.profiles:
                return "No voice profiles available"

            lines = ["Available Voice Profiles:"]
            lines.append("=" * 60)

            for profile in output_dto.profiles:
                lines.append(f"ID: {profile['id']}")
                lines.append(f"Name: {profile['name']}")
                lines.append(f"Language: {profile['language']}")
                lines.append(f"Description: {profile['description']}")
                lines.append("-" * 60)

            return "\n".join(lines)

        except RuntimeError as e:
            return f"Error: Failed to list profiles - {e}"
