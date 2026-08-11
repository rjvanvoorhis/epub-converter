"""Entities for audiobook conversion domain.

Entities have identity and mutable state over their lifetime.
"""

from dataclasses import dataclass, field
from pathlib import Path

from ..epub_extraction.entities import EPUBFile
from .value_objects import AudioFile, AudioProfile, AudioProfileId, TextChunk


@dataclass
class ChapterAudiobook:
    """Represents the audio version of a single chapter.

    Contains multiple audio files (one per text chunk) that will be
    spliced together into the final chapter audio.
    """

    chapter_index: int
    chapter_title: str
    audio_files: list[AudioFile] = field(default_factory=list)
    profile_id: AudioProfileId = field(default_factory=lambda: AudioProfileId(""))

    def add_audio_file(self, audio_file: AudioFile) -> None:
        """Add an audio file for this chapter.

        Args:
            audio_file: The audio file to add.

        Raises:
            ValueError: If files are not added in sequence order.
        """
        expected_sequence = len(self.audio_files)
        if audio_file.chunk_sequence != expected_sequence:
            raise ValueError(
                f"Expected sequence {expected_sequence}, "
                f"got {audio_file.chunk_sequence}"
            )
        self.audio_files.append(audio_file)

    def get_total_duration(self) -> float:
        """Get total audio duration in seconds."""
        return sum(f.duration_seconds for f in self.audio_files)

    def is_complete(self) -> bool:
        """Check if all audio files have been added and validated."""
        return len(self.audio_files) > 0 and all(
            Path(f.file_path).exists() for f in self.audio_files
        )


@dataclass
class Audiobook:
    """Aggregate root for audiobook conversion domain.

    Represents the complete audiobook generated from an EPUB file.
    """

    epub_file: EPUBFile
    profile_id: AudioProfileId
    output_path: Path
    chapter_audiobooks: list[ChapterAudiobook] = field(default_factory=list)
    final_audio_path: Path = field(default_factory=Path)

    def add_chapter_audiobook(self, chapter_audiobook: ChapterAudiobook) -> None:
        """Add a chapter audiobook to this audiobook.

        Args:
            chapter_audiobook: The chapter audiobook to add.

        Raises:
            ValueError: If chapter already exists.
        """
        if any(
            c.chapter_index == chapter_audiobook.chapter_index
            for c in self.chapter_audiobooks
        ):
            raise ValueError(
                f"Chapter {chapter_audiobook.chapter_index} already exists"
            )
        self.chapter_audiobooks.append(chapter_audiobook)

    def get_chapter_audiobook(self, chapter_index: int) -> ChapterAudiobook | None:
        """Retrieve a chapter audiobook by index.

        Args:
            chapter_index: The index of the chapter.

        Returns:
            The chapter audiobook if found, None otherwise.
        """
        for chapter_audiobook in self.chapter_audiobooks:
            if chapter_audiobook.chapter_index == chapter_index:
                return chapter_audiobook
        return None

    def get_total_duration(self) -> float:
        """Get total audiobook duration in seconds."""
        return sum(c.get_total_duration() for c in self.chapter_audiobooks)

    def is_complete(self) -> bool:
        """Check if all chapters have been processed.

        Returns:
            True if all chapters are complete and final audio exists.
        """
        if not self.chapter_audiobooks:
            return False

        all_chapters_complete = all(c.is_complete() for c in self.chapter_audiobooks)
        final_exists = self.final_audio_path.exists()

        return all_chapters_complete and final_exists

    def set_final_audio_path(self, path: Path) -> None:
        """Set the final output path for the complete audiobook.

        Args:
            path: Path to the final merged audio file.
        """
        self.final_audio_path = path
