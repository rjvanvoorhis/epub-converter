"""EPUB Converter CLI Application.

A clean architecture CLI application for converting and extracting EPUB files.
"""


def main() -> None:
    """Main entry point for the epub-converter CLI application.
    
    Uses Typer for modern, type-hinted CLI interface.
    """
    from epub_converter.presentation.cli.typer_app import cli_main

    cli_main()
