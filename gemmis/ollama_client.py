"""
Ollama Client - Direct streaming chat with local LLM
"""

import asyncio
import json
import time
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from typing import Any

import httpx

# Try to import tiktoken for accurate token counting
try:
    import tiktoken

    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False

from .config import (
    CONNECT_TIMEOUT,
    CONTEXT_LENGTH,
    MAX_TOKENS,
    MODEL_NAME,
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_ENDPOINT,
    READ_TIMEOUT,
    TEMPERATURE,
    TOP_P,
)
from .tools import TOOLS, execute_tool_call


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken or fallback estimation"""
    if _TIKTOKEN_AVAILABLE:
        try:
            # Use cl100k_base encoding (GPT-4 style, works well for most models)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            pass

    # Fallback: rough estimation (1 token ≈ 4 characters for English/Swedish)
    return len(text) // 4


@dataclass
class StreamStats:
    """Statistics from streaming response"""

    tokens_generated: int = 0
    start_time: float = 0.0
    first_token_time: float | None = None
    end_time: float = 0.0
    full_text: str = ""

    @property
    def total_duration_ms(self) -> int:
        if self.end_time and self.start_time:
            return int((self.end_time - self.start_time) * 1000)
        return 0

    @property
    def tokens_per_second(self) -> float:
        duration_s = (self.end_time - self.start_time) if self.end_time else 0
        if duration_s > 0 and self.tokens_generated > 0:
            return self.tokens_generated / duration_s
        return 0.0

    @property
    def time_to_first_token_ms(self) -> int | None:
        if self.first_token_time and self.start_time:
            return int((self.first_token_time - self.start_time) * 1000)
        return None

    def update_token_count(self):
        """Update token count based on full text"""
        if self.full_text:
            self.tokens_generated = count_tokens(self.full_text)


class OllamaError(Exception):
    """Base exception for Ollama errors"""

    pass


class OllamaClient:
    """Async client for Ollama API with streaming support"""

    def __init__(self, model: str = MODEL_NAME):
        self.model = model
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=30.0, pool=5.0
                )
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def is_connected(self) -> bool:
        """Check if Ollama server is reachable"""
        try:
            client = await self._get_client()
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=CONNECT_TIMEOUT)
            return response.status_code == 200
        except Exception:
            return False

    async def get_model_info(self) -> dict | None:
        """Get info about current model"""
        try:
            client = await self._get_client()
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                for model in data.get("models", []):
                    if self.model in model.get("name", ""):
                        return model
        except Exception:
            pass
        return None

    async def embed(self, prompt: str) -> list[float] | None:
        """Generate embeddings for text using the current model."""
        try:
            client = await self._get_client()
            payload = {
                "model": self.model,
                "prompt": prompt
            }
            response = await client.post(f"{OLLAMA_BASE_URL}/api/embeddings", json=payload)
            if response.status_code == 200:
                return response.json().get("embedding")
        except Exception:
            pass
        return None

    async def chat_stream(
        self,
        messages: list[dict],
        tools_enabled: bool = True,
        tool_executor: Callable[[str, dict], dict | Any] | None = None,
    ) -> AsyncGenerator[tuple[str, StreamStats | None, dict | None], None]:
        """
        Stream chat completion tokens with function calling support.

        Args:
            messages: List of message dictionaries
            tools_enabled: Whether to enable tools
            tool_executor: Optional async/sync callback to execute tools.
                           Signature: (tool_name, arguments) -> result_dict
                           If None, uses default execute_tool_call.

        Yields:
            (token_content, None, None) during streaming
            ("", StreamStats, None) at the end
            ("", None, tool_call_info) when tool is called
        """
        stats = StreamStats(start_time=time.time())

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": TEMPERATURE,
                "top_p": TOP_P,
                "num_predict": MAX_TOKENS,
                "num_ctx": CONTEXT_LENGTH,
            },
        }

        # Add tools if enabled (only if model supports it)
        if tools_enabled:
            try:
                payload["tools"] = TOOLS
            except Exception:
                # If tools fail, continue without them
                pass

        try:
            client = await self._get_client()

            async with client.stream(
                "POST",
                OLLAMA_CHAT_ENDPOINT,
                json=payload,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise OllamaError(f"Ollama error {response.status_code}: {error_text}")

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    message = data.get("message", {})
                    content = message.get("content", "")

                    # Check for tool calls in message (Ollama format)
                    # Ollama may send tool_calls in different formats
                    tool_calls = None
                    if message:
                        tool_calls = message.get("tool_calls")
                    if not tool_calls:
                        # Also check in data directly
                        tool_calls = data.get("tool_calls")
                    if not tool_calls:
                        # Check if message has tool_use (alternative format)
                        tool_calls = message.get("tool_use") if message else None

                    if tool_calls:
                        # Handle tool calls - Ollama sends tool_calls when model wants to use a tool
                        tool_list = tool_calls if isinstance(tool_calls, list) else [tool_calls]
                        for tool_call in tool_list:
                            func = tool_call.get("function", {})
                            if not func:
                                continue

                            tool_name = func.get("name", "")
                            tool_args_json = func.get("arguments", "{}")

                            try:
                                tool_args = (
                                    json.loads(tool_args_json)
                                    if isinstance(tool_args_json, str)
                                    else tool_args_json
                                )
                            except (json.JSONDecodeError, TypeError):
                                tool_args = {}

                            if tool_name:
                                # Execute tool with custom executor if provided
                                if tool_executor:
                                    if asyncio.iscoroutinefunction(tool_executor):
                                        tool_result = await tool_executor(tool_name, tool_args)
                                    else:
                                        tool_result = tool_executor(tool_name, tool_args)
                                else:
                                    tool_result = execute_tool_call(tool_name, tool_args)

                                # Yield tool call info
                                yield (
                                    "",
                                    None,
                                    {
                                        "type": "tool_call",
                                        "tool_name": tool_name,
                                        "arguments": tool_args,
                                        "result": tool_result,
                                    },
                                )

                    if content:
                        if stats.first_token_time is None:
                            stats.first_token_time = time.time()
                        stats.full_text += content
                        yield content, None, None

                    if data.get("done", False):
                        stats.end_time = time.time()
                        break

        except httpx.ConnectError as e:
            raise OllamaError("Cannot connect to Ollama. Is it running?") from e
        except httpx.ReadTimeout as e:
            stats.end_time = time.time()
            raise OllamaError(f"Request timed out after {READ_TIMEOUT}s") from e

        if stats.end_time == 0:
            stats.end_time = time.time()

        # Update accurate token count
        stats.update_token_count()
        yield "", stats, None
