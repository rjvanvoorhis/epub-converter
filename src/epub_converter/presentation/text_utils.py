"""Utility functions for text processing."""

from html.parser import HTMLParser
from typing import Optional


class HTMLStripper(HTMLParser):
    """HTML parser that extracts plain text from HTML content."""

    def __init__(self) -> None:
        """Initialize the HTML stripper."""
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text_parts: list[str] = []

    def handle_data(self, data: str) -> None:
        """Handle text data from HTML."""
        if data.strip():
            self.text_parts.append(data.strip())

    def get_text(self) -> str:
        """Get the extracted plain text."""
        return "\n".join(self.text_parts)


def normalize_unicode_to_ascii(text: str) -> str:
    """Convert Unicode characters to ASCII equivalents.

    This converts smart quotes, dashes, and other Unicode characters
    to their ASCII equivalents for cleaner text extraction.

    Args:
        text: Text to normalize

    Returns:
        Text with Unicode characters converted to ASCII
    """
    if not text:
        return text

    # Character mappings: Unicode -> ASCII
    replacements = {
        # Smart quotes
        "\u201c": '"',  # Left double quotation mark
        "\u201d": '"',  # Right double quotation mark
        "\u2018": "'",  # Left single quotation mark
        "\u2019": "'",  # Right single quotation mark
        "\u2032": "'",  # Prime
        "\u2033": '"',  # Double prime
        # Dashes
        "\u2013": "-",  # En dash
        "\u2014": "-",  # Em dash
        "\u2015": "-",  # Horizontal bar
        # Spaces and whitespace
        "\u200b": "",   # Zero-width space
        "\u200c": "",   # Zero-width non-joiner
        "\u200d": "",   # Zero-width joiner
        "\u2060": "",   # Word joiner
        "\u00a0": " ",  # Non-breaking space
        "\u2009": " ",  # Thin space
        "\u200a": " ",  # Hair space
        # Other common Unicode punctuation
        "\u2026": "...", # Ellipsis
        "\u2022": "-",   # Bullet
        # Hyphenation and word breaks
        "\u00ad": "",    # Soft hyphen
        "\u2010": "-",   # Hyphen
        "\u2011": "-",   # Non-breaking hyphen
        # Accented characters simplified
        "\u00e9": "e",   # é
        "\u00e8": "e",   # è
        "\u00ea": "e",   # ê
        "\u00fc": "u",   # ü
    }

    result = text
    for unicode_char, ascii_char in replacements.items():
        result = result.replace(unicode_char, ascii_char)

    return result


def strip_html_tags(html_content: str) -> str:
    """Strip HTML tags from content, returning only plain text.

    Args:
        html_content: HTML content to strip

    Returns:
        Plain text with HTML tags removed and Unicode normalized
    """
    if not html_content:
        return ""

    stripper = HTMLStripper()
    try:
        stripper.feed(html_content)
        text = stripper.get_text()
        # Normalize Unicode characters to ASCII
        text = normalize_unicode_to_ascii(text)
        return text
    except Exception:
        # If parsing fails, return normalized original content
        return normalize_unicode_to_ascii(html_content)
