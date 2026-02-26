"""Rich display utilities for color visualization."""

from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from .conversions import swatch_text_color


def create_color_swatch(
    hex_color: str,
    text: str = "  ",
    show_hex: bool = True,
) -> Text:
    """Create a Rich Text object with a colored background swatch."""
    hex_clean = hex_color.lstrip("#")[:6]
    tc = swatch_text_color(hex_color)

    styled_text = Text()
    if show_hex:
        styled_text.append(
            f"{hex_color} ", style=f"bold {tc}"
        )
    styled_text.append(text, style=Style(bgcolor=hex_clean))
    return styled_text


def display_color_bar(
    console: Console,
    colors: list[str],
    title: str | None = None,
    labels: list[str] | None = None,
):
    """Display a horizontal bar of color swatches."""
    if title:
        console.print(f"\n[bold]{title}[/bold]")

    for i, color in enumerate(colors):
        label = labels[i] if labels and i < len(labels) else ""
        hex_clean = color.lstrip("#")[:6]
        tc = swatch_text_color(color)

        swatch_text = (
            f"{color} {label}" if label else color
        )
        console.print(
            Text(
                swatch_text,
                style=Style(bgcolor=hex_clean, color=tc),
            )
        )


def display_color_comparison(
    color1: str,
    color2: str,
    rgb1: tuple[int, int, int],
    rgb2: tuple[int, int, int],
    hsl1: tuple[float, float, float],
    hsl2: tuple[float, float, float],
    lab1: tuple[float, float, float],
    lab2: tuple[float, float, float],
    delta_e: float,
    contrast: float,
    console: Console,
):
    """Display a side-by-side comparison of two colors."""
    from .conversions import (
        color_temperature,
        get_contrast_category,
    )

    table = Table(
        show_header=True, header_style="bold cyan", box=None
    )
    table.add_column("Property", style="dim")
    table.add_column(color1, justify="center")
    table.add_column(color2, justify="center")

    hex1_clean = color1.lstrip("#")[:6]
    hex2_clean = color2.lstrip("#")[:6]
    swatch1 = Text(
        "████████", style=Style(bgcolor=hex1_clean)
    )
    swatch2 = Text(
        "████████", style=Style(bgcolor=hex2_clean)
    )
    table.add_row("Preview", swatch1, swatch2)

    table.add_row("RGB", f"{rgb1}", f"{rgb2}")

    table.add_row(
        "HSL",
        f"H:{hsl1[0]:.1f} S:{hsl1[1]:.1f}% "
        f"L:{hsl1[2]:.1f}%",
        f"H:{hsl2[0]:.1f} S:{hsl2[1]:.1f}% "
        f"L:{hsl2[2]:.1f}%",
    )

    temp1 = color_temperature(hsl1[0], hsl1[1])
    temp2 = color_temperature(hsl2[0], hsl2[1])
    table.add_row("Temperature", temp1, temp2)

    table.add_row("ΔE (Lab)", f"{delta_e:.2f}", "")

    category = get_contrast_category(contrast)
    table.add_row(
        "Contrast Ratio",
        f"{contrast:.2f}:1",
        (
            f"[green]{category}[/green]"
            if "Fail" not in category
            else f"[red]{category}[/red]"
        ),
    )

    if delta_e < 2.3:
        similarity = "[green]Indistinguishable[/green]"
    elif delta_e < 5.0:
        similarity = "[green]Very similar[/green]"
    elif delta_e < 10.0:
        similarity = "[yellow]Similar[/yellow]"
    elif delta_e < 20.0:
        similarity = "[orange]Different[/orange]"
    else:
        similarity = "[red]Very different[/red]"

    table.add_row("Perceptual Difference", similarity, "")

    console.print(table)


def display_contrast_grid(
    console: Console,
    colors: list[tuple[str, str]],
    bg_color: str,
    min_contrast: float = 4.5,
):
    """Display a grid showing contrast ratios against a background."""
    from .conversions import (
        contrast_ratio,
        get_contrast_category,
        hex_to_rgb,
    )

    bg_rgb = hex_to_rgb(bg_color)
    if not bg_rgb:
        console.print("[red]Invalid background color[/red]")
        return

    table = Table(
        show_header=True, header_style="bold magenta"
    )
    table.add_column("Color", style="dim")
    table.add_column("Preview", justify="center")
    table.add_column("CR", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Usage", style="italic")

    for name, hex_color in colors:
        rgb = hex_to_rgb(hex_color)
        if rgb:
            cr = contrast_ratio(rgb, bg_rgb)
            category = get_contrast_category(cr)

            hex_clean = hex_color.lstrip("#")[:6]
            tc = swatch_text_color(hex_color)

            preview = Text(
                " Sample ",
                style=Style(bgcolor=hex_clean, color=tc),
            )

            if cr >= min_contrast:
                status = f"[green]✓ {category}[/green]"
                usage = (
                    "Safe for text"
                    if cr >= 4.5
                    else "Large text only"
                )
            else:
                status = f"[red]✗ {category}[/red]"
                usage = "Decorative only"

            table.add_row(
                name, preview, f"{cr:.2f}", status, usage
            )

    console.print(table)


def display_harmony_wheel(
    console: Console,
    base_hue: float,
    saturation: float,
    lightness: float,
    harmony_type: str = "all",
):
    """Display harmony colors in a visual format."""
    from .conversions import (
        generate_harmony_colors,
        hsl_to_rgb,
        rgb_to_hex,
    )

    harmonies = generate_harmony_colors(
        base_hue, saturation, lightness, harmony_type
    )

    table = Table(
        show_header=True, header_style="bold green", box=None
    )
    table.add_column("Type", style="cyan")
    table.add_column("HSL", style="dim")
    table.add_column("Hex", style="bold")
    table.add_column("Preview", justify="center")

    base_hex = rgb_to_hex(
        *hsl_to_rgb(base_hue, saturation, lightness)
    )
    tc = swatch_text_color(base_hex)
    hex_clean = base_hex.lstrip("#")[:6]
    base_preview = Text(
        " Base ",
        style=Style(bgcolor=hex_clean, color=tc),
    )
    table.add_row(
        "Base",
        f"H:{base_hue:.0f} S:{saturation:.0f}% "
        f"L:{lightness:.0f}%",
        base_hex,
        base_preview,
    )

    harmony_names = {
        180: "Complementary",
        -30: "Analogous (-30°)",
        30: "Analogous (+30°)",
        120: "Triadic (120°)",
        240: "Triadic (240°)",
        150: "Split (150°)",
        210: "Split (210°)",
        90: "Tetradic (90°)",
        270: "Tetradic (270°)",
    }

    for h, s, l_val in harmonies:
        hex_color = rgb_to_hex(*hsl_to_rgb(h, s, l_val))
        hex_clean = hex_color.lstrip("#")[:6]
        tc = swatch_text_color(hex_color)
        preview = Text(
            " Harmony ",
            style=Style(bgcolor=hex_clean, color=tc),
        )

        rotation = h - base_hue
        if rotation > 180:
            rotation -= 360
        elif rotation < -180:
            rotation += 360

        type_name = harmony_names.get(
            rotation, f"Harmony ({rotation:.0f}°)"
        )
        table.add_row(
            type_name,
            f"H:{h:.0f} S:{s:.0f}% L:{l_val:.0f}%",
            hex_color,
            preview,
        )

    console.print(table)


def display_temperature_bar(
    console: Console,
    temps: dict[str, int],
    total: int,
):
    """Display a visual temperature distribution bar."""
    console.print(
        "\n[bold]Temperature Distribution:[/bold]"
    )

    for temp in ["warm", "cool", "transitional", "neutral"]:
        count = temps.get(temp, 0)
        pct = count / total * 100 if total else 0
        bar_length = int(pct / 2)

        temp_colors = {
            "warm": "red",
            "cool": "blue",
            "transitional": "yellow",
            "neutral": "white",
        }
        color = temp_colors.get(temp, "white")

        bar = "█" * bar_length
        console.print(
            f"  [bold {color}]{temp:14s}[/bold {color}] "
            f"{count:3d} ({pct:4.1f}%) [dim]{bar}[/dim]"
        )


def display_emotion_summary(
    console: Console,
    emotions: dict[str, int],
):
    """Display emotional associations as a visual summary."""
    if not emotions:
        return

    console.print(
        "\n[bold]Emotional Associations:[/bold]"
    )

    max_count = max(emotions.values()) if emotions else 1

    for emotion, count in sorted(
        emotions.items(), key=lambda x: -x[1]
    ):
        bar_length = int((count / max_count) * 20)
        bar = "█" * bar_length
        console.print(
            f"  [cyan]{emotion:35s}[/cyan] "
            f"[green]{bar}[/green] ({count})"
        )
