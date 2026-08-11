"""Repository implementations for audiobook persistence."""

import json
from pathlib import Path

from epub_converter.domain.audiobook_conversion.entities import Audiobook
from epub_converter.domain.audiobook_conversion.value_objects import AudioProfileId


class AudiobookFileRepository:
    """File-based repository for storing audiobook metadata and files.

    Stores audiobook information in JSON metadata files alongside the audio files.
    """

    def __init__(self, storage_dir: Path) -> None:
        """Initialize the repository.

        Args:
            storage_dir: Directory where audiobook files and metadata are stored.
        """
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_dir = self._storage_dir / ".metadata"
        self._metadata_dir.mkdir(exist_ok=True)

    def save_audiobook(self, audiobook: Audiobook) -> None:
        """Save an audiobook and its metadata.

        Args:
            audiobook: The audiobook to save.

        Raises:
            RuntimeError: If save operation fails.
        """
        try:
            # Create metadata
            metadata = {
                "epub_source": str(audiobook.epub_file.file_path),
                "output_path": str(audiobook.output_path),
                "profile_id": audiobook.profile_id.value,
                "total_duration_seconds": audiobook.get_total_duration(),
                "chapter_count": len(audiobook.chapter_audiobooks),
                "is_complete": audiobook.is_complete(),
                "final_audio_path": str(audiobook.final_audio_path),
                "chapters": [
                    {
                        "index": ch.chapter_index,
                        "title": ch.chapter_title,
                        "duration_seconds": ch.get_total_duration(),
                        "audio_file_count": len(ch.audio_files),
                    }
                    for ch in audiobook.chapter_audiobooks
                ],
            }

            # Save metadata to file
            metadata_file = self._metadata_dir / f"{audiobook.output_path.stem}.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

        except (IOError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to save audiobook metadata: {e}") from e

    def get_audiobook(self, epub_path: Path) -> Audiobook | None:
        """Retrieve an audiobook by its source EPUB path.

        Note: This is a simplified implementation. In a real system,
        you might query a database or use more sophisticated lookups.

        Args:
            epub_path: Path to the source EPUB file.

        Returns:
            The audiobook if found, None otherwise.
        """
        # Look for metadata files that reference this EPUB
        for metadata_file in self._metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                if Path(metadata.get("epub_source", "")) == epub_path:
                    # Found matching audiobook
                    # In a real implementation, reconstruct the Audiobook entity
                    return None  # Simplified for now
            except (IOError, json.JSONDecodeError):
                continue

        return None
