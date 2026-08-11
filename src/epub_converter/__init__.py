"""EPUB Converter CLI Application.

A clean architecture CLI application for converting and extracting EPUB files.
"""

from epub_converter.composition.container import Container
from epub_converter.presentation.cli.responses import FormattedResponse, ResponseStatus


def main() -> None:
    """Main entry point for the epub-converter CLI application."""
    import sys

    try:
        # Compose application dependencies
        container = Container()
        controller = container.cli_controller

        # Display available commands if no arguments provided
        if len(sys.argv) < 2:
            commands = controller.get_available_commands()
            print("Available commands:")
            for cmd_name, cmd_desc in commands.items():
                print(f"  {cmd_name}: {cmd_desc}")
            return

        # Extract command and arguments
        command_name = sys.argv[1]
        args = sys.argv[2:]

        # Execute command
        result = controller.execute_command(command_name, *args)
        response = FormattedResponse(
            ResponseStatus.SUCCESS, "Command executed successfully", result
        )
        print(response.render())

    except FileNotFoundError as e:
        response = FormattedResponse(ResponseStatus.ERROR, str(e))
        print(response.render())
        sys.exit(1)
    except ValueError as e:
        response = FormattedResponse(ResponseStatus.ERROR, str(e))
        print(response.render())
        sys.exit(1)
    except Exception as e:
        response = FormattedResponse(ResponseStatus.ERROR, f"Unexpected error: {e}")
        print(response.render())
        sys.exit(1)
