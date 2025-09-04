import json
import os
import re
from pathlib import Path
from typing import Annotated

import typer

from confluence_markdown_exporter import __version__
from confluence_markdown_exporter.utils.app_data_store import get_settings
from confluence_markdown_exporter.utils.app_data_store import sanitize_config
from confluence_markdown_exporter.utils.app_data_store import set_setting
from confluence_markdown_exporter.utils.config_interactive import main_config_menu_loop
from confluence_markdown_exporter.utils.measure_time import measure
from confluence_markdown_exporter.utils.type_converter import str_to_bool

DEBUG: bool = str_to_bool(os.getenv("DEBUG", "False"))

app = typer.Typer()


def override_output_path_config(value: Path | None) -> None:
    """Override the default output path if provided."""
    if value is not None:
        set_setting("export.output_path", value)


@app.command(help="Export one or more Confluence pages by ID or URL to Markdown.")
def pages(
    pages: Annotated[list[str], typer.Argument(help="Page ID(s) or URL(s)")],
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Page  # noqa: PLC0415 lacy load

    with measure(f"Export pages {', '.join(pages)}"):
        override_output_path_config(output_path)
        for page in pages:
            _page = Page.from_id(int(page)) if page.isdigit() else Page.from_url(page)
            _page.export()


@app.command(help="Export Confluence pages and their descendant pages by ID or URL to Markdown.")
def pages_with_descendants(
    pages: Annotated[list[str], typer.Argument(help="Page ID(s) or URL(s)")],
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Page  # noqa: PLC0415 lacy load

    with measure(f"Export pages {', '.join(pages)} with descendants"):
        override_output_path_config(output_path)
        for page in pages:
            _page = Page.from_id(int(page)) if page.isdigit() else Page.from_url(page)
            _page.export_with_descendants()


@app.command(help="Export all Confluence pages of one or more spaces to Markdown.")
def spaces(
    space_keys: Annotated[list[str], typer.Argument()],
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Space  # noqa: PLC0415 lacy load

    normalized_space_keys = [_normalize_space_key(key) for key in space_keys]

    with measure(f"Export spaces {', '.join(normalized_space_keys)}"):
        override_output_path_config(output_path)
        for space_key in normalized_space_keys:
            space = Space.from_key(space_key)
            space.export()

@app.command(help="Export all Confluence pages across all spaces to Markdown.")
def all_spaces(
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Organization  # noqa: PLC0415 lacy load

    with measure("Export all spaces"):
        override_output_path_config(output_path)
        org = Organization.from_api()
        org.export()


@app.command(help="Open the interactive configuration menu or display current configuration.")
def config(
    jump_to: Annotated[
        str | None,
        typer.Option(help="Jump directly to a config submenu, e.g. 'auth.confluence'"),
    ] = None,
    *,
    show: Annotated[
        bool,
        typer.Option(
            "--show",
            help="Display current configuration as YAML instead of opening the interactive menu",
        ),
    ] = False,
) -> None:
    """Interactive configuration menu or display current configuration."""
    if show:
        # Display current configuration as YAML
        current_settings = get_settings()
        config_dict = current_settings.model_dump()
        sanitized_config = sanitize_config(config_dict)

        # Output as JSON with clean formatting
        json_output = json.dumps(sanitized_config, indent=2)
        typer.echo(f"```json\n{json_output}\n```")
    else:
        main_config_menu_loop(jump_to)


@app.command(help="Show the current version of confluence-markdown-exporter.")
def version() -> None:
    """Display the current version."""
    typer.echo(f"confluence-markdown-exporter {__version__}")

def _normalize_space_key(space_key: str) -> str:
    # Personal Confluence spaces start with ~. Exporting them on Windows leads to
    # Powershell expanding tilde to the Users directory, which is handled here
    return re.sub(r"^[A-Z]:\\Users\\", "~", space_key, count=1, flags=re.IGNORECASE)

if __name__ == "__main__":
    app()
