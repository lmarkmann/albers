"""Report generators for theme analysis."""

from collections import defaultdict

from .conversions import (
    color_temperature,
    contrast_ratio,
    delta_e_76,
    hex_to_rgb,
    rgb_to_hsl,
    rgb_to_lab,
)
from .harmony import analyze_harmony
from .psychology import SATURATION_RESPONSE, classify_emotion
from .theme_loader import extract_colors, extract_syntax_colors


def report_palette(themes):
    """Show the unique palette per theme with HSL breakdown."""
    print("=" * 80)
    print("PALETTE OVERVIEW")
    print("=" * 80)

    for name, theme in themes.items():
        ui_colors = extract_colors(theme)
        syntax_colors = extract_syntax_colors(theme)

        # Deduplicate by hex
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

        print(f"\n{'─' * 80}")
        print(f"  {name}")
        print(f"  Base: {theme.get('base')}")
        print(f"{'─' * 80}")

        bg_hex = theme["colors"].get("editor.background", "#000000")
        bg_rgb = hex_to_rgb(bg_hex)

        print(f"\n  UI Colors ({len(unique_ui)} unique):")
        for hex_val, data in sorted(
            unique_ui.items(), key=lambda x: x[1]["color"]["hsl"][2]
        ):
            h, s, lgt = data["color"]["hsl"]
            temp = color_temperature(h, s)
            usage_count = len(data["used_by"])
            cr = contrast_ratio(data["color"]["rgb"], bg_rgb) if bg_rgb else 0
            print(
                f"    {hex_val}  H:{h:5.1f} S:{s:4.1f}% L:{lgt:4.1f}%  "
                f"{temp:13s}  CR:{cr:5.2f}  used {usage_count}x"
            )

        print(f"\n  Syntax Colors ({len(unique_syntax)} unique):")
        for hex_val, data in sorted(
            unique_syntax.items(), key=lambda x: x[1]["color"]["hsl"][0]
        ):
            h, s, lgt = data["color"]["hsl"]
            temp = color_temperature(h, s)
            cr = contrast_ratio(data["color"]["rgb"], bg_rgb) if bg_rgb else 0
            scopes_preview = ", ".join(data["used_by"][:3])
            if len(data["used_by"]) > 3:
                scopes_preview += f" +{len(data['used_by']) - 3}"
            print(
                f"    {hex_val}  H:{h:5.1f} S:{s:4.1f}% L:{lgt:4.1f}%  "
                f"{temp:13s}  CR:{cr:5.2f}  {scopes_preview}"
            )


def report_harmony(themes):
    """Analyze color harmony relationships in syntax palettes."""
    print("=" * 80)
    print("COLOR HARMONY ANALYSIS")
    print("=" * 80)

    for name, theme in themes.items():
        syntax_colors = extract_syntax_colors(theme)

        # Get unique saturated hues (skip grays)
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

        print(f"\n{'─' * 80}")
        print(f"  {name}")
        print(f"{'─' * 80}")
        print(f"  Distinct chromatic hues: {harmony['distinct_hues']}")
        if harmony.get("hue_values"):
            print(f"  Hue distribution: {harmony['hue_values']}")
            print(f"  Hue range: {harmony['hue_range']}°")

        if harmony.get("relationships"):
            print("\n  Detected relationships:")
            for rel_type, h1, h2, diff in harmony["relationships"]:
                print(f"    {rel_type:30s}  {h1:3.0f}° ↔ {h2:3.0f}°  (Δ{diff:.0f}°)")
        else:
            print("  No strong classical harmony relationships detected.")

        # Temperature balance
        temps = defaultdict(int)
        for _key, info in syntax_colors.items():
            h, s, _lgt = info["hsl"]
            temps[color_temperature(h, s)] += 1

        total = sum(temps.values())
        print("\n  Temperature balance:")
        for t in ["warm", "cool", "transitional", "neutral"]:
            count = temps.get(t, 0)
            pct = count / total * 100 if total else 0
            bar = "█" * int(pct / 2)
            print(f"    {t:14s} {count:3d} ({pct:4.1f}%)  {bar}")


def report_contrast(themes):
    """WCAG contrast analysis for key UI and syntax elements."""
    print("=" * 80)
    print("CONTRAST & ACCESSIBILITY ANALYSIS")
    print("=" * 80)

    for name, theme in themes.items():
        colors = theme.get("colors", {})
        bg_hex = colors.get("editor.background", "#000000")
        bg_rgb = hex_to_rgb(bg_hex)
        fg_hex = colors.get("editor.foreground", "#ffffff")
        fg_rgb = hex_to_rgb(fg_hex)

        print(f"\n{'─' * 80}")
        print(f"  {name}")
        print(f"{'─' * 80}")

        # Main text contrast
        if bg_rgb and fg_rgb:
            cr = contrast_ratio(fg_rgb, bg_rgb)
            wcag_aa = "PASS" if cr >= 4.5 else "FAIL"
            wcag_aaa = "PASS" if cr >= 7.0 else "FAIL"
            print(f"\n  Main text contrast: {cr:.2f}:1  AA={wcag_aa}  AAA={wcag_aaa}")
            print(f"    editor.foreground {fg_hex} on editor.background {bg_hex}")

        # Syntax token contrast against editor background
        syntax = extract_syntax_colors(theme)
        seen = set()
        issues = []
        good = []

        print("\n  Syntax color contrast against editor background:")
        for key, info in sorted(
            syntax.items(), key=lambda x: contrast_ratio(x[1]["rgb"], bg_rgb)
        ):
            h = info["hex"][:7].lower()
            if h in seen:
                continue
            seen.add(h)
            cr = contrast_ratio(info["rgb"], bg_rgb)
            status = "PASS" if cr >= 4.5 else ("WARN" if cr >= 3.0 else "FAIL")
            if status != "PASS":
                issues.append((h, cr, status, key))
            else:
                good.append((h, cr, key))

        if issues:
            print(f"    Issues ({len(issues)}):")
            for h, cr, status, scope in issues:
                print(f"      [{status}] {h}  CR:{cr:.2f}  ({scope})")
        print(f"    Passing: {len(good)} colors with CR >= 4.5:1")

        # Border visibility
        border_keys = [
            k for k in colors if "border" in k.lower() and "bracket" not in k.lower()
        ]
        print("\n  Border visibility (against editor background):")
        for key in sorted(border_keys):
            rgb = hex_to_rgb(colors[key])
            if rgb and bg_rgb:
                cr = contrast_ratio(rgb, bg_rgb)
                de = delta_e_76(rgb_to_lab(*rgb), rgb_to_lab(*bg_rgb))
                visibility = (
                    "visible" if de > 10 else ("subtle" if de > 5 else "barely visible")
                )
                print(f"    {key:45s} {colors[key]:9s}  ΔE:{de:5.1f}  {visibility}")


def report_psychology(themes):
    """Emotional/psychological response predictions based on color theory."""
    print("=" * 80)
    print("COLOR PSYCHOLOGY & EMOTIONAL RESPONSE ANALYSIS")
    print("=" * 80)

    for name, theme in themes.items():
        colors = theme.get("colors", {})
        bg_hex = colors.get("editor.background", "#000000")
        bg_rgb = hex_to_rgb(bg_hex)

        print(f"\n{'─' * 80}")
        print(f"  {name}")
        print(f"{'─' * 80}")

        # Background psychology
        if bg_rgb:
            h, s, lgt = rgb_to_hsl(*bg_rgb)
            emo = classify_emotion(h, s, lgt)
            print(f"\n  Background ({bg_hex}):")
            print(
                f"    Lightness: {emo.get('lightness_class', 'unknown')} "
                f"— {emo.get('lightness_response', '')}"
            )
            print(f"    Temperature: {emo.get('temperature', 'unknown')}")

        # Overall syntax palette mood
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

        avg_sat = 0.0
        if saturations:
            avg_sat = sum(saturations) / len(saturations)
            for sname, (smin, smax, desc) in SATURATION_RESPONSE.items():
                if smin <= avg_sat < smax:
                    print(f"\n  Average syntax saturation: {avg_sat:.1f}% ({sname})")
                    print(f"    → {desc}")
                    break

        if emotions:
            print("\n  Emotional associations (by frequency):")
            for emo_name, count in sorted(emotions.items(), key=lambda x: -x[1]):
                bar = "█" * count
                print(f"    {emo_name:40s} {bar} ({count})")

        if temps:
            total = sum(temps.values())
            warm_pct = temps.get("warm", 0) / total * 100
            cool_pct = temps.get("cool", 0) / total * 100
            print(
                f"\n  Overall palette temperature: "
                f"{warm_pct:.0f}% warm / {cool_pct:.0f}% cool"
            )
            if warm_pct > cool_pct:
                print(
                    "    → Warm-leaning palette: inviting, comfortable, "
                    "natural wood/earth associations"
                )
            elif cool_pct > warm_pct:
                print(
                    "    → Cool-leaning palette: focused, serene, "
                    "technology/precision associations"
                )
            else:
                print(
                    "    → Balanced temperature: versatile, "
                    "neither stimulating nor sedating"
                )

        # Predicted user responses
        print("\n  Predicted user responses:")
        is_dark = theme.get("base") == "vs-dark"
        if is_dark:
            print("    + Reduced eye strain in low-light environments")
            print("    + Lower blue light emission supports circadian rhythm")
            if bg_rgb and rgb_to_hsl(*bg_rgb)[1] > 0:
                print(
                    "    + Warm-tinted background avoids the 'void' feel of pure black"
                )
        else:
            print("    + Natural, paper-like reading experience")
            print("    + Familiar document metaphor reduces cognitive load")
            if bg_rgb:
                _, s, _lgt = rgb_to_hsl(*bg_rgb)
                if s > 5:
                    print("    + Warm tint avoids the clinical feel of pure white")

        if saturations and avg_sat < 40:
            print(
                "    + Muted saturation reduces visual fatigue over extended sessions"
            )
            print(
                "    + Subtle color differences encourage pattern recognition "
                "rather than color-coded reading"
            )
        print(
            "    ? Users preferring vivid/high-contrast themes may find this too subtle"
        )


def report_cross_theme(themes):
    """Compare color choices across theme variants."""
    print("=" * 80)
    print("CROSS-THEME CONSISTENCY ANALYSIS")
    print("=" * 80)

    # Compare syntax color hue consistency
    theme_hues = {}
    for name, theme in themes.items():
        syntax = extract_syntax_colors(theme)
        scope_hues = {}
        for scope, info in syntax.items():
            h, s, _lgt = info["hsl"]
            if s > 10:
                scope_hues[scope] = h
        theme_hues[name] = scope_hues

    # Find scopes present in all themes
    all_scopes = set()
    for sh in theme_hues.values():
        all_scopes |= set(sh.keys())

    common_scopes = all_scopes.copy()
    for sh in theme_hues.values():
        common_scopes &= set(sh.keys())

    print(f"\n  Common scopes across all themes: {len(common_scopes)}")
    print("\n  Hue consistency for shared scopes:")

    inconsistent = []
    for scope in sorted(common_scopes):
        hues = [
            (name, theme_hues[name][scope])
            for name in themes
            if scope in theme_hues[name]
        ]
        if len(hues) >= 2:
            hue_vals = [h for _, h in hues]
            spread = max(hue_vals) - min(hue_vals)
            if spread > 180:
                spread = 360 - spread
            if spread > 15:
                inconsistent.append((scope, hues, spread))

    if inconsistent:
        for scope, hues, spread in sorted(inconsistent, key=lambda x: -x[2]):
            print(f"    {scope:50s}  spread: {spread:.0f}°")
            for tname, h in hues:
                print(f"      {tname:25s}  {h:.0f}°")
    else:
        print("    All shared scopes maintain hue within 15° — excellent consistency!")

    # Background/foreground contrast comparison
    print("\n  Main text contrast comparison:")
    for name, theme in themes.items():
        colors = theme.get("colors", {})
        bg = hex_to_rgb(colors.get("editor.background", "#000000"))
        fg = hex_to_rgb(colors.get("editor.foreground", "#ffffff"))
        if bg and fg:
            cr = contrast_ratio(fg, bg)
            bar = "█" * int(cr)
            print(f"    {name:25s}  {cr:.2f}:1  {bar}")
