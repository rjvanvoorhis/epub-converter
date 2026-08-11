"""Infrastructure implementations for audiobook conversion."""

import json
from pathlib import Path

import requests

from epub_converter.domain.audiobook_conversion.value_objects import (
    AudioProfile,
    AudioProfileId,
    TextChunk,
)


class VoiceBoxApiService:
    """Concrete implementation of VoiceBox API service.

    Communicates with VoiceBox API to retrieve profiles and generate speech.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:17493") -> None:
        """Initialize the VoiceBox service.

        Args:
            base_url: The base URL of the VoiceBox API.
        """
        self._base_url = base_url
        self._timeout = 300  # 5 minutes for long audio generation

    def get_available_profiles(self) -> list[AudioProfile]:
        """Get all available voice profiles from VoiceBox.

        Returns:
            List of available audio profiles.

        Raises:
            RuntimeError: If unable to connect to VoiceBox service.
        """
        try:
            response = requests.get(f"{self._base_url}/profiles", timeout=10)
            response.raise_for_status()
            profiles_data = response.json()

            profiles = []
            if isinstance(profiles_data, list):
                for profile_data in profiles_data:
                    profile = AudioProfile(
                        id=AudioProfileId(profile_data.get("id", "")),
                        name=profile_data.get("name", ""),
                        language=profile_data.get("language", "en"),
                        description=profile_data.get("description", ""),
                    )
                    profiles.append(profile)
            elif isinstance(profiles_data, dict) and "profiles" in profiles_data:
                for profile_data in profiles_data["profiles"]:
                    profile = AudioProfile(
                        id=AudioProfileId(profile_data.get("id", "")),
                        name=profile_data.get("name", ""),
                        language=profile_data.get("language", "en"),
                        description=profile_data.get("description", ""),
                    )
                    profiles.append(profile)

            return profiles
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to retrieve voice profiles: {e}")

    def generate_speech(self, text: str, profile_id: str, language: str) -> bytes:
        """Generate speech audio for the given text.

        Args:
            text: The text to convert to speech.
            profile_id: The ID of the voice profile to use.
            language: The language code (e.g., 'en', 'es').

        Returns:
            The generated audio data in MP3 format.

        Raises:
            ValueError: If text is empty or profile_id is invalid.
            RuntimeError: If the API call fails.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        if not profile_id or not profile_id.strip():
            raise ValueError("profile_id cannot be empty")

        try:
            payload = {
                "text": text,
                "profile_id": profile_id,
                "language": language,
            }

            response = requests.post(
                f"{self._base_url}/generate",
                json=payload,
                timeout=self._timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            # If response is JSON, it might contain the audio data in base64
            # or a file path; if it's binary, it's direct MP3 data
            try:
                response_data = response.json()
                if isinstance(response_data, dict) and "audio_data" in response_data:
                    import base64

                    return base64.b64decode(response_data["audio_data"])
                elif isinstance(response_data, dict) and "error" in response_data:
                    raise RuntimeError(f"VoiceBox error: {response_data['error']}")
            except json.JSONDecodeError:
                # Response is binary audio data
                return response.content

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to generate speech: {e}")


class TextChunkerService:
    """Concrete implementation of text chunking service.

    Splits text into chunks that fit within size limits, respecting word boundaries.
    """

    def chunk_text(self, text: str, max_chunk_size: int = 45000) -> list[TextChunk]:
        """Split text into chunks.

        Attempts to break at sentence or word boundaries to avoid cutting
        in the middle of words when possible.

        Args:
            text: The text to chunk.
            max_chunk_size: Maximum characters per chunk.

        Returns:
            List of text chunks in order.

        Raises:
            ValueError: If text is empty or max_chunk_size is invalid.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        if max_chunk_size <= 0:
            raise ValueError("max_chunk_size must be positive")

        chunks = []
        sequence = 0
        start_char = 0

        while start_char < len(text):
            end_char = min(start_char + max_chunk_size, len(text))

            # If we're not at the end, try to break at a word boundary
            if end_char < len(text):
                # Look for the last space within the chunk
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

        return (
            chunks
            if chunks
            else [
                TextChunk(
                    sequence=0,
                    text=text.strip(),
                    start_char=0,
                    end_char=len(text),
                )
            ]
        )
