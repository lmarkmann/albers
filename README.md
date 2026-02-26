# Patina Theme Color Analyzer

Analyzes color choices across all Patina theme variants using color theory principles. Produces reports on harmony, contrast, accessibility, and emotional response based on established color psychology research.

Colors are sourced directly from the VS Code theme files in `vscode/themes/`.

## Structure

```
color_analysis/
├── pyproject.toml
└── src/color_analysis/
    ├── __init__.py
    ├── __main__.py       CLI entry point
    ├── conversions.py    hex/rgb/hsl/lab conversions, contrast ratio, delta-e
    ├── harmony.py        color harmony relationship detection
    ├── psychology.py     emotional and saturation response maps
    ├── reports.py        all report generators
    └── theme_loader.py   theme file loading and color extraction
```

## Running

Requires [uv](https://docs.astral.sh/uv/).

```sh
# Run all reports
uv run python -m color_analysis

# Run a specific report
uv run python -m color_analysis --report palette
uv run python -m color_analysis --report harmony
uv run python -m color_analysis --report contrast
uv run python -m color_analysis --report psychology
uv run python -m color_analysis --report cross
```

## Reports

| Report | Description |
|---|---|
| `palette` | Unique colors per theme with HSL values, temperature, and contrast ratio |
| `harmony` | Detected harmony relationships (complementary, analogous, triadic) and temperature balance |
| `contrast` | WCAG AA/AAA contrast for main text, syntax tokens, and borders |
| `psychology` | Emotional associations, saturation mood, and predicted user responses |
| `cross` | Hue consistency for shared scopes across all theme variants |
