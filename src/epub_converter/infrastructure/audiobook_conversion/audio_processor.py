"""Audio processing infrastructure for merging and analyzing audio files."""

import subprocess
import tempfile
from pathlib import Path


class FFmpegAudioProcessor:
    """Concrete audio processor using FFmpeg for file operations.

    Handles merging multiple audio files and retrieving duration information.
    """

    def __init__(self) -> None:
        """Initialize the audio processor.

        Raises:
            RuntimeError: If ffmpeg is not available in the system.
        """
        self._verify_ffmpeg_available()

    def _verify_ffmpeg_available(self) -> None:
        """Verify that ffmpeg is installed and available.

        Raises:
            RuntimeError: If ffmpeg is not found.
        """
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(
                "ffmpeg is not installed or not in PATH. "
                "Install it to use audio processing features."
            ) from e

    def get_audio_duration(self, audio_file: Path) -> float:
        """Get the duration of an audio file in seconds.

        Args:
            audio_file: Path to the audio file.

        Returns:
            Duration in seconds.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is not supported.
            RuntimeError: If ffmpeg fails.
        """
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1:noprint_wrappers=1",
                    str(audio_file),
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            duration = float(result.stdout.strip())
            return duration
        except (subprocess.CalledProcessError, ValueError, FileNotFoundError) as e:
            raise RuntimeError(f"Failed to get audio duration: {e}") from e

    def merge_audio_files(self, audio_files: list[Path], output_path: Path) -> None:
        """Merge one or more audio files into a single file.

        Files are merged in the order provided. Creates a temporary concat file
        for ffmpeg to process. Inputs are re-encoded (not stream-copied) when
        the output is MP3, since VoiceBox may return other formats (e.g. WAV)
        that can't be copied directly into an MP3 container.

        Args:
            audio_files: List of audio file paths to merge.
            output_path: Path where the merged audio will be saved.

        Raises:
            FileNotFoundError: If any input file does not exist.
            ValueError: If audio_files is empty.
            RuntimeError: If the merge operation fails.
        """
        if not audio_files:
            raise ValueError("audio_files cannot be empty")

        # Verify all files exist
        for audio_file in audio_files:
            if not audio_file.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")

        # Create a temporary concat file for ffmpeg
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as concat_file:
            for audio_file in audio_files:
                # Escape backslashes in Windows paths for ffmpeg
                file_path = str(audio_file.resolve()).replace("\\", "/")
                concat_file.write(f"file '{file_path}'\n")
            concat_path = concat_file.name

        codec_args = (
            ["-c:a", "libmp3lame", "-q:a", "2"]
            if output_path.suffix.lower() == ".mp3"
            else ["-c", "copy"]
        )

        try:
            # Use ffmpeg to concatenate the files, transcoding as needed
            subprocess.run(
                [
                    "ffmpeg",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    concat_path,
                    *codec_args,
                    "-y",
                    str(output_path),
                ],
                capture_output=True,
                check=True,
                timeout=300,  # 5 minutes max
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg merge failed: {e.stderr.decode()}") from e
        finally:
            # Clean up temp file
            Path(concat_path).unlink(missing_ok=True)
