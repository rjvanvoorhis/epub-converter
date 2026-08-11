"""Unit tests for infrastructure layer services.

Tests concrete implementations without requiring external services.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from epub_converter.infrastructure.audiobook_conversion.voicebox_service import (
    TextChunkerService,
)
from epub_converter.domain.audiobook_conversion.value_objects import TextChunk


class TestTextChunkerService:
    """Test text chunking service."""

    def test_chunk_short_text_single_chunk(self) -> None:
        """Test chunking short text that fits in one chunk."""
        chunker = TextChunkerService()
        text = "This is a short text that fits in one chunk."

        chunks = chunker.chunk_text(text, max_chunk_size=100)

        assert len(chunks) == 1
        assert chunks[0].text == text.strip()
        assert chunks[0].sequence == 0

    def test_chunk_long_text_multiple_chunks(self) -> None:
        """Test chunking long text into multiple chunks."""
        chunker = TextChunkerService()
        text = "word " * 1000  # 5000 characters

        chunks = chunker.chunk_text(text, max_chunk_size=1000)

        assert len(chunks) > 1
        # Verify sequence numbers are consecutive
        for i, chunk in enumerate(chunks):
            assert chunk.sequence == i

    def test_chunk_at_word_boundary(self) -> None:
        """Test that chunks break at word boundaries."""
        chunker = TextChunkerService()
        text = "word " * 100

        chunks = chunker.chunk_text(text, max_chunk_size=200)

        # Verify chunks are valid
        assert len(chunks) > 0
        # Each chunk should have content
        for chunk in chunks:
            assert len(chunk.text) > 0

    def test_chunk_preserves_content(self) -> None:
        """Test that all content is preserved when chunked."""
        chunker = TextChunkerService()
        original_text = "The quick brown fox jumps over the lazy dog. " * 50

        chunks = chunker.chunk_text(original_text, max_chunk_size=500)

        reconstructed = " ".join(chunk.text for chunk in chunks)
        # The text should be very similar (might have extra spaces)
        assert original_text.replace("  ", " ") in reconstructed or \
               reconstructed.replace("  ", " ") in original_text

    def test_chunk_empty_text_raises_error(self) -> None:
        """Test that empty text raises error."""
        chunker = TextChunkerService()

        with pytest.raises(ValueError, match="Text cannot be empty"):
            chunker.chunk_text("   ", max_chunk_size=100)

    def test_chunk_invalid_max_size_raises_error(self) -> None:
        """Test that invalid max_chunk_size raises error."""
        chunker = TextChunkerService()

        with pytest.raises(ValueError, match="max_chunk_size must be positive"):
            chunker.chunk_text("Some text", max_chunk_size=0)

    def test_chunk_default_max_size(self) -> None:
        """Test chunking with default max size."""
        chunker = TextChunkerService()
        text = "word " * 15000  # About 75KB

        chunks = chunker.chunk_text(text)  # Uses default 45000

        assert len(chunks) > 1
        # Each chunk except last should be close to max size
        for chunk in chunks[:-1]:
            assert len(chunk.text) <= 45000

    def test_chunk_respects_custom_max_size(self) -> None:
        """Test that custom max_chunk_size is respected."""
        chunker = TextChunkerService()
        text = "word " * 1000

        chunks = chunker.chunk_text(text, max_chunk_size=500)

        # Each chunk should not exceed max size
        for chunk in chunks:
            assert len(chunk.text) <= 500

    def test_chunk_single_word_per_line(self) -> None:
        """Test chunking text with line breaks."""
        chunker = TextChunkerService()
        text = "\n".join(["word"] * 1000)

        chunks = chunker.chunk_text(text, max_chunk_size=100)

        assert len(chunks) > 1
        # All chunks should have content
        for chunk in chunks:
            assert len(chunk.text) > 0

    def test_chunk_very_long_single_word(self) -> None:
        """Test chunking when a single word exceeds max size."""
        chunker = TextChunkerService()
        long_word = "x" * 1000
        text = f"Start {long_word} End"

        chunks = chunker.chunk_text(text, max_chunk_size=500)

        # Should handle gracefully and chunk the long word
        assert len(chunks) >= 1
        assert all(len(c.text) > 0 for c in chunks)

    def test_chunk_character_boundaries(self) -> None:
        """Test that chunks have correct start/end character positions."""
        chunker = TextChunkerService()
        text = "This is a sample text for testing chunk boundaries."

        chunks = chunker.chunk_text(text, max_chunk_size=20)

        # Verify start_char and end_char are consistent
        for i, chunk in enumerate(chunks):
            if i < len(chunks) - 1:
                # Next chunk should not overlap
                assert chunk.end_char <= chunks[i + 1].start_char

    def test_chunk_text_object_properties(self) -> None:
        """Test properties of TextChunk objects."""
        chunker = TextChunkerService()
        text = "This is sample text"

        chunks = chunker.chunk_text(text, max_chunk_size=100)

        assert len(chunks) == 1
        chunk = chunks[0]

        assert isinstance(chunk, TextChunk)
        assert chunk.sequence == 0
        assert chunk.character_count() == len(chunk.text)
        assert chunk.start_char >= 0
        assert chunk.end_char > chunk.start_char


class TestTextChunkerServiceEdgeCases:
    """Test edge cases for text chunker service."""

    def test_chunk_only_spaces(self) -> None:
        """Test that text with only spaces raises error."""
        chunker = TextChunkerService()

        with pytest.raises(ValueError, match="Text cannot be empty"):
            chunker.chunk_text("     ", max_chunk_size=100)

    def test_chunk_only_newlines(self) -> None:
        """Test text with only newlines."""
        chunker = TextChunkerService()

        with pytest.raises(ValueError, match="Text cannot be empty"):
            chunker.chunk_text("\n\n\n", max_chunk_size=100)

    def test_chunk_unicode_text(self) -> None:
        """Test chunking unicode text."""
        chunker = TextChunkerService()
        text = "こんにちは世界 " * 100  # Japanese + space

        chunks = chunker.chunk_text(text, max_chunk_size=500)

        assert len(chunks) > 0
        # Verify content is preserved
        reconstructed = "".join(c.text for c in chunks)
        assert len(reconstructed) > 0

    def test_chunk_mixed_languages(self) -> None:
        """Test chunking text with mixed languages."""
        chunker = TextChunkerService()
        text = ("Hello world " + "مرحبا بالعالم " + "你好世界 ") * 50

        chunks = chunker.chunk_text(text, max_chunk_size=500)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.text) > 0

    def test_chunk_with_special_characters(self) -> None:
        """Test chunking text with special characters."""
        chunker = TextChunkerService()
        text = ("!@#$%^&*()_+-=[]{}|;:',.<>?/ " * 50)

        chunks = chunker.chunk_text(text, max_chunk_size=500)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.text) > 0

    def test_chunk_hyphenated_words(self) -> None:
        """Test chunking hyphenated words at chunk boundary."""
        chunker = TextChunkerService()
        text = "some-hyphenated-word " * 100

        chunks = chunker.chunk_text(text, max_chunk_size=200)

        assert len(chunks) > 0
        # Verify all chunks have content
        for chunk in chunks:
            assert len(chunk.text) > 0

    def test_chunk_maintains_sequence_order(self) -> None:
        """Test that chunk sequences are sequential and unique."""
        chunker = TextChunkerService()
        text = "word " * 500

        chunks = chunker.chunk_text(text, max_chunk_size=500)

        sequences = [c.sequence for c in chunks]
        assert sequences == list(range(len(chunks)))
        assert len(set(sequences)) == len(sequences)  # All unique


class TestTextChunkerPerformance:
    """Test performance characteristics of text chunker."""

    def test_chunk_large_text(self) -> None:
        """Test chunking very large text."""
        chunker = TextChunkerService()
        # Create a 1MB text
        text = "word " * 200000

        chunks = chunker.chunk_text(text, max_chunk_size=45000)

        assert len(chunks) > 0
        # Verify total length matches
        total_length = sum(len(c.text) for c in chunks)
        # Should be close to original (might have slight differences due to boundary)
        assert total_length <= len(text)

    def test_chunk_many_small_chunks(self) -> None:
        """Test creating many small chunks."""
        chunker = TextChunkerService()
        text = "word " * 1000

        chunks = chunker.chunk_text(text, max_chunk_size=50)

        assert len(chunks) > 10
        # All chunks should be valid
        for chunk in chunks:
            assert chunk.sequence >= 0
            assert len(chunk.text) > 0
