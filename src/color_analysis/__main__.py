"""CLI entry point for the Patina Theme Color Analyzer."""

import argparse

from .reports import (
    report_contrast,
    report_cross_theme,
    report_harmony,
    report_palette,
    report_psychology,
)
from .theme_loader import THEMES_DIR, load_themes


def main():
    parser = argparse.ArgumentParser(description="Patina Theme Color Analyzer")
    parser.add_argument(
        "--report",
        choices=["all", "palette", "harmony", "contrast", "psychology", "cross"],
        default="all",
        help="Which report to generate",
    )
    args = parser.parse_args()

    themes = load_themes()
    if not themes:
        print(f"No themes found in {THEMES_DIR}")
        return

    print(f"\nLoaded {len(themes)} themes: {', '.join(themes.keys())}\n")

    reports = {
        "palette": report_palette,
        "harmony": report_harmony,
        "contrast": report_contrast,
        "psychology": report_psychology,
        "cross": report_cross_theme,
    }

    if args.report == "all":
        for report_fn in reports.values():
            report_fn(themes)
            print()
    else:
        reports[args.report](themes)


if __name__ == "__main__":
    main()
