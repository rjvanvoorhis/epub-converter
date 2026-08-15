"""FastKoko TTS backend infrastructure implementation."""

import requests

from epub_converter.domain.audiobook_conversion.value_objects import (
    AudioProfile,
    AudioProfileId,
)

# FastKoko voice names are prefixed with a language/gender code (e.g.
# "af_bella" is American English/female, "bf_emma" is British English/
# female). The voices endpoint only returns bare names, so this maps the
# prefix to a language code for AudioProfile.language.
_VOICE_PREFIX_LANGUAGES = {
    "af": "en", "am": "en",  # American English
    "bf": "en", "bm": "en",  # British English
    "jf": "ja", "jm": "ja",  # Japanese
    "zf": "zh", "zm": "zh",  # Mandarin Chinese
    "ef": "es", "em": "es",  # Spanish
    "ff": "fr",              # French
    "hf": "hi", "hm": "hi",  # Hindi
    "if": "it", "im": "it",  # Italian
    "pf": "pt", "pm": "pt",  # Brazilian Portuguese
}


class FastKokoApiService:
    """Concrete TTS provider implementation backed by a FastKoko server.

    Unlike VoiceBox, FastKoko exposes a synchronous, OpenAI-compatible
    speech API: ``POST /v1/audio/speech`` returns the generated audio
    directly (no job id/status polling), and ``GET /v1/audio/voices`` lists
    the available voice names.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8880",
        request_timeout: float = 120,
    ) -> None:
        """Initialize the FastKoko service.

        Args:
            base_url: The base URL of the FastKoko API.
            request_timeout: Timeout (seconds) for the speech generation
                request.
        """
        self._base_url = base_url
        self._timeout = request_timeout

    def get_available_profiles(self) -> list[AudioProfile]:
        """Get all available voices from FastKoko.

        Returns:
            List of available audio profiles.

        Raises:
            RuntimeError: If unable to connect to the FastKoko server.
        """
        try:
            response = requests.get(f"{self._base_url}/v1/audio/voices", timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to retrieve voice profiles: {e}")

        voices = data.get("voices", []) if isinstance(data, dict) else data

        # Each entry is normally {"id": ..., "name": ...}, but tolerate a
        # bare voice-name string too.
        voice_names = [
            voice["name"] if isinstance(voice, dict) else voice for voice in voices
        ]

        return [
            AudioProfile(
                id=AudioProfileId(name),
                name=name,
                language=_VOICE_PREFIX_LANGUAGES.get(name.split("_", 1)[0], "en"),
                description=f"FastKoko voice: {name}",
            )
            for name in voice_names
        ]

    def generate_speech(
        self, text: str, profile_id: str, language: str, engine: str = "kokoro"
    ) -> bytes:
        """Generate speech audio for the given text.

        FastKoko's speech endpoint returns audio synchronously in a single
        request/response (no job polling like VoiceBox).

        Args:
            text: The text to convert to speech.
            profile_id: The FastKoko voice name to use (e.g. 'af_bella').
            language: Unused; a FastKoko voice determines its own language.
            engine: Unused; a FastKoko server only ever serves one model.
                Present for interface compatibility with other providers.

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
            response = requests.post(
                f"{self._base_url}/v1/audio/speech",
                json={
                    "input": text,
                    "voice": profile_id,
                    # mp3 (not FastKoko's default "pcm") so the resulting
                    # file is self-describing for downstream ffmpeg/ffprobe
                    # merging and duration lookups.
                    "response_format": "mp3",
                },
                timeout=self._timeout,
                stream=True,
            )
            response.raise_for_status()
            return b"".join(
                chunk for chunk in response.iter_content(chunk_size=8192) if chunk
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to generate speech: {e}")
