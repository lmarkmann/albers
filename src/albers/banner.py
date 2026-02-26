"""Homage to Josef Albers — rendered as nested squares on first run."""

from rich.console import Console
from rich.style import Style
from rich.text import Text


# Four layers of nested squares, inspired by Albers' "Homage to the Square"
# series (1950–1976). Colors chosen to evoke his warm/cool palette studies.
_LAYERS = [
    "#3d6b5e",  # outer — deep teal
    "#6b9e6e",  # second — muted sage
    "#c4935a",  # third — amber
    "#e8c98a",  # inner — warm gold
]

# Each layer is a pair: (top/bottom rows, side fill character count)
# The square is 19 wide, 9 tall — readable at 80-col terminals.
_WIDTH = 19
_HEIGHT = 9


def _build_square() -> list[Text]:
    """Build the nested square as a list of Rich Text lines."""
    lines = []
    half_h = _HEIGHT // 2

    for row in range(_HEIGHT):
        dist_v = min(row, _HEIGHT - 1 - row)
        layer = min(dist_v, len(_LAYERS) - 1)

        line = Text()
        for col in range(_WIDTH):
            dist_h = min(col, _WIDTH - 1 - col)
            cell_layer = min(min(dist_v, dist_h), len(_LAYERS) - 1)
            color = _LAYERS[cell_layer]
            line.append("  ", style=Style(bgcolor=color))

        lines.append(line)

    return lines


def print_banner(console: Console) -> None:
    """Print the Albers homage banner with attribution."""
    square_lines = _build_square()

    # Center the square with attribution alongside
    attribution = [
        "",
        "",
        "  [bold]albers[/bold]",
        "  [dim]a color analysis tool[/dim]",
        "",
        "  after [italic]Josef Albers[/italic]",
        "  [dim]Interaction of Color, 1963[/dim]",
        "",
        "",
    ]

    for i, line in enumerate(square_lines):
        attr = attribution[i] if i < len(attribution) else ""
        console.print(line, end="")
        if attr:
            console.print(attr)
        else:
            console.print()
