"""Report generators for theme analysis.

"In visual perception a color is almost never seen as it really is."
— Josef Albers, Interaction of Color
"""

from collections import defaultdict

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from .conversions import (
    color_temperature,
    contrast_ratio,
    delta_e_76,
    get_contrast_category,
    hex_to_rgb,
    rgb_to_hsl,
    rgb_to_lab,
    swatch_text_color,
)
from .harmony import analyze_harmony
from .psychology import SATURATION_RESPONSE, classify_emotion
from .rich_utils import (
    display_color_bar,
    display_emotion_summary,
    display_temperature_bar,
)
from .theme_loader import extract_colors, extract_syntax_colors


# computation


def analyze_palette(themes: dict) -> dict[str, dict]:
    """Compute palette statistics for each theme."""
    results = {}
    for name, theme in themes.items():
        ui_colors = extract_colors(theme)
        syntax_colors = extract_syntax_colors(theme)

        bg_hex = theme.get("colors", {}).get(
            "editor.background", "#000000"
        )
        bg_rgb = hex_to_rgb(bg_hex)

        unique_ui = {}
        for key, info in ui_colors.items():
            h = info["hex"].lower()[:7]
            if h not in unique_ui:
                unique_ui[h] = {"color": info, "used_by": []}
            unique_ui[h]["used_by"].append(key)

        unique_syntax = {}
        for key, info in syntax_colors.items():
            h = info["hex"].lower()[:7]
            if h not in unique_syntax:
                unique_syntax[h] = {"color": info, "used_by": []}
            unique_syntax[h]["used_by"].append(key)

        # Enrich with derived metrics
        for hex_val, data in unique_ui.items():
            h, s, lgt = data["color"]["hsl"]
            data["temperature"] = color_temperature(h, s)
            data["contrast_ratio"] = (
                contrast_ratio(data["color"]["rgb"], bg_rgb)
                if bg_rgb
                else 0
            )

        for hex_val, data in unique_syntax.items():
            h, s, lgt = data["color"]["hsl"]
            data["temperature"] = color_temperature(h, s)
            data["contrast_ratio"] = (
                contrast_ratio(data["color"]["rgb"], bg_rgb)
                if bg_rgb
                else 0
            )

        results[name] = {
            "unique_ui": unique_ui,
            "unique_syntax": unique_syntax,
            "bg_hex": bg_hex,
            "base": theme.get("base"),
        }
    return results


def analyze_harmony_report(themes: dict) -> dict[str, dict]:
    """Compute harmony analysis for each theme."""
    results = {}
    for name, theme in themes.items():
        syntax_colors = extract_syntax_colors(theme)

        hues = []
        seen_hex = set()
        for _key, info in syntax_colors.items():
            h_hex = info["hex"][:7].lower()
            if h_hex in seen_hex:
                continue
            seen_hex.add(h_hex)
            h, s, lgt = info["hsl"]
            if s > 15 and 10 < lgt < 90:
                hues.append(h)

        harmony = analyze_harmony(hues)

        temps = defaultdict(int)
        for _key, info in syntax_colors.items():
            h, s, _lgt = info["hsl"]
            temps[color_temperature(h, s)] += 1

        results[name] = {
            "harmony": harmony,
            "temperature_distribution": dict(temps),
        }
    return results


def analyze_contrast(
    themes: dict,
    min_contrast: float = 4.5,
) -> dict[str, dict]:
    """Compute contrast/accessibility data for each theme."""
    results = {}
    for name, theme in themes.items():
        colors = theme.get("colors", {})
        bg_hex = colors.get("editor.background", "#000000")
        bg_rgb = hex_to_rgb(bg_hex)
        fg_hex = colors.get("editor.foreground", "#ffffff")
        fg_rgb = hex_to_rgb(fg_hex)

        main_cr = None
        if bg_rgb and fg_rgb:
            main_cr = contrast_ratio(fg_rgb, bg_rgb)

        syntax = extract_syntax_colors(theme)
        seen = set()
        issues = []
        passing = 0

        for key, info in sorted(
            syntax.items(),
            key=lambda x: contrast_ratio(x[1]["rgb"], bg_rgb),
        ):
            h = info["hex"][:7].lower()
            if h in seen:
                continue
            seen.add(h)
            cr = contrast_ratio(info["rgb"], bg_rgb)

            if cr >= min_contrast:
                passing += 1
            else:
                status = "WARN" if cr >= 3.0 else "FAIL"
                issues.append(
                    {
                        "hex": h,
                        "cr": cr,
                        "status": status,
                        "scope": key,
                    }
                )

        border_keys = [
            k
            for k in colors
            if "border" in k.lower() and "bracket" not in k.lower()
        ]
        borders = []
        for key in sorted(border_keys)[:5]:
            rgb = hex_to_rgb(colors[key])
            if rgb and bg_rgb:
                cr = contrast_ratio(rgb, bg_rgb)
                de = delta_e_76(
                    rgb_to_lab(*rgb), rgb_to_lab(*bg_rgb)
                )
                borders.append(
                    {
                        "key": key,
                        "hex": colors[key],
                        "cr": cr,
                        "delta_e": de,
                    }
                )

        results[name] = {
            "bg_hex": bg_hex,
            "fg_hex": fg_hex,
            "main_cr": main_cr,
            "issues": issues,
            "passing": passing,
            "borders": borders,
        }
    return results


def analyze_psychology_report(themes: dict) -> dict[str, dict]:
    """Compute color psychology data for each theme."""
    results = {}
    for name, theme in themes.items():
        colors = theme.get("colors", {})
        bg_hex = colors.get("editor.background", "#000000")
        bg_rgb = hex_to_rgb(bg_hex)

        bg_emotion = None
        if bg_rgb:
            h, s, lgt = rgb_to_hsl(*bg_rgb)
            bg_emotion = classify_emotion(h, s, lgt)

        syntax = extract_syntax_colors(theme)
        seen = set()
        saturations = []
        emotions = defaultdict(int)
        temps = defaultdict(int)

        for _key, info in syntax.items():
            hx = info["hex"][:7].lower()
            if hx in seen:
                continue
            seen.add(hx)
            h, s, lgt = info["hsl"]
            if s > 10:
                saturations.append(s)
                emo = classify_emotion(h, s, lgt)
                if "hue_emotion" in emo:
                    emotions[emo["hue_emotion"]] += 1
                temps[emo["temperature"]] += 1

        avg_sat = (
            sum(saturations) / len(saturations)
            if saturations
            else 0.0
        )

        results[name] = {
            "bg_hex": bg_hex,
            "background_emotion": bg_emotion,
            "avg_saturation": avg_sat,
            "emotions": dict(emotions),
            "temperatures": dict(temps),
            "is_dark": theme.get("base") == "vs-dark",
        }
    return results


def analyze_cross_theme(themes: dict) -> dict:
    """Compute cross-theme consistency data."""
    theme_hues = {}
    for name, theme in themes.items():
        syntax = extract_syntax_colors(theme)
        scope_hues = {}
        for scope, info in syntax.items():
            h, s, _lgt = info["hsl"]
            if s > 10:
                scope_hues[scope] = h
        theme_hues[name] = scope_hues

    all_scopes: set[str] = set()
    for sh in theme_hues.values():
        all_scopes |= set(sh.keys())

    common_scopes = all_scopes.copy()
    for sh in theme_hues.values():
        common_scopes &= set(sh.keys())

    inconsistent = []
    for scope in sorted(common_scopes):
        hues = [
            (tname, theme_hues[tname][scope])
            for tname in themes
            if scope in theme_hues[tname]
        ]
        if len(hues) >= 2:
            hue_vals = [h for _, h in hues]
            spread = max(hue_vals) - min(hue_vals)
            if spread > 180:
                spread = 360 - spread
            if spread > 15:
                inconsistent.append(
                    {
                        "scope": scope,
                        "hues": hues,
                        "spread": spread,
                    }
                )

    contrasts = {}
    for name, theme in themes.items():
        colors = theme.get("colors", {})
        bg = hex_to_rgb(
            colors.get("editor.background", "#000000")
        )
        fg = hex_to_rgb(
            colors.get("editor.foreground", "#ffffff")
        )
        if bg and fg:
            contrasts[name] = contrast_ratio(fg, bg)

    return {
        "common_scopes": len(common_scopes),
        "inconsistent": inconsistent,
        "contrasts": contrasts,
    }


# display


def report_palette(
    themes: dict, console: Console | None = None
):
    """Show the unique palette per theme with HSL breakdown."""
    if console is None:
        console = Console()

    data = analyze_palette(themes)

    console.print(
        Panel("[bold]Palette Overview[/bold]", border_style="cyan")
    )

    for name, info in data.items():
        unique_ui = info["unique_ui"]
        unique_syntax = info["unique_syntax"]
        bg_hex = info["bg_hex"]

        console.print(f"\n[bold]{name}[/bold]")
        console.print(f"[dim]Base: {info['base']}[/dim]")

        # UI Colors table
        console.print(
            f"\n[bold cyan]UI Colors "
            f"({len(unique_ui)} unique):[/bold cyan]"
        )
        ui_table = Table(
            show_header=True, header_style="bold", box=None
        )
        ui_table.add_column("Preview", justify="center")
        ui_table.add_column("Hex", style="bold")
        ui_table.add_column("H", justify="right", style="dim")
        ui_table.add_column("S", justify="right", style="dim")
        ui_table.add_column("L", justify="right", style="dim")
        ui_table.add_column("Temp", style="italic")
        ui_table.add_column("CR", justify="right")
        ui_table.add_column("Usage", justify="right")

        for hex_val, d in sorted(
            unique_ui.items(),
            key=lambda x: x[1]["color"]["hsl"][2],
        ):
            h, s, lgt = d["color"]["hsl"]
            hex_clean = hex_val.lstrip("#")[:6]
            tc = swatch_text_color(hex_val)
            preview = Text(
                "██",
                style=Style(bgcolor=hex_clean, color=tc),
            )

            ui_table.add_row(
                preview,
                hex_val,
                f"{h:5.1f}",
                f"{s:4.1f}%",
                f"{lgt:4.1f}%",
                d["temperature"],
                f"{d['contrast_ratio']:5.2f}",
                f"{len(d['used_by'])}x",
            )

        console.print(ui_table)

        # Syntax Colors table
        console.print(
            f"\n[bold cyan]Syntax Colors "
            f"({len(unique_syntax)} unique):[/bold cyan]"
        )
        syntax_table = Table(
            show_header=True, header_style="bold", box=None
        )
        syntax_table.add_column("Preview", justify="center")
        syntax_table.add_column("Hex", style="bold")
        syntax_table.add_column(
            "H", justify="right", style="dim"
        )
        syntax_table.add_column(
            "S", justify="right", style="dim"
        )
        syntax_table.add_column(
            "L", justify="right", style="dim"
        )
        syntax_table.add_column("Temp", style="italic")
        syntax_table.add_column("CR", justify="right")
        syntax_table.add_column("Scopes", style="italic")

        for hex_val, d in sorted(
            unique_syntax.items(),
            key=lambda x: x[1]["color"]["hsl"][0],
        ):
            h, s, lgt = d["color"]["hsl"]
            hex_clean = hex_val.lstrip("#")[:6]
            tc = swatch_text_color(hex_val)
            preview = Text(
                "██",
                style=Style(bgcolor=hex_clean, color=tc),
            )

            scopes_preview = ", ".join(d["used_by"][:2])
            if len(d["used_by"]) > 2:
                scopes_preview += (
                    f" +{len(d['used_by']) - 2}"
                )

            syntax_table.add_row(
                preview,
                hex_val,
                f"{h:5.1f}",
                f"{s:4.1f}%",
                f"{lgt:4.1f}%",
                d["temperature"],
                f"{d['contrast_ratio']:5.2f}",
                (
                    scopes_preview[:50] + "..."
                    if len(scopes_preview) > 50
                    else scopes_preview
                ),
            )

        console.print(syntax_table)


def report_harmony(
    themes: dict, console: Console | None = None
):
    """Analyze color harmony relationships in syntax palettes."""
    if console is None:
        console = Console()

    data = analyze_harmony_report(themes)

    console.print(
        Panel(
            "[bold]Color Harmony Analysis[/bold]\n"
            "[dim]\"Colors are never seen as they really are.\" — Albers[/dim]",
            border_style="green",
        )
    )

    for name, info in data.items():
        harmony = info["harmony"]
        temps = info["temperature_distribution"]

        console.print(f"\n[bold]{name}[/bold]")
        console.print(
            f"  Distinct chromatic hues: "
            f"[cyan]{harmony['distinct_hues']}[/cyan]"
        )

        if harmony.get("hue_values"):
            console.print(
                f"  Hue values: {harmony['hue_values']}"
            )
            console.print(
                f"  Hue range: "
                f"[yellow]{harmony['hue_range']}°[/yellow]"
            )

        if harmony.get("relationships"):
            console.print(
                "\n  [bold]Detected relationships:[/bold]"
            )
            rel_table = Table(show_header=False, box=None)
            rel_table.add_column("Type", style="cyan")
            rel_table.add_column(
                "H1", justify="right", style="dim"
            )
            rel_table.add_column("", justify="center")
            rel_table.add_column(
                "H2", justify="right", style="dim"
            )
            rel_table.add_column(
                "Δ", justify="right", style="yellow"
            )

            for rel_type, h1, h2, diff in harmony[
                "relationships"
            ]:
                rel_table.add_row(
                    rel_type,
                    f"{h1:3.0f}°",
                    "↔",
                    f"{h2:3.0f}°",
                    f"Δ{diff:.0f}°",
                )

            console.print(rel_table)
        else:
            console.print(
                "  [dim]No strong classical harmony "
                "relationships detected.[/dim]"
            )

        total = sum(temps.values())
        display_temperature_bar(console, temps, total)


def report_contrast(
    themes: dict,
    console: Console | None = None,
    min_contrast: float = 4.5,
):
    """WCAG contrast analysis for key UI and syntax elements."""
    if console is None:
        console = Console()

    data = analyze_contrast(themes, min_contrast)

    console.print(
        Panel(
            f"[bold]Contrast & Accessibility Analysis"
            f"[/bold]\nMinimum CR: {min_contrast}:1",
            border_style="yellow",
        )
    )

    for name, info in data.items():
        console.print(f"\n[bold]{name}[/bold]")

        fg_hex = info["fg_hex"]
        bg_hex = info["bg_hex"]

        if info["main_cr"] is not None:
            cr = info["main_cr"]
            wcag_aa = (
                "[green]PASS[/green]"
                if cr >= 4.5
                else "[red]FAIL[/red]"
            )
            wcag_aaa = (
                "[green]PASS[/green]"
                if cr >= 7.0
                else "[red]FAIL[/red]"
            )

            console.print(
                f"\n  Main text: [bold]{cr:.2f}:1[/bold]"
                f"  AA={wcag_aa}  AAA={wcag_aaa}"
            )

            hex_clean = fg_hex.lstrip("#")[:6]
            bg_clean = bg_hex.lstrip("#")[:6]
            preview = Text(
                "  The quick brown fox jumps "
                "over the lazy dog  ",
                style=Style(
                    bgcolor=bg_clean,
                    color=f"#{hex_clean}",
                ),
            )
            console.print(preview)

        issues = info["issues"]
        if issues:
            console.print(
                f"\n  [bold red]Issues "
                f"({len(issues)}):[/bold red]"
            )
            issue_table = Table(show_header=False, box=None)
            issue_table.add_column("Status", style="bold")
            issue_table.add_column("Color", style="bold")
            issue_table.add_column("CR", justify="right")
            issue_table.add_column("Scope", style="italic")

            for item in issues[:10]:
                ss = (
                    "yellow"
                    if item["status"] == "WARN"
                    else "red"
                )
                scope = item["scope"]
                issue_table.add_row(
                    f"[{ss}]{item['status']}[/{ss}]",
                    item["hex"],
                    f"{item['cr']:.2f}",
                    (
                        scope[:40] + "..."
                        if len(scope) > 40
                        else scope
                    ),
                )

            console.print(issue_table)
            if len(issues) > 10:
                console.print(
                    f"  [dim]... and "
                    f"{len(issues) - 10} more[/dim]"
                )

        console.print(
            f"\n  [green]✓ {info['passing']} colors passing "
            f"(CR >= {min_contrast}:1)[/green]"
        )

        if info["borders"]:
            console.print(
                "\n  [bold]Border visibility:[/bold]"
            )
            for b in info["borders"]:
                de = b["delta_e"]
                visibility = (
                    "[green]visible[/green]"
                    if de > 10
                    else (
                        "[yellow]subtle[/yellow]"
                        if de > 5
                        else "[dim]barely visible[/dim]"
                    )
                )
                console.print(
                    f"    {b['key']:40s} {b['hex']:9s}"
                    f"  ΔE:{de:5.1f}  {visibility}"
                )


def report_psychology(
    themes: dict, console: Console | None = None
):
    """Emotional/psychological response predictions."""
    if console is None:
        console = Console()

    data = analyze_psychology_report(themes)

    console.print(
        Panel(
            "[bold]Color Psychology Analysis[/bold]\n"
            "[dim]\"One and the same color evokes innumerable readings.\" — Albers[/dim]",
            border_style="magenta",
        )
    )

    for name, info in data.items():
        console.print(f"\n[bold]{name}[/bold]")

        emo = info["background_emotion"]
        if emo:
            console.print(
                f"\n  [bold]Background "
                f"({info['bg_hex']}):[/bold]"
            )
            console.print(
                f"    Lightness: [cyan]"
                f"{emo.get('lightness_class', 'unknown')}"
                f"[/cyan] — [dim]"
                f"{emo.get('lightness_response', '')}"
                f"[/dim]"
            )
            console.print(
                f"    Temperature: [cyan]"
                f"{emo.get('temperature', 'unknown')}"
                f"[/cyan]"
            )

        avg_sat = info["avg_saturation"]
        if avg_sat > 0:
            for sname, (smin, smax, desc) in (
                SATURATION_RESPONSE.items()
            ):
                if smin <= avg_sat < smax:
                    console.print(
                        f"\n  [bold]Average saturation:"
                        f"[/bold] {avg_sat:.1f}% ({sname})"
                    )
                    console.print(f"    [dim]→ {desc}[/dim]")
                    break

        display_emotion_summary(console, info["emotions"])

        temps = info["temperatures"]
        if temps:
            total = sum(temps.values())
            warm_pct = temps.get("warm", 0) / total * 100
            cool_pct = temps.get("cool", 0) / total * 100

            console.print(
                f"\n  [bold]Palette temperature:[/bold] "
                f"{warm_pct:.0f}% warm / {cool_pct:.0f}% cool"
            )

            if warm_pct > cool_pct + 10:
                console.print(
                    "    [dim]→ Warm-leaning: inviting, "
                    "comfortable, natural wood/earth[/dim]"
                )
            elif cool_pct > warm_pct + 10:
                console.print(
                    "    [dim]→ Cool-leaning: focused, "
                    "serene, technology/precision[/dim]"
                )
            else:
                console.print(
                    "    [dim]→ Balanced: versatile, "
                    "neither stimulating nor sedating[/dim]"
                )

        console.print(
            "\n  [bold]Predicted user responses:[/bold]"
        )
        if info["is_dark"]:
            console.print(
                "    [green]+[/green] "
                "Reduced eye strain in low-light"
            )
            console.print(
                "    [green]+[/green] "
                "Lower blue light emission"
            )
            if (
                emo
                and emo.get("temperature") != "neutral"
            ):
                console.print(
                    "    [green]+[/green] "
                    "Warm tint avoids 'void' feel"
                )
        else:
            console.print(
                "    [green]+[/green] "
                "Natural, paper-like reading"
            )
            console.print(
                "    [green]+[/green] "
                "Familiar document metaphor"
            )

        if avg_sat > 0 and avg_sat < 40:
            console.print(
                "    [green]+[/green] "
                "Muted saturation reduces fatigue"
            )
            console.print(
                "    [green]+[/green] "
                "Encourages pattern recognition"
            )

        console.print(
            "    [yellow]? Some may prefer "
            "higher contrast[/yellow]"
        )


def report_cross_theme(
    themes: dict, console: Console | None = None
):
    """Compare color choices across theme variants."""
    if console is None:
        console = Console()

    data = analyze_cross_theme(themes)

    console.print(
        Panel("[bold]Cross-Theme Consistency[/bold]", border_style="blue")
    )

    console.print(
        f"\n  Common scopes: "
        f"[cyan]{data['common_scopes']}[/cyan]"
    )

    inconsistent = data["inconsistent"]
    if inconsistent:
        console.print(
            "\n  [bold yellow]Inconsistent hues "
            "(spread > 15°):[/bold yellow]"
        )
        for item in sorted(
            inconsistent, key=lambda x: -x["spread"]
        )[:10]:
            console.print(
                f"\n    [cyan]{item['scope']}[/cyan]"
                f" - spread: "
                f"[yellow]{item['spread']:.0f}°[/yellow]"
            )
            for tname, h in item["hues"]:
                console.print(
                    f"      {tname:25s} {h:.0f}°"
                )
        if len(inconsistent) > 10:
            console.print(
                f"  [dim]... and "
                f"{len(inconsistent) - 10} more[/dim]"
            )
    else:
        console.print(
            "\n  [green]✓ All shared scopes maintain hue "
            "within 15° — excellent![/green]"
        )

    console.print("\n  [bold]Main text contrast:[/bold]")
    contrast_table = Table(show_header=False, box=None)
    contrast_table.add_column("Theme", style="bold")
    contrast_table.add_column("CR", justify="right")
    contrast_table.add_column("Visual", justify="center")

    for tname, cr in data["contrasts"].items():
        bar_length = int(cr / 7 * 20)
        bar = "█" * bar_length
        contrast_table.add_row(
            tname, f"{cr:.2f}:1", f"[dim]{bar}[/dim]"
        )

    console.print(contrast_table)
