"""Typer-based CLI application for EPUB Converter.

Provides a modern, type-hinted CLI interface using Typer.
"""

from pathlib import Path
from typing import Optional

import typer

from epub_converter.composition.container import Container
from epub_converter.application.audiobook_conversion.dtos import (
    ConvertEPUBToAudiobookInput,
)
from epub_converter.presentation.text_utils import strip_html_tags

app = typer.Typer(
    name="epub-converter",
    help="Convert and extract EPUB files to audiobooks and text",
    no_args_is_help=True,
)


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get or create the application container."""
    global _container
    if _container is None:
        _container = Container()
    return _container


@app.command()
def convert_to_audiobook(
    epub_file: Path = typer.Argument(
        ...,
        help="Path to the EPUB file to convert",
        exists=True,
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Path for output MP3 file (default: {epub_name}.mp3)",
    ),
    voice_profile_id: str = typer.Option(
        "voice_1",
        "--profile",
        "-p",
        help="Voice profile ID to use for speech synthesis",
    ),
    language: str = typer.Option(
        "en",
        "--language",
        "-l",
        help="Language code for text-to-speech",
    ),
    chunk_size: int = typer.Option(
        45000,
        "--chunk-size",
        "-c",
        help="Maximum characters per audio chunk",
    ),
) -> None:
    """Convert an EPUB file to an audiobook in MP3 format.

    Example:
        epub-converter convert-to-audiobook book.epub --output book.mp3 --profile voice_1
    """
    try:
        # Set default output path if not provided
        if output_file is None:
            output_file = epub_file.with_suffix(".mp3")

        # Get use case from container
        container = get_container()
        use_case = container.convert_audiobook_use_case

        # Create input DTO and execute
        input_dto = ConvertEPUBToAudiobookInput(
            epub_file_path=epub_file,
            output_file_path=output_file,
            voice_profile_id=voice_profile_id,
            language=language,
            chunk_size=chunk_size,
        )

        output_dto = use_case.execute(input_dto)

        typer.echo(
            typer.style("[OK] Conversion successful!", fg=typer.colors.GREEN),
            err=False,
        )
        typer.echo(f"Output file: {output_dto.output_file_path}")
        typer.echo(
            f"Duration: {output_dto.total_duration_seconds:.1f} seconds "
            f"({output_dto.total_duration_seconds / 60:.1f} minutes)"
        )
        typer.echo(f"Chapters: {output_dto.chapter_count}")

    except FileNotFoundError as e:
        typer.echo(typer.style(f"[ERROR] Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        typer.echo(typer.style(f"[ERROR] Invalid input: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(
            typer.style(f"[ERROR] Conversion failed: {e}", fg=typer.colors.RED),
            err=True,
        )
        raise typer.Exit(code=1)


@app.command()
def list_voices() -> None:
    """List available voice profiles for speech synthesis.

    Example:
        epub-converter list-voices
    """
    try:
        container = get_container()
        use_case = container.list_voice_profiles_use_case

        output = use_case.execute()

        if output.profile_count == 0:
            typer.echo("No voice profiles available.")
            return

        typer.echo(
            typer.style(
                f"Available Voice Profiles ({output.profile_count}):",
                fg=typer.colors.CYAN,
                bold=True,
            )
        )
        typer.echo()

        for profile in output.profiles:
            typer.echo(
                typer.style(f"  {profile['id']}", fg=typer.colors.BLUE, bold=True)
            )
            typer.echo(f"    Name: {profile['name']}")
            typer.echo(f"    Language: {profile['language']}")
            typer.echo(f"    Description: {profile['description']}")
            typer.echo()

    except Exception as e:
        typer.echo(
            typer.style(f"[ERROR] Failed to list voices: {e}", fg=typer.colors.RED),
            err=True,
        )
        raise typer.Exit(code=1)


@app.command()
def extract_chapters(
    epub_file: Path = typer.Argument(
        ...,
        help="Path to the EPUB file to extract",
        exists=True,
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for extracted chapters (default: current directory)",
    ),
) -> None:
    """Extract chapters from an EPUB file.

    Example:
        epub-converter extract-chapters book.epub --output chapters/
    """
    try:
        container = get_container()
        load_epub_use_case = container.load_epub_use_case
        extract_chapter_use_case = container.extract_chapter_use_case

        # Import here to avoid circular dependency
        from epub_converter.application.epub_extraction.dtos import (
            LoadEPUBInput,
            ExtractChapterInput,
        )

        # Set default output directory to current directory
        if output_dir is None:
            output_dir = Path.cwd()
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load EPUB to get chapter information
        input_dto = LoadEPUBInput(file_path=epub_file)
        epub_info = load_epub_use_case.execute(input_dto)

        typer.echo(
            typer.style("[OK] Extraction successful!", fg=typer.colors.GREEN),
            err=False,
        )
        typer.echo(f"Title: {epub_info.title}")
        if epub_info.author:
            typer.echo(f"Author: {epub_info.author}")
        typer.echo(f"Language: {epub_info.language}")
        typer.echo(f"Total Chapters: {epub_info.total_chapters}")
        typer.echo(f"Total Words: {epub_info.total_word_count}")

        if epub_info.chapters:
            typer.echo()
            typer.echo(
                typer.style("Writing chapters to:", fg=typer.colors.CYAN, bold=True)
            )
            typer.echo(f"  {output_dir.resolve()}")
            typer.echo()

            files_written = 0
            for chapter in epub_info.chapters:
                try:
                    # Extract chapter content
                    extract_input = ExtractChapterInput(
                        file_path=epub_file,
                        chapter_id=chapter.id,
                    )
                    chapter_content = extract_chapter_use_case.execute(extract_input)

                    # Create filename: chapter_001_title.txt
                    filename = f"chapter_{chapter.id:03d}_{chapter.title[:50]}.txt"
                    # Sanitize filename
                    filename = "".join(c for c in filename if c.isalnum() or c in " _-.").strip()
                    output_file = output_dir / filename

                    # Strip HTML tags and write chapter to file
                    plain_text = strip_html_tags(chapter_content.content)
                    output_file.write_text(plain_text, encoding="utf-8")

                    typer.echo(
                        f"  [+] {filename} ({chapter.word_count} words)"
                    )
                    files_written += 1

                except Exception as chapter_err:
                    typer.echo(
                        typer.style(
                            f"  [-] Failed to extract chapter {chapter.id}: {chapter_err}",
                            fg=typer.colors.YELLOW,
                        )
                    )

            typer.echo()
            typer.echo(
                typer.style(
                    f"Successfully wrote {files_written}/{epub_info.total_chapters} chapters",
                    fg=typer.colors.GREEN,
                )
            )

    except FileNotFoundError as e:
        typer.echo(typer.style(f"[ERROR] Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(
            typer.style(f"[ERROR] Extraction failed: {e}", fg=typer.colors.RED),
            err=True,
        )
        raise typer.Exit(code=1)


@app.command()
def info() -> None:
    """Display information about the EPUB Converter application."""
    typer.echo(
        typer.style("EPUB Converter v0.1.0", fg=typer.colors.CYAN, bold=True)
    )
    typer.echo()
    typer.echo("A clean architecture CLI application for converting and extracting EPUB files.")
    typer.echo()
    typer.echo(
        typer.style("Features:", fg=typer.colors.BLUE, bold=True)
    )
    typer.echo("  • Convert EPUB files to audiobooks (MP3)")
    typer.echo("  • Extract chapters from EPUB files")
    typer.echo("  • List available voice profiles")
    typer.echo()
    typer.echo(
        typer.style("Commands:", fg=typer.colors.BLUE, bold=True)
    )
    typer.echo("  epub-converter convert-to-audiobook  Convert EPUB to audiobook")
    typer.echo("  epub-converter list-voices          List available voice profiles")
    typer.echo("  epub-converter extract-chapters     Extract chapters from EPUB")
    typer.echo("  epub-converter info                 Show this information")
    typer.echo()
    typer.echo(
        typer.style("Use --help for more information on any command.", fg=typer.colors.BRIGHT_BLACK)
    )


def cli_main() -> None:
    """Entry point for the Typer CLI application."""
    app()
