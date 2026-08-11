"""Interfaces (protocols) for audiobook conversion application layer.

These interfaces define contracts for use cases.
"""

from typing import Protocol

from .dtos import (
    ConvertEPUBToAudiobookInput,
    ConvertEPUBToAudiobookOutput,
    ListVoiceProfilesOutput,
)


class IConvertEPUBToAudiobookUseCase(Protocol):
    """Interface for converting EPUB to audiobook use case."""

    def execute(
        self, input_dto: ConvertEPUBToAudiobookInput
    ) -> ConvertEPUBToAudiobookOutput:
        """Convert an EPUB file to an audiobook.

        Args:
            input_dto: Input containing EPUB path, output path, and voice settings.

        Returns:
            Output with generated audiobook details.

        Raises:
            ValueError: If input is invalid.
            RuntimeError: If conversion fails.
        """
        ...


class IListVoiceProfilesUseCase(Protocol):
    """Interface for listing available voice profiles."""

    def execute(self) -> ListVoiceProfilesOutput:
        """Get all available voice profiles.

        Returns:
            Output containing list of available profiles.

        Raises:
            RuntimeError: If unable to retrieve profiles.
        """
        ...
