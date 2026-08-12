"""Unit tests for HTML text extraction utilities."""

from epub_converter.presentation.text_utils import strip_html_tags


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
