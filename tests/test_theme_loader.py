"""Tests for albers.theme_loader."""

from albers.theme_loader import extract_colors, extract_syntax_colors


MINIMAL_THEME = {
    "name": "Test Theme",
    "type": "dark",
    "colors": {
        "editor.background": "#121212",
        "editor.foreground": "#d4d4d4",
        "activityBar.background": "#1a1a1a",
    },
    "tokenColors": [
        {
            "scope": ["keyword", "storage.type"],
            "settings": {"foreground": "#4d9375"},
        },
        {
            "scope": "string",
            "settings": {"foreground": "#c98a7d"},
        },
    ],
    "semanticTokenColors": {
        "function": "#80a665",
        "type": "#5da9a7",
    },
}


class TestExtractColors:
    def test_returns_dict(self):
        result = extract_colors(MINIMAL_THEME)
        assert isinstance(result, dict)

    def test_extracts_known_keys(self):
        result = extract_colors(MINIMAL_THEME)
        assert "editor.background" in result
        assert "editor.foreground" in result

    def test_entry_has_required_fields(self):
        result = extract_colors(MINIMAL_THEME)
        entry = result["editor.background"]
        assert "hex" in entry
        assert "rgb" in entry
        assert "hsl" in entry
        assert "lab" in entry

    def test_rgb_is_tuple_of_ints(self):
        result = extract_colors(MINIMAL_THEME)
        rgb = result["editor.background"]["rgb"]
        assert len(rgb) == 3
        assert all(isinstance(v, int) for v in rgb)

    def test_background_rgb_correct(self):
        result = extract_colors(MINIMAL_THEME)
        assert result["editor.background"]["rgb"] == (18, 18, 18)

    def test_invalid_hex_skipped(self):
        theme = {"colors": {"bad.key": "not-a-color", "good.key": "#4d9375"}}
        result = extract_colors(theme)
        assert "bad.key" not in result
        assert "good.key" in result

    def test_empty_colors(self):
        result = extract_colors({"colors": {}})
        assert result == {}

    def test_missing_colors_key(self):
        result = extract_colors({})
        assert result == {}


class TestExtractSyntaxColors:
    def test_returns_dict(self):
        result = extract_syntax_colors(MINIMAL_THEME)
        assert isinstance(result, dict)

    def test_token_scope_string_parsed(self):
        result = extract_syntax_colors(MINIMAL_THEME)
        assert "string" in result

    def test_token_scope_list_parsed(self):
        result = extract_syntax_colors(MINIMAL_THEME)
        assert "keyword" in result
        assert "storage.type" in result

    def test_semantic_token_parsed(self):
        result = extract_syntax_colors(MINIMAL_THEME)
        assert "semantic:function" in result
        assert "semantic:type" in result

    def test_entry_has_required_fields(self):
        result = extract_syntax_colors(MINIMAL_THEME)
        entry = result["keyword"]
        assert "hex" in entry
        assert "rgb" in entry
        assert "hsl" in entry
        assert "lab" in entry

    def test_keyword_color_correct(self):
        result = extract_syntax_colors(MINIMAL_THEME)
        assert result["keyword"]["rgb"] == (77, 147, 117)

    def test_no_foreground_skipped(self):
        theme = {
            "tokenColors": [{"scope": "comment", "settings": {}}],
            "semanticTokenColors": {},
        }
        result = extract_syntax_colors(theme)
        assert "comment" not in result

    def test_semantic_non_string_value_skipped(self):
        theme = {
            "tokenColors": [],
            "semanticTokenColors": {
                "bold": {"bold": True},  # dict value, not a hex string
                "function": "#80a665",
            },
        }
        result = extract_syntax_colors(theme)
        assert "semantic:bold" not in result
        assert "semantic:function" in result

    def test_empty_theme(self):
        result = extract_syntax_colors({})
        assert result == {}
