"""Infrastructure implementations for audiobook conversion."""

import json
import time
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

    Generation is asynchronous: ``POST /generate`` enqueues the job and
    immediately returns a ``GenerationResponse`` containing an ``id`` and an
    in-progress ``status`` (e.g. ``queued``, ``loading_model``,
    ``generating``). The service then watches
    ``GET /generate/{id}/status`` (a server-sent-events stream of status
    snapshots) until a terminal status is reached, and finally downloads the
    finished audio via ``GET /history/{id}/export-audio``.
    """

    _SUCCESS_STATUSES = frozenset({"completed"})
    _FAILURE_STATUSES = frozenset({"failed", "error", "cancelled"})
    _TERMINAL_STATUSES = _SUCCESS_STATUSES | _FAILURE_STATUSES

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:17493",
        request_timeout: float = 30,
        generation_timeout: float = 1800,
        status_read_timeout: float = 30,
    ) -> None:
        """Initialize the VoiceBox service.

        Args:
            base_url: The base URL of the VoiceBox API.
            request_timeout: Timeout (seconds) for quick request/response
                calls (enqueueing a generation, exporting finished audio).
            generation_timeout: Maximum time (seconds) to wait for a
                generation to reach a terminal status before giving up.
            status_read_timeout: Per-read timeout (seconds) while streaming
                the status endpoint; the connection is transparently
                reopened if it goes quiet without exceeding
                ``generation_timeout``.
        """
        self._base_url = base_url
        self._timeout = request_timeout
        self._generation_timeout = generation_timeout
        self._status_read_timeout = status_read_timeout

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

    def generate_speech(
        self, text: str, profile_id: str, language: str, engine: str = "kokoro"
    ) -> bytes:
        """Generate speech audio for the given text.

        Enqueues the generation, waits for it to complete, and downloads the
        resulting audio.

        Args:
            text: The text to convert to speech.
            profile_id: The ID of the voice profile to use.
            language: The language code (e.g., 'en', 'es').
            engine: The speech synthesis engine to use (default: 'kokoro').

        Returns:
            The generated audio data in MP3 format.

        Raises:
            ValueError: If text is empty or profile_id is invalid.
            RuntimeError: If the API call fails, the generation fails, or it
                does not complete within the configured timeout.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        if not profile_id or not profile_id.strip():
            raise ValueError("profile_id cannot be empty")

        generation = self._start_generation(text, profile_id, language, engine)

        generation_id = generation.get("id")
        if not generation_id:
            raise RuntimeError(f"VoiceBox did not return a generation id: {generation}")

        status = generation.get("status")
        error = generation.get("error")
        if status not in self._TERMINAL_STATUSES:
            status, error = self._await_generation_completion(generation_id)

        if status not in self._SUCCESS_STATUSES:
            raise RuntimeError(
                f"VoiceBox generation {generation_id} did not complete successfully "
                f"(status={status!r}, error={error!r})"
            )

        return self._export_audio(generation_id)

    def _start_generation(
        self, text: str, profile_id: str, language: str, engine: str
    ) -> dict:
        """POST /generate to enqueue a generation and return the raw response."""
        payload = {
            "text": text,
            "profile_id": profile_id,
            "language": language,
            "engine": engine,
        }
        try:
            response = requests.post(
                f"{self._base_url}/generate",
                json=payload,
                timeout=self._timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to start speech generation: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"VoiceBox returned an invalid generation response: {e}")

    def _await_generation_completion(
        self, generation_id: str
    ) -> tuple[str, str | None]:
        """Watch GET /generate/{id}/status until a terminal status is reached.

        The endpoint is a server-sent-events stream of status snapshots. The
        connection is reopened on transient read timeouts/drops until a
        terminal status arrives or ``generation_timeout`` elapses.
        """
        deadline = time.monotonic() + self._generation_timeout
        status = "unknown"
        error: str | None = None

        while time.monotonic() < deadline:
            try:
                with requests.get(
                    f"{self._base_url}/generate/{generation_id}/status",
                    stream=True,
                    timeout=(10, self._status_read_timeout),
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines(decode_unicode=True):
                        if not line or not line.startswith("data:"):
                            continue
                        try:
                            event = json.loads(line[len("data:"):].strip())
                        except json.JSONDecodeError:
                            continue
                        status = event.get("status", status)
                        error = event.get("error")
                        if status in self._TERMINAL_STATUSES:
                            return status, error
                        if time.monotonic() >= deadline:
                            break
            except requests.exceptions.HTTPError as e:
                raise RuntimeError(
                    f"Failed to poll status for generation {generation_id}: {e}"
                )
            except requests.RequestException:
                # Transient stream drop/read timeout; retry until deadline.
                continue

        raise RuntimeError(
            f"Timed out waiting for VoiceBox generation {generation_id} to "
            f"complete (last known status: {status!r})"
        )

    def _export_audio(self, generation_id: str) -> bytes:
        """GET /history/{id}/export-audio to download the finished audio."""
        try:
            response = requests.get(
                f"{self._base_url}/history/{generation_id}/export-audio",
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            raise RuntimeError(
                f"Failed to export audio for generation {generation_id}: {e}"
            )


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
