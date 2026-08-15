"""Unit tests for HTML text extraction utilities."""

import pytest

from epub_converter.presentation.text_utils import (
    apply_pronunciation_dictionary,
    load_pronunciation_dictionary,
    strip_html_tags,
)


class TestStripHtmlTagsInlineTags:
    """Inline tags must not introduce spurious line breaks mid-sentence."""

    def test_emphasis_tag_does_not_split_sentence(self) -> None:
        """<em> around a word should not break the surrounding sentence."""
        html = (
            "<p>the man who kept <em>hitting Zuko's back</em> said, "
            "without much inflection.</p>"
        )
        result = strip_html_tags(html)
        assert result == "the man who kept hitting Zuko's back said, without much inflection."

    def test_single_word_emphasis_stays_inline(self) -> None:
        """A single emphasized word must not end up on its own line."""
        html = "<p>Zuko <em>would</em> live, if only to spite them.</p>"
        result = strip_html_tags(html)
        assert result == "Zuko would live, if only to spite them."

    def test_span_and_bold_tags_join_inline(self) -> None:
        """Other common inline tags (span, b, i, strong, a) join inline too."""
        html = (
            "<p>Some <span>styled</span> and <b>bold</b> and <i>italic</i> "
            "and <strong>strong</strong> and <a href='#'>linked</a> text.</p>"
        )
        result = strip_html_tags(html)
        assert result == "Some styled and bold and italic and strong and linked text."


class TestStripHtmlTagsBlockTags:
    """Block-level tags should still produce real line breaks."""

    def test_paragraphs_become_separate_lines(self) -> None:
        """Each <p> should be its own line in the output."""
        html = "<p>First sentence.</p><p>Second sentence.</p>"
        result = strip_html_tags(html)
        assert result == "First sentence.\nSecond sentence."

    def test_br_tag_breaks_line(self) -> None:
        """<br/> within a paragraph should still create a line break."""
        html = "<p>Line one.<br/>Line two.</p>"
        result = strip_html_tags(html)
        assert result == "Line one.\nLine two."

    def test_empty_paragraphs_do_not_produce_blank_lines(self) -> None:
        """Empty block elements should not leave stray blank lines."""
        html = "<p>First.</p><p></p><p>Second.</p>"
        result = strip_html_tags(html)
        assert result == "First.\nSecond."


class TestStripHtmlTagsRealWorldExample:
    """Regression test for the exact reported choppy-narration bug."""

    def test_multiple_dialogue_paragraphs_with_emphasis(self) -> None:
        """Reproduces the Salvage chapter 2 passage that motivated the fix."""
        html = (
            '<p>“Tuluk, take him down to the healer.”</p>'
            '<p>“Chief,” the man who’d kept '
            '<em class="calibre11"> hitting Zuko’s back </em> '
            'said, without much inflection.</p>'
            '<p>“We’ll deal with it if he lives,” the Chief said.</p>'
            '<p>Zuko <em class="calibre11"> would </em> live, '
            'if only to spite them.</p>'
        )
        result = strip_html_tags(html)
        lines = result.split("\n")
        assert lines == [
            '"Tuluk, take him down to the healer."',
            '"Chief," the man who\'d kept hitting Zuko\'s back said, without much inflection.',
            '"We\'ll deal with it if he lives," the Chief said.',
            "Zuko would live, if only to spite them.",
        ]


class TestApplyPronunciationDictionary:
    """Tests for replacing words with TTS phoneme control tokens."""

    def test_replaces_whole_word_match(self) -> None:
        """A matched word is wrapped in a phoneme control token."""
        result = apply_pronunciation_dictionary(
            "Worcester speaks at the meeting.", {"Worcester": "wˈʊstər"}
        )
        assert result == "[Worcester](/wˈʊstər/) speaks at the meeting."

    def test_does_not_match_partial_word(self) -> None:
        """A dictionary key must not match inside a longer word."""
        result = apply_pronunciation_dictionary(
            "Worcestershire sauce is different.", {"Worcester": "wˈʊstər"}
        )
        assert result == "Worcestershire sauce is different."

    def test_longer_key_wins_over_overlapping_shorter_key(self) -> None:
        """Overlapping keys prefer the longest match."""
        result = apply_pronunciation_dictionary(
            "Worcestershire sauce.",
            {"Worcester": "wˈʊstər", "Worcestershire": "ˈwʊstərʃər"},
        )
        assert result == "[Worcestershire](/ˈwʊstərʃər/) sauce."

    def test_matches_case_insensitively_preserving_original_case(self) -> None:
        """Matching ignores case but keeps the matched text's original casing."""
        result = apply_pronunciation_dictionary(
            "worcester is a city.", {"Worcester": "wˈʊstər"}
        )
        assert result == "[worcester](/wˈʊstər/) is a city."

    def test_replaces_multiple_occurrences(self) -> None:
        """Every occurrence of a key is replaced."""
        result = apply_pronunciation_dictionary(
            "Worcester is near Worcester.", {"Worcester": "wˈʊstər"}
        )
        assert result == "[Worcester](/wˈʊstər/) is near [Worcester](/wˈʊstər/)."

    def test_empty_dictionary_returns_text_unchanged(self) -> None:
        """No dictionary entries means no replacements."""
        result = apply_pronunciation_dictionary("Worcester speaks.", {})
        assert result == "Worcester speaks."

    def test_empty_text_returns_empty(self) -> None:
        """Empty input text is returned as-is."""
        result = apply_pronunciation_dictionary("", {"Worcester": "wˈʊstər"})
        assert result == ""


class TestLoadPronunciationDictionary:
    """Tests for loading a pronunciation dictionary from a JSON file."""

    def test_loads_valid_dictionary(self, tmp_path) -> None:
        """A flat JSON object of strings loads as a dict."""
        path = tmp_path / "pronunciation.json"
        path.write_text('{"Worcester": "w\\u02cc\\u028cst\\u0259r"}', encoding="utf-8")

        result = load_pronunciation_dictionary(path)

        assert result == {"Worcester": "wˌʌstər"}

    def test_invalid_json_raises_value_error(self, tmp_path) -> None:
        """Malformed JSON raises a ValueError."""
        path = tmp_path / "pronunciation.json"
        path.write_text("{not valid json", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid pronunciation dictionary"):
            load_pronunciation_dictionary(path)

    def test_non_object_json_raises_value_error(self, tmp_path) -> None:
        """A JSON array (or other non-object) raises a ValueError."""
        path = tmp_path / "pronunciation.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")

        with pytest.raises(ValueError, match="flat JSON object"):
            load_pronunciation_dictionary(path)

    def test_non_string_value_raises_value_error(self, tmp_path) -> None:
        """Non-string values in the mapping raise a ValueError."""
        path = tmp_path / "pronunciation.json"
        path.write_text('{"Worcester": 123}', encoding="utf-8")

        with pytest.raises(ValueError, match="flat JSON object"):
            load_pronunciation_dictionary(path)
