"""Tests for the persona system."""

import pytest
from gemmis.personas import (
    PERSONAS,
    get_persona_prompt,
    list_personas,
    get_persona_description,
)


class TestPersonaRegistry:
    """Tests for persona management functions."""

    def test_all_personas_registered(self):
        """All expected personas should be in PERSONAS dict."""
        expected = {"default", "architect", "hacker", "assistant"}
        assert set(PERSONAS.keys()) == expected

    def test_list_personas(self):
        """list_personas should return all persona names."""
        personas = list_personas()
        assert "default" in personas
        assert "architect" in personas
        assert "hacker" in personas
        assert "assistant" in personas

    def test_get_persona_prompt_valid(self):
        """get_persona_prompt should return prompt for valid persona."""
        prompt = get_persona_prompt("architect")
        assert "Senior Software Architect" in prompt

    def test_get_persona_prompt_invalid(self):
        """get_persona_prompt should raise ValueError for invalid persona."""
        with pytest.raises(ValueError):
            get_persona_prompt("nonexistent")

    def test_get_persona_description(self):
        """get_persona_description should return short description."""
        desc = get_persona_description("hacker")
        assert desc is not None
        assert "terse" in desc.lower() or "efficient" in desc.lower()


class TestPersonaContent:
    """Tests for persona prompt content."""

    def test_default_persona_has_tools_info(self):
        """Default persona should mention available tools."""
        prompt = get_persona_prompt("default")
        assert "tool" in prompt.lower() or "TOOL" in prompt

    def test_architect_focused_on_design(self):
        """Architect persona should focus on design patterns."""
        prompt = get_persona_prompt("architect")
        assert "design" in prompt.lower() or "architecture" in prompt.lower()

    def test_hacker_is_terse(self):
        """Hacker persona should emphasize terseness."""
        prompt = get_persona_prompt("hacker")
        assert "terse" in prompt.lower() or "minimal" in prompt.lower()

    def test_assistant_is_friendly(self):
        """Assistant persona should be friendly and pedagogical."""
        prompt = get_persona_prompt("assistant")
        assert "friendly" in prompt.lower() or "patient" in prompt.lower()
