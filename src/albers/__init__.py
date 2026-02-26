"""Color analysis tool for working with theme palettes.

Harmony, contrast, accessibility, and psychological reads on a palette.
Named after Josef Albers, whose Interaction of Color (1963) showed that
color is never perceived in isolation — always relative to its context.
"""

__version__ = "0.1.0"

# conversions
from .conversions import (
    color_temperature,
    contrast_ratio,
    delta_e_76,
    delta_e_2000,
    generate_harmony_colors,
    get_contrast_category,
    get_text_color_for_background,
    hex_to_rgb,
    hsl_to_rgb,
    is_color_dark,
    relative_luminance,
    rgb_to_hex,
    rgb_to_hsl,
    rgb_to_lab,
    rotate_hue,
    swatch_text_color,
)

# harmony
from .harmony import analyze_harmony

# psychology
from .psychology import classify_emotion

# theme loading
from .theme_loader import (
    extract_colors,
    extract_syntax_colors,
    load_palette_from_dict,
    load_palette_from_directory,
    load_palette_from_json,
    load_themes,
)

# analysis
from .reports import (
    analyze_contrast,
    analyze_cross_theme,
    analyze_harmony_report,
    analyze_palette,
    analyze_psychology_report,
)
from .replacement import (
    compute_harmony_suggestions,
    compute_replacement_impact,
    compute_similar_colors,
)

__all__ = [
    # conversions
    "hex_to_rgb",
    "rgb_to_hex",
    "rgb_to_hsl",
    "hsl_to_rgb",
    "rgb_to_lab",
    "delta_e_76",
    "delta_e_2000",
    "relative_luminance",
    "contrast_ratio",
    "color_temperature",
    "get_contrast_category",
    "is_color_dark",
    "get_text_color_for_background",
    "swatch_text_color",
    "rotate_hue",
    "generate_harmony_colors",
    # harmony
    "analyze_harmony",
    # psychology
    "classify_emotion",
    # theme loading
    "load_themes",
    "load_palette_from_dict",
    "load_palette_from_json",
    "load_palette_from_directory",
    "extract_colors",
    "extract_syntax_colors",
    # analysis (computation)
    "analyze_palette",
    "analyze_harmony_report",
    "analyze_contrast",
    "analyze_psychology_report",
    "analyze_cross_theme",
    "compute_replacement_impact",
    "compute_harmony_suggestions",
    "compute_similar_colors",
]
