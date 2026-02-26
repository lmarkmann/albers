"""CLI entry point."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .banner import print_banner
from .reports import (
    report_contrast,
    report_cross_theme,
    report_harmony,
    report_palette,
    report_psychology,
)
from .replacement import analyze_color_replacement, suggest_replacements
from .theme_loader import THEMES_DIR, load_themes

app = typer.Typer(
    name="albers",
    help="Color analysis — harmony, contrast, and perceptual metrics for theme palettes.",
    add_completion=False,
    invoke_without_command=True,
)
console = Console()

_themes_dir: Path | None = None


def _load_and_validate_themes() -> dict[str, dict]:
    """Load themes and exit with an error if none are found."""
    themes = load_themes(_themes_dir)
    if not themes:
        directory = _themes_dir or THEMES_DIR
        console.print(
            f"[bold red]No themes found in[/bold red] [cyan]{directory}[/cyan]\n"
            f"[dim]Set ALBERS_THEMES_DIR or pass --themes-dir[/dim]"
        )
        raise typer.Exit(1)
    console.print(
        f"[dim]Loaded {len(themes)} theme(s):[/dim] "
        f"[bold]{', '.join(themes.keys())}[/bold]"
    )
    return themes


@app.callback()
def main_callback(
    ctx: typer.Context,
    themes_dir: Annotated[
        Path | None,
        typer.Option(
            "--themes-dir",
            "-d",
            help="Directory containing theme JSON files.",
            show_default=False,
        ),
    ] = None,
):
    """Color analysis for theme palettes."""
    global _themes_dir
    _themes_dir = themes_dir
    print_banner(console)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("palette")
def cmd_palette(
    theme_name: Annotated[
        str | None,
        typer.Option(
            "--theme", "-t", help="Specific theme to analyze (default: all)"
        ),
    ] = None,
):
    """Show the unique palette per theme with HSL breakdown and color swatches."""
    themes = _load_and_validate_themes()
    if theme_name:
        if theme_name not in themes:
            console.print(f"[bold red]Error:[/bold red] Theme '{theme_name}' not found")
            raise typer.Exit(1)
        themes = {theme_name: themes[theme_name]}
    report_palette(themes, console=console)


@app.command("harmony")
def cmd_harmony(
    theme_name: Annotated[
        str | None,
        typer.Option(
            "--theme", "-t", help="Specific theme to analyze (default: all)"
        ),
    ] = None,
):
    """Analyze color harmony relationships in syntax palettes."""
    themes = _load_and_validate_themes()
    if theme_name:
        if theme_name not in themes:
            console.print(f"[bold red]Error:[/bold red] Theme '{theme_name}' not found")
            raise typer.Exit(1)
        themes = {theme_name: themes[theme_name]}
    report_harmony(themes, console=console)


@app.command("contrast")
def cmd_contrast(
    theme_name: Annotated[
        str | None,
        typer.Option(
            "--theme", "-t", help="Specific theme to analyze (default: all)"
        ),
    ] = None,
    min_contrast: Annotated[
        float,
        typer.Option(
            "--min", "-m", help="Minimum contrast ratio to check (default: 4.5)"
        ),
    ] = 4.5,
):
    """WCAG contrast analysis for key UI and syntax elements."""
    themes = _load_and_validate_themes()
    if theme_name:
        if theme_name not in themes:
            console.print(f"[bold red]Error:[/bold red] Theme '{theme_name}' not found")
            raise typer.Exit(1)
        themes = {theme_name: themes[theme_name]}
    report_contrast(themes, console=console, min_contrast=min_contrast)


@app.command("psychology")
def cmd_psychology(
    theme_name: Annotated[
        str | None,
        typer.Option(
            "--theme", "-t", help="Specific theme to analyze (default: all)"
        ),
    ] = None,
):
    """Emotional/psychological response predictions based on color theory."""
    themes = _load_and_validate_themes()
    if theme_name:
        if theme_name not in themes:
            console.print(f"[bold red]Error:[/bold red] Theme '{theme_name}' not found")
            raise typer.Exit(1)
        themes = {theme_name: themes[theme_name]}
    report_psychology(themes, console=console)


@app.command("cross-theme")
def cmd_cross_theme():
    """Compare color choices across theme variants."""
    themes = _load_and_validate_themes()
    report_cross_theme(themes, console=console)


@app.command("all")
def cmd_all(
    theme_name: Annotated[
        str | None,
        typer.Option(
            "--theme", "-t", help="Specific theme to analyze (default: all)"
        ),
    ] = None,
):
    """Run all analysis reports."""
    themes = _load_and_validate_themes()
    if theme_name:
        if theme_name not in themes:
            console.print(f"[bold red]Error:[/bold red] Theme '{theme_name}' not found")
            raise typer.Exit(1)
        themes = {theme_name: themes[theme_name]}

    reports = [
        ("Palette Overview", cmd_palette),
        ("Harmony Analysis", cmd_harmony),
        ("Contrast Analysis", cmd_contrast),
        ("Psychology Analysis", cmd_psychology),
        ("Cross-Theme Comparison", cmd_cross_theme),
    ]

    for report_name, _ in reports:
        console.print(
            Panel(
                f"[bold]{report_name}[/bold]",
                title="📊 Color Analysis",
                border_style="blue",
            )
        )

    # Run reports directly
    report_palette(themes, console=console)
    console.print()
    report_harmony(themes, console=console)
    console.print()
    report_contrast(themes, console=console)
    console.print()
    report_psychology(themes, console=console)
    console.print()
    report_cross_theme(themes, console=console)


@app.command("replace")
def cmd_replace(
    old_color: Annotated[
        str,
        typer.Argument(help="Current color hex code (e.g., #ff5555)"),
    ],
    new_color: Annotated[
        str,
        typer.Argument(help="New color hex code (e.g., #ff6666)"),
    ],
    theme_name: Annotated[
        str | None,
        typer.Option(
            "--theme", "-t", help="Specific theme to analyze (default: all)"
        ),
    ] = None,
    show_preview: Annotated[
        bool,
        typer.Option("--preview", "-p", help="Show color preview swatches"),
    ] = False,
):
    """Analyze the impact of replacing one color with another."""
    themes = _load_and_validate_themes()
    if theme_name:
        if theme_name not in themes:
            console.print(f"[bold red]Error:[/bold red] Theme '{theme_name}' not found")
            raise typer.Exit(1)
        themes = {theme_name: themes[theme_name]}

    for name, theme in themes.items():
        console.print(
            Panel(
                f"[bold]{name}[/bold]\n[cyan]{old_color}[/cyan] → [green]{new_color}[/green]",
                title="🔄 Replacement Analysis",
                border_style="yellow",
            )
        )
        result = analyze_color_replacement(theme, old_color, new_color, console=console)
        if show_preview:
            suggest_replacements(old_color, new_color, console=console)


@app.command("suggest")
def cmd_suggest(
    color: Annotated[
        str,
        typer.Argument(help="Base color hex code to find alternatives for"),
    ],
    theme_name: Annotated[
        str | None,
        typer.Option(
            "--theme", "-t", help="Specific theme to analyze (default: all)"
        ),
    ] = None,
    harmony_type: Annotated[
        str,
        typer.Option(
            "--harmony",
            "-h",
            help="Type of harmony to suggest (complementary, analogous, triadic, split)",
            case_sensitive=False,
        ),
    ] = "all",
):
    """Suggest color alternatives based on harmony rules."""
    themes = _load_and_validate_themes()
    if theme_name:
        themes = {theme_name: themes[theme_name]}

    for name, theme in themes.items():
        console.print(
            Panel(
                f"[bold]{name}[/bold]\nBase color: [cyan]{color}[/cyan]",
                title="💡 Color Suggestions",
                border_style="green",
            )
        )
        suggest_replacements(color, None, harmony_type=harmony_type, console=console)


@app.command("compare")
def cmd_compare(
    color1: Annotated[
        str,
        typer.Argument(help="First color hex code"),
    ],
    color2: Annotated[
        str,
        typer.Argument(help="Second color hex code"),
    ],
):
    """Compare two colors side-by-side with metrics."""
    from .conversions import (
        delta_e_76,
        hex_to_rgb,
        rgb_to_hsl,
        rgb_to_lab,
        contrast_ratio,
    )
    from .rich_utils import display_color_comparison

    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    if not rgb1 or not rgb2:
        console.print("[bold red]Error:[/bold red] Invalid color hex code(s)")
        raise typer.Exit(1)

    hsl1 = rgb_to_hsl(*rgb1)
    hsl2 = rgb_to_hsl(*rgb2)
    lab1 = rgb_to_lab(*rgb1)
    lab2 = rgb_to_lab(*rgb2)

    de = delta_e_76(lab1, lab2)
    cr = contrast_ratio(rgb1, rgb2)

    display_color_comparison(
        color1, color2, rgb1, rgb2, hsl1, hsl2, lab1, lab2, de, cr, console=console
    )


# Test commands group
test_app = typer.Typer(help="Run tests for color analysis functionality")
app.add_typer(test_app, name="test")


@test_app.command("all")
def test_all():
    """Run all tests."""
    console.print(Panel("[bold]Running All Tests[/bold]", border_style="green"))
    results = []
    results.append(("Theme Loading", test_theme_loading()))
    results.append(("Color Conversions", test_color_conversions()))
    results.append(("Contrast Analysis", test_contrast_analysis()))
    results.append(("Harmony Detection", test_harmony_detection()))
    results.append(("Palette Report", test_palette_report()))
    results.append(("Psychology Analysis", test_psychology_analysis()))
    results.append(("Replacement Analysis", test_replacement_analysis()))

    console.print("\n[bold]Test Summary[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Test", style="dim")
    table.add_column("Result", justify="center")
    table.add_column("Details", style="green")

    for name, (passed, details) in results:
        status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        table.add_row(name, status, details)

    console.print(table)

    all_passed = all(passed for passed, _ in results)
    if all_passed:
        console.print("\n[bold green]✓ All tests passed![/bold green]")
    else:
        console.print("\n[bold red]✗ Some tests failed[/bold red]")
        raise typer.Exit(1)


@test_app.command("theme-loading")
def test_theme_cmd():
    """Test theme loading functionality."""
    passed, details = test_theme_loading()
    if passed:
        console.print(f"[green]✓ PASS[/green] {details}")
    else:
        console.print(f"[red]✗ FAIL[/red] {details}")
        raise typer.Exit(1)


@test_app.command("conversions")
def test_conversions_cmd():
    """Test color conversion functions."""
    passed, details = test_color_conversions()
    if passed:
        console.print(f"[green]✓ PASS[/green] {details}")
    else:
        console.print(f"[red]✗ FAIL[/red] {details}")
        raise typer.Exit(1)


@test_app.command("contrast")
def test_contrast_cmd():
    """Test contrast analysis."""
    passed, details = test_contrast_analysis()
    if passed:
        console.print(f"[green]✓ PASS[/green] {details}")
    else:
        console.print(f"[red]✗ FAIL[/red] {details}")
        raise typer.Exit(1)


@test_app.command("harmony")
def test_harmony_cmd():
    """Test harmony detection."""
    passed, details = test_harmony_detection()
    if passed:
        console.print(f"[green]✓ PASS[/green] {details}")
    else:
        console.print(f"[red]✗ FAIL[/red] {details}")
        raise typer.Exit(1)


@test_app.command("palette")
def test_palette_cmd():
    """Test palette report generation."""
    passed, details = test_palette_report()
    if passed:
        console.print(f"[green]✓ PASS[/green] {details}")
    else:
        console.print(f"[red]✗ FAIL[/red] {details}")
        raise typer.Exit(1)


@test_app.command("psychology")
def test_psychology_cmd():
    """Test psychology analysis."""
    passed, details = test_psychology_analysis()
    if passed:
        console.print(f"[green]✓ PASS[/green] {details}")
    else:
        console.print(f"[red]✗ FAIL[/red] {details}")
        raise typer.Exit(1)


@test_app.command("replacement")
def test_replacement_cmd():
    """Test replacement analysis."""
    passed, details = test_replacement_analysis()
    if passed:
        console.print(f"[green]✓ PASS[/green] {details}")
    else:
        console.print(f"[red]✗ FAIL[/red] {details}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
