"""Interfaces (protocols) for EPUB extraction domain.

These interfaces define contracts for repositories and services that will be
implemented in the infrastructure layer.
"""

from typing import Protocol

from .entities import EPUBFile
from .value_objects import FilePath


class EPUBRepository(Protocol):
    """Interface for EPUB file repository.

    Abstracts persistence and retrieval of EPUB files.
    """

    def load(self, file_path: FilePath) -> EPUBFile:
        """Load an EPUB file from disk.

        Args:
            file_path: Path to the EPUB file.

        Returns:
            The loaded EPUB file as an aggregate root.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a valid EPUB.
        """
        ...

    def save(self, epub_file: EPUBFile, file_path: FilePath) -> None:
        """Save an EPUB file to disk.

        Args:
            epub_file: The EPUB file to save.
            file_path: Path where to save the EPUB file.
        """
        ...
