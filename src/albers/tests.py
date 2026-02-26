"""Test functions for color analysis functionality.

Each test is a standalone function that returns a tuple of (passed: bool, details: str).
These tests can be run individually via the CLI or all together.
"""

from .conversions import (
    hex_to_rgb,
    rgb_to_hex,
    rgb_to_hsl,
    hsl_to_rgb,
    rgb_to_lab,
    delta_e_76,
    relative_luminance,
    contrast_ratio,
    color_temperature,
    get_contrast_category,
    rotate_hue,
    generate_harmony_colors,
)
from .harmony import analyze_harmony
from .psychology import classify_emotion
from .theme_loader import load_themes, extract_colors, extract_syntax_colors
from .replacement import analyze_color_replacement, find_similar_colors_in_theme


def test_theme_loading() -> tuple[bool, str]:
    """Test that themes can be loaded from the themes directory."""
    try:
        themes = load_themes()

        if not themes:
            return False, "No themes loaded - check THEMES_DIR path"

        if len(themes) < 1:
            return False, f"Expected at least 1 theme, got {len(themes)}"

        # Verify each theme has required structure
        for name, theme in themes.items():
            if "colors" not in theme:
                return False, f"Theme '{name}' missing 'colors' key"
            if "tokenColors" not in theme:
                return False, f"Theme '{name}' missing 'tokenColors' key"

        return True, f"Loaded {len(themes)} theme(s) successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_color_conversions() -> tuple[bool, str]:
    """Test color conversion functions for accuracy."""
    errors = []

    # Test hex_to_rgb
    test_cases_hex = [
        ("#ff0000", (255, 0, 0)),
        ("#00ff00", (0, 255, 0)),
        ("#0000ff", (0, 0, 255)),
        ("#ffffff", (255, 255, 255)),
        ("#000000", (0, 0, 0)),
        ("#ff5555", (255, 85, 85)),
        ("#FF5555", (255, 85, 85)),  # Test uppercase
        ("ff5555", (255, 85, 85)),   # Test without #
    ]

    for hex_input, expected in test_cases_hex:
        result = hex_to_rgb(hex_input)
        if result != expected:
            errors.append(f"hex_to_rgb({hex_input}) = {result}, expected {expected}")

    # Test rgb_to_hex
    test_cases_rgb = [
        ((255, 0, 0), "#ff0000"),
        ((0, 255, 0), "#00ff00"),
        ((0, 0, 255), "#0000ff"),
        ((255, 255, 255), "#ffffff"),
        ((0, 0, 0), "#000000"),
    ]

    for rgb_input, expected in test_cases_rgb:
        result = rgb_to_hex(*rgb_input)
        if result != expected:
            errors.append(f"rgb_to_hex{rgb_input} = {result}, expected {expected}")

    # Test rgb_to_hsl (approximate due to floating point)
    red_hsl = rgb_to_hsl(255, 0, 0)
    if not (abs(red_hsl[0] - 0) < 1 or abs(red_hsl[0] - 360) < 1):
        errors.append(f"rgb_to_hsl(255,0,0) hue = {red_hsl[0]}, expected ~0 or ~360")
    if abs(red_hsl[1] - 100) > 1:
        errors.append(f"rgb_to_hsl(255,0,0) saturation = {red_hsl[1]}, expected ~100")

    # Test hsl_to_rgb (roundtrip)
    test_hsl = (120, 100, 50)  # Green
    rgb_back = hsl_to_rgb(*test_hsl)
    hsl_back = rgb_to_hsl(*rgb_back)
    if abs(hsl_back[0] - test_hsl[0]) > 1:
        errors.append(f"HSL roundtrip failed: {test_hsl} -> {rgb_back} -> {hsl_back}")

    # Test contrast ratio (known values)
    white = (255, 255, 255)
    black = (0, 0, 0)
    cr = contrast_ratio(white, black)
    if abs(cr - 21.0) > 0.1:
        errors.append(f"contrast_ratio(white, black) = {cr}, expected ~21.0")

    # Test same color contrast
    cr_same = contrast_ratio(white, white)
    if abs(cr_same - 1.0) > 0.01:
        errors.append(f"contrast_ratio(same color) = {cr_same}, expected ~1.0")

    # Test color temperature
    if color_temperature(0, 50) != "warm":
        errors.append("color_temperature(0, 50) should be 'warm'")
    if color_temperature(180, 50) != "cool":
        errors.append("color_temperature(180, 50) should be 'cool'")
    if color_temperature(0, 0) != "neutral":
        errors.append("color_temperature(0, 0) should be 'neutral'")

    # Test contrast category
    if get_contrast_category(21.0) != "AAA":
        errors.append("get_contrast_category(21.0) should be 'AAA'")
    if get_contrast_category(5.0) != "AA":
        errors.append("get_contrast_category(5.0) should be 'AA'")
    if get_contrast_category(3.5) != "AA Large":
        errors.append("get_contrast_category(3.5) should be 'AA Large'")
    if get_contrast_category(2.0) != "Fail":
        errors.append("get_contrast_category(2.0) should be 'Fail'")

    # Test hue rotation
    if abs(rotate_hue(0, 180) - 180) > 0.01:
        errors.append(f"rotate_hue(0, 180) = {rotate_hue(0, 180)}, expected 180")
    if abs(rotate_hue(300, 120) - 60) > 0.01:
        errors.append(f"rotate_hue(300, 120) = {rotate_hue(300, 120)}, expected 60")

    if errors:
        return False, "; ".join(errors[:3])  # Show first 3 errors

    return True, "All conversion tests passed"


def test_contrast_analysis() -> tuple[bool, str]:
    """Test contrast ratio calculations and WCAG compliance."""
    try:
        # Test known contrast ratios
        white = (255, 255, 255)
        black = (0, 0, 0)
        gray = (128, 128, 128)

        # White on black should be ~21:1
        cr1 = contrast_ratio(white, black)
        if not (20.9 < cr1 < 21.1):
            return False, f"White/black contrast = {cr1}, expected ~21.0"

        # Gray on black
        cr2 = contrast_ratio(gray, black)
        if cr2 < 1.0 or cr2 > 10.0:
            return False, f"Gray/black contrast = {cr2}, unexpected value"

        # Test luminance calculations
        lum_white = relative_luminance(*white)
        lum_black = relative_luminance(*black)

        if abs(lum_white - 1.0) > 0.01:
            return False, f"White luminance = {lum_white}, expected ~1.0"
        if abs(lum_black - 0.0) > 0.01:
            return False, f"Black luminance = {lum_black}, expected ~0.0"

        # Test with theme data if available
        themes = load_themes()
        if themes:
            for name, theme in themes.items():
                bg_hex = theme.get("colors", {}).get("editor.background", "#000000")
                fg_hex = theme.get("colors", {}).get("editor.foreground", "#ffffff")
                bg_rgb = hex_to_rgb(bg_hex)
                fg_rgb = hex_to_rgb(fg_hex)

                if bg_rgb and fg_rgb:
                    cr = contrast_ratio(fg_rgb, bg_rgb)
                    if cr < 1.0:
                        return False, f"Theme {name}: Invalid contrast ratio {cr}"

        return True, "Contrast analysis working correctly"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_harmony_detection() -> tuple[bool, str]:
    """Test color harmony detection algorithms."""
    try:
        # Test complementary detection
        comp_harmony = analyze_harmony([0, 180])
        has_complementary = any(r[0] == "complementary" for r in comp_harmony.get("relationships", []))
        if not has_complementary:
            return False, "Failed to detect complementary colors (0° and 180°)"

        # Test analogous detection
        analog_harmony = analyze_harmony([0, 30])
        has_analogous = any(r[0] == "analogous" for r in analog_harmony.get("relationships", []))
        if not has_analogous:
            return False, "Failed to detect analogous colors (0° and 30°)"

        # Test monochromatic (single hue)
        mono_harmony = analyze_harmony([120])
        if mono_harmony.get("type") != "monochromatic":
            return False, "Single hue should be classified as monochromatic"

        # Test empty input
        empty_harmony = analyze_harmony([])
        if empty_harmony.get("type") != "monochromatic":
            return False, "Empty input should return monochromatic"

        # Test with theme data
        themes = load_themes()
        if themes:
            for name, theme in themes.items():
                syntax = extract_syntax_colors(theme)
                hues = []
                for _key, info in syntax.items():
                    h, s, _lgt = info["hsl"]
                    if s > 15:
                        hues.append(h)

                if hues:
                    harmony = analyze_harmony(hues)
                    if "distinct_hues" not in harmony:
                        return False, f"Theme {name}: Missing distinct_hues in result"

        return True, "Harmony detection working correctly"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_palette_report() -> tuple[bool, str]:
    """Test palette extraction and reporting."""
    try:
        themes = load_themes()
        if not themes:
            return True, "No themes to test (skipped)"

        for name, theme in themes.items():
            ui_colors = extract_colors(theme)
            syntax_colors = extract_syntax_colors(theme)

            if not ui_colors:
                return False, f"Theme {name}: No UI colors extracted"

            # Verify color data structure
            for key, info in ui_colors.items():
                if "hex" not in info:
                    return False, f"Theme {name}: Missing 'hex' in color data"
                if "rgb" not in info:
                    return False, f"Theme {name}: Missing 'rgb' in color data"
                if "hsl" not in info:
                    return False, f"Theme {name}: Missing 'hsl' in color data"
                if "lab" not in info:
                    return False, f"Theme {name}: Missing 'lab' in color data"

                # Verify RGB values are valid
                r, g, b = info["rgb"]
                if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                    return False, f"Theme {name}: Invalid RGB values {info['rgb']}"

            # Verify syntax colors
            if not syntax_colors:
                return False, f"Theme {name}: No syntax colors extracted"

        return True, f"Palette extraction working for {len(themes)} theme(s)"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_psychology_analysis() -> tuple[bool, str]:
    """Test color psychology/emotion classification."""
    try:
        # Test known color associations
        # Red should be associated with energy/passion
        red_emotion = classify_emotion(0, 80, 50)
        if "hue_emotion" not in red_emotion:
            return False, "Missing hue_emotion in classification"

        # Test temperature classification
        if red_emotion.get("temperature") != "warm":
            return False, f"Red should be warm, got {red_emotion.get('temperature')}"

        # Test blue (cool)
        blue_emotion = classify_emotion(200, 80, 50)
        if blue_emotion.get("temperature") != "cool":
            return False, f"Blue should be cool, got {blue_emotion.get('temperature')}"

        # Test gray (neutral)
        gray_emotion = classify_emotion(0, 0, 50)
        if gray_emotion.get("temperature") != "neutral":
            return False, f"Gray should be neutral, got {gray_emotion.get('temperature')}"

        # Test lightness classification
        if "lightness_class" not in red_emotion:
            return False, "Missing lightness_class in classification"

        # Test saturation classification
        if "saturation_class" not in red_emotion:
            return False, "Missing saturation_class in classification"

        return True, "Psychology analysis working correctly"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_replacement_analysis() -> tuple[bool, str]:
    """Test color replacement analysis functionality."""
    try:
        themes = load_themes()
        if not themes:
            return True, "No themes to test (skipped)"

        # Test with a sample color replacement
        test_old = "#ff5555"
        test_new = "#ff6666"

        for name, theme in themes.items():
            result = analyze_color_replacement(theme, test_old, test_new, console=None)

            if "error" in result:
                return False, f"Replacement analysis returned error: {result['error']}"

            if "affected_ui" not in result:
                return False, "Missing 'affected_ui' in result"

            if "affected_syntax" not in result:
                return False, "Missing 'affected_syntax' in result"

            if "delta_e" not in result:
                return False, "Missing 'delta_e' in result"

            # Delta E should be reasonable for similar colors
            if result["delta_e"] < 0 or result["delta_e"] > 100:
                return False, f"Unexpected delta_e: {result['delta_e']}"

        # Test find_similar_colors_in_theme
        for name, theme in themes.items():
            similar = find_similar_colors_in_theme(theme, test_old, max_delta_e=20.0, console=None)

            if not isinstance(similar, list):
                return False, "find_similar_colors_in_theme should return a list"

            # Verify structure of results
            for item in similar:
                if "location" not in item:
                    return False, "Missing 'location' in similar color result"
                if "key" not in item:
                    return False, "Missing 'key' in similar color result"
                if "hex" not in item:
                    return False, "Missing 'hex' in similar color result"
                if "delta_e" not in item:
                    return False, "Missing 'delta_e' in similar color result"

        return True, "Replacement analysis working correctly"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_harmony_generation() -> tuple[bool, str]:
    """Test harmony color generation."""
    try:
        base_h, base_s, base_l = 180, 70, 50

        # Test complementary
        comp = generate_harmony_colors(base_h, base_s, base_l, "complementary")
        if len(comp) < 1:
            return False, "Complementary harmony should return at least 1 color"

        # Verify complementary is ~180° from base
        if comp:
            comp_h = comp[0][0]
            expected = (base_h + 180) % 360
            if abs(comp_h - expected) > 1:
                return False, f"Complementary hue {comp_h}, expected {expected}"

        # Test analogous
        analog = generate_harmony_colors(base_h, base_s, base_l, "analogous")
        if len(analog) < 2:
            return False, "Analogous harmony should return 2 colors"

        # Test triadic
        triadic = generate_harmony_colors(base_h, base_s, base_l, "triadic")
        if len(triadic) < 2:
            return False, "Triadic harmony should return 2 colors"

        # Test all harmonies
        all_harmonies = generate_harmony_colors(base_h, base_s, base_l, "all")
        if len(all_harmonies) < len(comp):
            return False, "'all' should return at least as many as individual types"

        return True, "Harmony generation working correctly"
    except Exception as e:
        return False, f"Exception: {str(e)}"
