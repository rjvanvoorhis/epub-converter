"""Interfaces (protocols) for audiobook conversion domain.

These interfaces define contracts for repositories and services that will be
implemented in the infrastructure layer.
"""

from pathlib import Path
from typing import Protocol

from .entities import Audiobook
from .value_objects import AudioFile, AudioProfile, TextChunk


class TTSProvider(Protocol):
    """Interface for a text-to-speech backend.

    Handles voice profile retrieval and text-to-speech generation. Concrete
    implementations adapt a specific TTS API (e.g. VoiceBox, FastKoko) to
    this common contract.
    """

    def get_available_profiles(self) -> list[AudioProfile]:
        """Get all available voice profiles from the TTS backend.

        Returns:
            List of available audio profiles.

        Raises:
            RuntimeError: If unable to connect to the TTS backend.
        """
        ...

    def generate_speech(
        self, text: str, profile_id: str, language: str, engine: str = "kokoro"
    ) -> bytes:
        """Generate speech audio for the given text.

        Args:
            text: The text to convert to speech.
            profile_id: The ID of the voice profile to use.
            language: The language code (e.g., 'en', 'es').
            engine: The speech synthesis engine to use (default: 'kokoro').
                Backends that don't distinguish between engines may ignore
                this parameter.

        Returns:
            The generated audio data in MP3 format.

        Raises:
            ValueError: If text is empty or profile_id is invalid.
            RuntimeError: If the API call fails.
        """
        ...


class TextChunker(Protocol):
    """Interface for splitting text into manageable chunks.

    Handles the chunking strategy and ensures chunks stay within limits.
    """

    def chunk_text(self, text: str, max_chunk_size: int = 45000) -> list[TextChunk]:
        """Split text into chunks.

        Args:
            text: The text to chunk.
            max_chunk_size: Maximum characters per chunk.

        Returns:
            List of text chunks in order.

        Raises:
            ValueError: If text is empty or max_chunk_size is invalid.
        """
        ...


class AudioProcessor(Protocol):
    """Interface for processing and merging audio files.

    Handles audio file format conversion, splicing, and metadata.
    """

    def get_audio_duration(self, audio_file: Path) -> float:
        """Get the duration of an audio file in seconds.

        Args:
            audio_file: Path to the audio file.

        Returns:
            Duration in seconds.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is not supported.
        """
        ...

    def merge_audio_files(self, audio_files: list[Path], output_path: Path) -> None:
        """Merge multiple audio files into a single file.

        Files are merged in the order provided.

        Args:
            audio_files: List of audio file paths to merge.
            output_path: Path where the merged audio will be saved.

        Raises:
            FileNotFoundError: If any input file does not exist.
            ValueError: If audio_files is empty.
            RuntimeError: If the merge operation fails.
        """
        ...


class AudiobookRepository(Protocol):
    """Interface for persisting and retrieving audiobooks.

    Abstracts storage of audiobook metadata and generated files.
    """

    def save_audiobook(self, audiobook: Audiobook) -> None:
        """Save an audiobook and its metadata.

        Args:
            audiobook: The audiobook to save.

        Raises:
            RuntimeError: If save operation fails.
        """
        ...

    def get_audiobook(self, epub_path: Path) -> Audiobook | None:
        """Retrieve an audiobook by its source EPUB path.

        Args:
            epub_path: Path to the source EPUB file.

        Returns:
            The audiobook if found, None otherwise.
        """
        ...
