# albers - Color Analysis Package

Color analysis for theme palettes: harmony, contrast, and perceptual metrics.

Named after Josef Albers, whose *Interaction of Color* (1963) showed that color
is never perceived in isolation, always relative to its context.

## Install

```sh
uv add albers
# or
pip install albers
```

## Usage

Point it at a directory of VS Code theme JSON files:

```sh
albers --themes-dir ./vscode/themes palette
albers --themes-dir ./vscode/themes harmony
albers --themes-dir ./vscode/themes contrast
albers --themes-dir ./vscode/themes psychology
albers --themes-dir ./vscode/themes all
```

Or set the directory once via environment variable:

```sh
export ALBERS_THEMES_DIR=./vscode/themes
albers palette
albers contrast --min 4.5
```

## Commands

| Command | What it does |
|---|---|
| `palette` | Unique colors per theme with HSL, temperature, and contrast ratio |
| `harmony` | Detected harmony relationships — complementary, analogous, triadic |
| `contrast` | WCAG AA/AAA contrast for main text, syntax tokens, and borders |
| `psychology` | Emotional associations and predicted user responses |
| `cross-theme` | Hue consistency across theme variants |
| `compare #hex1 #hex2` | Side-by-side perceptual comparison of two colors |
| `replace #old #new` | Impact analysis of swapping one color for another |
| `suggest #hex` | Harmony-based color alternatives |
| `all` | Run every report |

## Python API

```python
from albers import hex_to_rgb, contrast_ratio, analyze_harmony

rgb = hex_to_rgb("#4d9375")
cr = contrast_ratio(rgb, (18, 18, 18))

harmony = analyze_harmony([155.0, 94.0, 36.0, 11.0])
```

## License

MIT
