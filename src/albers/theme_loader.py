"""Theme file loading and color extraction."""

import json
import os
from pathlib import Path

from .conversions import hex_to_rgb, rgb_to_hsl, rgb_to_lab

# Resolution order:
#   1. ALBERS_THEMES_DIR environment variable
#   2. vscode/themes/ relative to the current working directory
THEMES_DIR = (
    Path(os.environ["ALBERS_THEMES_DIR"])
    if "ALBERS_THEMES_DIR" in os.environ
    else Path.cwd() / "vscode" / "themes"
)


def load_themes(themes_dir: Path | None = None) -> dict[str, dict]:
    """Load VS Code theme JSON files from a directory.

    Scans for files matching patina-*.json. Pass themes_dir explicitly
    or set ALBERS_THEMES_DIR in the environment.
    """
    directory = themes_dir or THEMES_DIR
    themes = {}
    for f in sorted(directory.glob("patina-*.json")):
        with open(f) as fh:
            data = json.load(fh)
            themes[data["name"]] = data
    return themes


def load_palette_from_dict(colors: dict[str, str]) -> dict[str, dict]:
    """Build enriched color records from a {name: hex} dict."""
    result = {}
    for name, hex_val in colors.items():
        rgb = hex_to_rgb(hex_val)
        if rgb:
            hsl = rgb_to_hsl(*rgb)
            lab = rgb_to_lab(*rgb)
            result[name] = {
                "hex": hex_val,
                "rgb": rgb,
                "hsl": hsl,
                "lab": lab,
            }
    return result


def load_palette_from_json(path: str | Path) -> dict[str, dict]:
    """Load a {name: hex} JSON file and enrich each color."""
    with open(path) as fh:
        raw = json.load(fh)
    return load_palette_from_dict(raw)


def load_palette_from_directory(
    directory: str | Path,
    glob_pattern: str = "*.json",
) -> dict[str, dict[str, dict]]:
    """Load multiple palette JSON files from a directory."""
    directory = Path(directory)
    palettes = {}
    for f in sorted(directory.glob(glob_pattern)):
        palettes[f.stem] = load_palette_from_json(f)
    return palettes


def extract_colors(theme: dict) -> dict[str, dict]:
    """Extract all UI colors as dicts with hex, rgb, hsl, lab."""
    colors = {}
    for key, val in theme.get("colors", {}).items():
        rgb = hex_to_rgb(val)
        if rgb:
            hsl = rgb_to_hsl(*rgb)
            lab = rgb_to_lab(*rgb)
            colors[key] = {"hex": val, "rgb": rgb, "hsl": hsl, "lab": lab}
    return colors


def extract_syntax_colors(theme: dict) -> dict[str, dict]:
    """Extract syntax/token colors."""
    colors = {}
    for token in theme.get("tokenColors", []):
        fg = token.get("settings", {}).get("foreground")
        scopes = token.get("scope", [])
        if isinstance(scopes, str):
            scopes = [scopes]
        if fg:
            rgb = hex_to_rgb(fg)
            if rgb:
                hsl = rgb_to_hsl(*rgb)
                lab = rgb_to_lab(*rgb)
                for scope in scopes:
                    colors[scope] = {"hex": fg, "rgb": rgb, "hsl": hsl, "lab": lab}
    for key, val in theme.get("semanticTokenColors", {}).items():
        if isinstance(val, str):
            rgb = hex_to_rgb(val)
            if rgb:
                hsl = rgb_to_hsl(*rgb)
                lab = rgb_to_lab(*rgb)
                colors[f"semantic:{key}"] = {
                    "hex": val,
                    "rgb": rgb,
                    "hsl": hsl,
                    "lab": lab,
                }
    return colors
