"""Color replacement analysis and suggestion tools."""

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from .conversions import (
    contrast_ratio,
    delta_e_76,
    generate_harmony_colors,
    hex_to_rgb,
    hsl_to_rgb,
    rgb_to_hex,
    rgb_to_hsl,
    rgb_to_lab,
    swatch_text_color,
)
from .theme_loader import extract_colors, extract_syntax_colors


# ── Pure computation functions ────────────────────────────────────


def compute_replacement_impact(
    theme: dict,
    old_color: str,
    new_color: str,
) -> dict:
    """Compute the impact of replacing one color with another.

    Args:
        theme: Parsed theme data dict.
        old_color: Current hex color string.
        new_color: Replacement hex color string.

    Returns:
        Dict with ``affected_ui``, ``affected_syntax``,
        ``contrast_changes``, ``recommendations``,
        and ``delta_e`` keys.  Returns ``{"error": ...}``
        on invalid input.
    """
    old_rgb = hex_to_rgb(old_color)
    new_rgb = hex_to_rgb(new_color)

    if not old_rgb or not new_rgb:
        return {"error": "Invalid color"}

    old_hsl = rgb_to_hsl(*old_rgb)
    new_hsl = rgb_to_hsl(*new_rgb)
    old_lab = rgb_to_lab(*old_rgb)
    new_lab = rgb_to_lab(*new_rgb)

    delta_e = delta_e_76(old_lab, new_lab)

    ui_colors = extract_colors(theme)
    syntax_colors = extract_syntax_colors(theme)

    affected_ui = [
        key
        for key, info in ui_colors.items()
        if info["hex"].lower()[:7] == old_color.lower()[:7]
    ]

    affected_syntax = [
        key
        for key, info in syntax_colors.items()
        if info["hex"].lower()[:7] == old_color.lower()[:7]
    ]

    bg_hex = theme.get("colors", {}).get(
        "editor.background", "#000000"
    )
    bg_rgb = hex_to_rgb(bg_hex)

    contrast_changes = []
    if bg_rgb:
        old_cr = contrast_ratio(old_rgb, bg_rgb)
        new_cr = contrast_ratio(new_rgb, bg_rgb)
        contrast_changes.append(
            {
                "context": "editor.background",
                "old_contrast": old_cr,
                "new_contrast": new_cr,
                "change": new_cr - old_cr,
            }
        )

    recommendations = []

    if delta_e < 2.3:
        recommendations.append(
            "✓ Change is barely perceptible - safe replacement"
        )
    elif delta_e < 10:
        recommendations.append(
            "⚠ Moderate change - review affected elements"
        )
    else:
        recommendations.append(
            "⚠⚠ Significant change - "
            "thorough review recommended"
        )

    if bg_rgb:
        old_cr = contrast_ratio(old_rgb, bg_rgb)
        new_cr = contrast_ratio(new_rgb, bg_rgb)

        if old_cr < 4.5 and new_cr >= 4.5:
            recommendations.append(
                "✓ Improves WCAG AA compliance for text"
            )
        elif old_cr >= 4.5 and new_cr < 4.5:
            recommendations.append(
                "⚠ Reduces contrast below WCAG AA standard"
            )

        if new_cr < 3.0:
            recommendations.append(
                "⚠ New color may have visibility issues"
            )

    old_temp = (
        "warm"
        if old_hsl[0] < 60 or old_hsl[0] > 300
        else "cool"
    )
    new_temp = (
        "warm"
        if new_hsl[0] < 60 or new_hsl[0] > 300
        else "cool"
    )

    if old_temp != new_temp:
        recommendations.append(
            f"⚠ Temperature shift: {old_temp} → {new_temp}"
        )

    return {
        "affected_ui": affected_ui,
        "affected_syntax": affected_syntax,
        "contrast_changes": contrast_changes,
        "recommendations": recommendations,
        "delta_e": delta_e,
    }


def compute_harmony_suggestions(
    base_color: str,
    harmony_type: str = "all",
) -> dict:
    """Compute harmony-based color suggestions.

    Args:
        base_color: Hex color string to generate harmonies for.
        harmony_type: One of ``complementary``, ``analogous``,
            ``triadic``, ``split``, ``tetradic``, or ``all``.

    Returns:
        Dict with ``base`` info and ``suggestions`` list.
        Returns ``{"error": ...}`` on invalid input.
    """
    base_rgb = hex_to_rgb(base_color)
    if not base_rgb:
        return {"error": "Invalid base color"}

    base_hsl = rgb_to_hsl(*base_rgb)
    base_lab = rgb_to_lab(*base_rgb)

    harmonies = generate_harmony_colors(
        base_hsl[0], base_hsl[1], base_hsl[2], harmony_type
    )

    suggestions = []
    for h, s, l_val in harmonies:
        rgb = hsl_to_rgb(h, s, l_val)
        hex_color = rgb_to_hex(*rgb)
        lab = rgb_to_lab(*rgb)
        de = delta_e_76(base_lab, lab)

        rotation = h - base_hsl[0]
        if rotation > 180:
            rotation -= 360
        elif rotation < -180:
            rotation += 360

        suggestions.append(
            {
                "hex": hex_color,
                "hsl": (h, s, l_val),
                "delta_e": de,
                "rotation": rotation,
            }
        )

    variations = []
    for l_mod in [-20, -10, 0, 10, 20]:
        l_new = max(0, min(100, base_hsl[2] + l_mod))
        rgb = hsl_to_rgb(base_hsl[0], base_hsl[1], l_new)
        hex_var = rgb_to_hex(*rgb)
        variations.append(
            {"name": f"L{int(l_new)}", "hex": hex_var}
        )

    return {
        "base": {
            "hex": base_color,
            "hsl": base_hsl,
        },
        "suggestions": suggestions,
        "variations": variations,
    }


def compute_similar_colors(
    theme: dict,
    target_color: str,
    max_delta_e: float = 15.0,
) -> list[dict]:
    """Find colors in a theme similar to the target.

    Args:
        theme: Parsed theme data dict.
        target_color: Hex color string to match against.
        max_delta_e: Maximum ΔE for inclusion.

    Returns:
        Sorted list of dicts with ``location``, ``key``,
        ``hex``, and ``delta_e`` keys.  Empty list on
        invalid input.
    """
    target_rgb = hex_to_rgb(target_color)
    if not target_rgb:
        return []

    target_lab = rgb_to_lab(*target_rgb)
    ui_colors = extract_colors(theme)
    syntax_colors = extract_syntax_colors(theme)

    similar: list[dict] = []

    for key, info in ui_colors.items():
        try:
            de = delta_e_76(target_lab, info["lab"])
            if de <= max_delta_e:
                similar.append(
                    {
                        "location": "ui",
                        "key": key,
                        "hex": info["hex"],
                        "delta_e": de,
                    }
                )
        except (KeyError, TypeError, ValueError):
            continue

    for key, info in syntax_colors.items():
        try:
            de = delta_e_76(target_lab, info["lab"])
            if de <= max_delta_e:
                similar.append(
                    {
                        "location": "syntax",
                        "key": key,
                        "hex": info["hex"],
                        "delta_e": de,
                    }
                )
        except (KeyError, TypeError, ValueError):
            continue

    similar.sort(key=lambda x: x["delta_e"])
    return similar


# ── Display wrappers (Rich) ──────────────────────────────────────


def analyze_color_replacement(
    theme: dict,
    old_color: str,
    new_color: str,
    console: Console | None = None,
) -> dict:
    """Analyze and display the impact of a color replacement.

    Args:
        theme: Parsed theme data dict.
        old_color: Current hex color string.
        new_color: Replacement hex color string.
        console: Rich console for output (created if None).

    Returns:
        Same dict as ``compute_replacement_impact``.
    """
    if console is None:
        console = Console()

    result = compute_replacement_impact(
        theme, old_color, new_color
    )

    if "error" in result:
        console.print(
            "[bold red]Error:[/bold red] Invalid color hex code"
        )
        return result

    console.print("\n[bold]Impact Analysis:[/bold]")
    console.print(
        f"  Affected UI colors: "
        f"[cyan]{len(result['affected_ui'])}[/cyan]"
    )
    console.print(
        f"  Affected syntax scopes: "
        f"[cyan]{len(result['affected_syntax'])}[/cyan]"
    )
    console.print(
        f"  Perceptual difference (ΔE): "
        f"[cyan]{result['delta_e']:.2f}[/cyan]"
    )

    if result["affected_ui"]:
        console.print(
            "\n[bold yellow]Affected UI Colors:[/bold yellow]"
        )
        for key in result["affected_ui"][:10]:
            console.print(f"  • {key}")
        if len(result["affected_ui"]) > 10:
            console.print(
                f"  ... and "
                f"{len(result['affected_ui']) - 10} more"
            )

    if result["affected_syntax"]:
        console.print(
            "\n[bold yellow]Affected Syntax Scopes:"
            "[/bold yellow]"
        )
        for key in result["affected_syntax"][:10]:
            console.print(f"  • {key}")
        if len(result["affected_syntax"]) > 10:
            console.print(
                f"  ... and "
                f"{len(result['affected_syntax']) - 10} more"
            )

    if result["contrast_changes"]:
        console.print("\n[bold]Contrast Changes:[/bold]")
        for change in result["contrast_changes"]:
            arrow = (
                "↑"
                if change["change"] > 0
                else "↓" if change["change"] < 0 else "→"
            )
            color = (
                "green"
                if change["change"] > 0
                else "red" if change["change"] < 0 else "dim"
            )
            console.print(
                f"  vs {change['context']}: "
                f"{change['old_contrast']:.2f} {arrow} "
                f"{change['new_contrast']:.2f} "
                f"[{color}]({change['change']:+.2f})"
                f"[/{color}]"
            )

    if result["recommendations"]:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in result["recommendations"]:
            console.print(f"  {rec}")

    return result


def suggest_replacements(
    base_color: str,
    target_color: str | None = None,
    harmony_type: str = "all",
    console: Console | None = None,
):
    """Display harmony-based color suggestions.

    Args:
        base_color: Hex color string to generate harmonies for.
        target_color: Optional hex to compare against.
        harmony_type: Harmony type filter.
        console: Rich console for output.
    """
    if console is None:
        console = Console()

    data = compute_harmony_suggestions(
        base_color, harmony_type
    )

    if "error" in data:
        console.print(
            "[bold red]Error:[/bold red] Invalid base color"
        )
        return

    base_hsl = data["base"]["hsl"]
    console.print(f"\n[bold]Base Color:[/bold] {base_color}")
    console.print(
        f"  HSL: H:{base_hsl[0]:.1f} "
        f"S:{base_hsl[1]:.1f}% L:{base_hsl[2]:.1f}%"
    )

    table = Table(
        show_header=True, header_style="bold cyan"
    )
    table.add_column("Type", style="dim")
    table.add_column("Hex", style="bold")
    table.add_column("HSL", style="italic")
    table.add_column("Preview", justify="center")
    table.add_column("ΔE", justify="right")

    for sug in data["suggestions"]:
        hex_color = sug["hex"]
        h, s, l_val = sug["hsl"]
        tc = swatch_text_color(hex_color)
        hex_clean = hex_color.lstrip("#")[:6]
        preview = Text(
            " Sample ",
            style=Style(bgcolor=hex_clean, color=tc),
        )

        rotation = sug["rotation"]
        if abs(rotation - 180) < 5:
            type_name = "Complementary"
        elif abs(rotation - 30) < 5:
            type_name = "Analogous (+30°)"
        elif abs(rotation + 30) < 5:
            type_name = "Analogous (-30°)"
        elif abs(rotation - 120) < 5:
            type_name = "Triadic (120°)"
        elif abs(rotation - 240) < 5:
            type_name = "Triadic (240°)"
        elif abs(rotation - 150) < 5:
            type_name = "Split (150°)"
        elif abs(rotation - 210) < 5:
            type_name = "Split (210°)"
        else:
            type_name = f"Harmony ({rotation:.0f}°)"

        table.add_row(
            type_name,
            hex_color,
            f"H:{h:.0f} S:{s:.0f}% L:{l_val:.0f}%",
            preview,
            f"{sug['delta_e']:.1f}",
        )

    console.print(table)

    if target_color:
        target_rgb = hex_to_rgb(target_color)
        base_rgb = hex_to_rgb(base_color)
        if target_rgb and base_rgb:
            target_lab = rgb_to_lab(*target_rgb)
            base_lab = rgb_to_lab(*base_rgb)
            target_de = delta_e_76(base_lab, target_lab)
            target_cr = contrast_ratio(
                base_rgb, target_rgb
            )

            console.print(
                f"\n[bold]Target Comparison:[/bold] "
                f"{target_color}"
            )
            console.print(
                f"  ΔE from base: {target_de:.2f}"
            )
            console.print(
                f"  Contrast ratio: {target_cr:.2f}:1"
            )

    console.print("\n[bold]Lightness Variations:[/bold]")
    var_table = Table(show_header=False, box=None)
    var_table.add_column("Name", style="dim")
    var_table.add_column("Hex", style="bold")
    var_table.add_column("Preview", justify="center")

    for v in data["variations"]:
        tc = swatch_text_color(v["hex"])
        hex_clean = v["hex"].lstrip("#")[:6]
        preview = Text(
            " Var ",
            style=Style(bgcolor=hex_clean, color=tc),
        )
        var_table.add_row(v["name"], v["hex"], preview)

    console.print(var_table)


def find_similar_colors_in_theme(
    theme: dict,
    target_color: str,
    max_delta_e: float = 15.0,
    console: Console | None = None,
) -> list[dict]:
    """Find and display colors similar to the target.

    Args:
        theme: Parsed theme data dict.
        target_color: Hex color to match against.
        max_delta_e: Maximum ΔE for inclusion.
        console: Rich console for output.

    Returns:
        Sorted list from ``compute_similar_colors``.
    """
    if console is None:
        console = Console()

    similar = compute_similar_colors(
        theme, target_color, max_delta_e
    )

    if not similar:
        if not hex_to_rgb(target_color):
            console.print(
                "[bold red]Error:[/bold red] "
                "Invalid target color"
            )
        else:
            console.print(
                f"\n[dim]No similar colors found "
                f"(ΔE ≤ {max_delta_e})[/dim]"
            )
        return similar

    console.print(
        f"\n[bold]Found {len(similar)} similar color(s) "
        f"(ΔE ≤ {max_delta_e}):[/bold]"
    )

    table = Table(
        show_header=True, header_style="bold green"
    )
    table.add_column("Location", style="dim")
    table.add_column("Key/Scope", style="cyan")
    table.add_column("Hex", style="bold")
    table.add_column("ΔE", justify="right")
    table.add_column("Preview", justify="center")

    for item in similar[:20]:
        tc = swatch_text_color(item["hex"])
        hex_clean = item["hex"].lstrip("#")[:6]
        preview = Text(
            " Sample ",
            style=Style(bgcolor=hex_clean, color=tc),
        )

        location = (
            "UI" if item["location"] == "ui" else "Syntax"
        )
        key = item["key"]
        table.add_row(
            location,
            key[:40] + "..." if len(key) > 40 else key,
            item["hex"],
            f"{item['delta_e']:.1f}",
            preview,
        )

    console.print(table)

    if len(similar) > 20:
        console.print(
            f"[dim]... and {len(similar) - 20} more[/dim]"
        )

    return similar
