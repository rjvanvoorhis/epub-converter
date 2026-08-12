"""Utility functions for text processing."""

from html.parser import HTMLParser
from typing import Optional

# Tags whose boundaries represent real line/paragraph breaks. Text inside
# inline tags (<em>, <span>, <a>, <b>, <i>, ...) is joined with a space
# instead, since those tags routinely split a single sentence across
# multiple handle_data() calls without indicating any actual line break.
_BLOCK_TAGS = frozenset(
    {
        "p", "div", "br", "hr",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "ul", "ol", "blockquote",
        "tr", "table", "section", "article", "header", "footer",
    }
)


class HTMLStripper(HTMLParser):
    """HTML parser that extracts plain text from HTML content.

    Line breaks are only introduced at block-level tag boundaries; text
    split across inline tags is joined into a single line.
    """

    def __init__(self) -> None:
        """Initialize the HTML stripper."""
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self._lines: list[str] = []
        self._current_line: list[str] = []

    def _flush_line(self) -> None:
        """End the current line, if it has any text in it."""
        if self._current_line:
            self._lines.append(" ".join(self._current_line))
            self._current_line = []

    def handle_data(self, data: str) -> None:
        """Handle text data from HTML."""
        stripped = data.strip()
        if stripped:
            self._current_line.append(stripped)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Break the current line on block-level start tags."""
        if tag.lower() in _BLOCK_TAGS:
            self._flush_line()

    def handle_endtag(self, tag: str) -> None:
        """Break the current line on block-level end tags."""
        if tag.lower() in _BLOCK_TAGS:
            self._flush_line()

    def get_text(self) -> str:
        """Get the extracted plain text."""
        self._flush_line()
        return "\n".join(self._lines)


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


def normalize_text_characters(text: str) -> str:
    """Normalize text by removing/converting Unicode characters.

    This is a convenience function that applies Unicode-to-ASCII normalization
    to already plain text (without HTML tags).

    Args:
        text: Plain text to normalize

    Returns:
        Text with Unicode characters converted to ASCII equivalents
    """
    return normalize_unicode_to_ascii(text)
