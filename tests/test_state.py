"""Tests for application state management."""

import pytest
from gemmis.state import AppState


class TestAppState:
    """Tests for the AppState dataclass."""

    def test_initial_state(self):
        """AppState should initialize with correct defaults."""
        state = AppState()
        assert state.connected is False
        assert state.status == "READY"
        assert state.messages == []
        assert state.current_response == ""
        assert state.tokens == 0
        assert state.avatar_state == "idle"

    @pytest.mark.asyncio
    async def test_add_message(self):
        """add_message should append to messages list."""
        state = AppState(use_memory=False) # Disable memory for unit tests
        await state.add_message("user", "Hello")

        assert len(state.messages) == 1
        assert state.messages[0]["role"] == "user"
        assert state.messages[0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_add_multiple_messages(self):
        """Multiple messages should be added in order."""
        state = AppState(use_memory=False)
        await state.add_message("user", "Hello")
        await state.add_message("assistant", "Hi there!")
        await state.add_message("user", "How are you?")

        assert len(state.messages) == 3
        assert state.messages[0]["role"] == "user"
        assert state.messages[1]["role"] == "assistant"
        assert state.messages[2]["role"] == "user"

    @pytest.mark.asyncio
    async def test_get_chat_messages_includes_system(self):
        """get_chat_messages should include system prompt."""
        state = AppState(use_memory=False)
        await state.add_message("user", "Hello")

        messages = await state.get_chat_messages()

        # First message should be system prompt
        assert messages[0]["role"] == "system"
        # User message should follow
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    def test_history_tracking(self):
        """CPU and memory history lists should be initialized."""
        state = AppState()
        assert state.cpu_history == []
        assert state.mem_history == []

        # Should be appendable
        state.cpu_history.append(50.0)
        state.mem_history.append(60.0)

        assert len(state.cpu_history) == 1
        assert len(state.mem_history) == 1
