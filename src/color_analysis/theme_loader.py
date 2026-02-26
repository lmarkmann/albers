"""Theme file loading and color extraction."""

import json
from pathlib import Path

from .conversions import hex_to_rgb, rgb_to_hsl, rgb_to_lab

THEMES_DIR = Path(__file__).parent.parent.parent.parent / "vscode" / "themes"


def load_themes() -> dict[str, dict]:
    """Load all Patina theme JSON files."""
    themes = {}
    for f in sorted(THEMES_DIR.glob("patina-*.json")):
        with open(f) as fh:
            data = json.load(fh)
            themes[data["name"]] = data
    return themes


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
