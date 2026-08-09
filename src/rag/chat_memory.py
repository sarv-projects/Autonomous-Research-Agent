"""
Chat Memory — sliding window conversation history with summary compression.

Manages conversation context for chat mode:
- Keeps the last N messages in full (sliding window)
- Compresses older messages into a running summary
- Integrates with the LLM gateway for summary generation

Uses a simple JSON file for persistence across sessions.
"""

from __future__ import annotations

import json
import os
import time
from typing import Optional


class ChatMemory:
    """Conversation history manager for chat mode.

    Architecture:
        - Recent window: last `window_size` messages kept verbatim
        - Summary: older messages compressed into a running summary string
        - Persisted to disk as JSON for session continuity
    """

    def __init__(
        self,
        window_size: int = 10,
        max_summary_length: int = 500,
        persist_path: str = "",
    ) -> None:
        self.window_size = window_size
        self.max_summary_length = max_summary_length
        self.messages: list[dict] = []  # [{role, content, timestamp}]
        self.summary: str = ""

        if not persist_path:
            persist_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "data", "chat_memory.json",
            )
        self.persist_path = os.path.abspath(persist_path)
        self._load()

    def add(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })
        self._maybe_compress()
        self._save()

    def _maybe_compress(self) -> None:
        """If window is full, compress oldest messages into summary."""
        if len(self.messages) <= self.window_size:
            return

        # Messages to compress: oldest messages beyond the window
        to_compress = self.messages[: -self.window_size]
        self.messages = self.messages[-self.window_size :]

        # Build new summary from old messages
        old_text = "\n".join(
            f"[{m['role']}]: {m['content'][:200]}" for m in to_compress
        )

        # Generate summary using lightweight approach (no LLM call needed)
        new_summary = self._generate_summary(old_text)
        if self.summary:
            self.summary = f"{self.summary}\n{new_summary}"
        else:
            self.summary = new_summary

        # Truncate summary if too long
        if len(self.summary) > self.max_summary_length:
            self.summary = self.summary[-self.max_summary_length:]

    def _generate_summary(self, text: str) -> str:
        """Generate a brief summary of conversation segment (no LLM needed).

        Uses a simple extractive approach: picks key sentences.
        """
        sentences = [s.strip() for s in text.replace("\n", ". ").split(".") if s.strip()]
        # Pick sentences with key indicators
        key_indicators = ["?", "important", "key", "main", "note", "result"]
        key_sentences = [
            s for s in sentences
            if any(ind in s.lower() for ind in key_indicators)
        ]
        if not key_sentences:
            key_sentences = sentences[:2]  # fallback: first two sentences

        condensed = " | ".join(s[:80] for s in key_sentences[:3])
        return f"[summary: {condensed}]"

    def build_context(self, system_prompt: str = "") -> list[dict]:
        """Build the full context for the next LLM call.

        Returns a list of message dicts in OpenAI-compatible format.
        """
        messages: list[dict] = []

        if system_prompt:
            # Inject summary into system prompt if available
            if self.summary:
                system_prompt = (
                    f"{system_prompt}\n\n"
                    f"[Previous conversation summary: {self.summary}]"
                )
            messages.append({"role": "system", "content": system_prompt})

        # Add recent window
        for m in self.messages:
            messages.append({"role": m["role"], "content": m["content"]})

        return messages

    def clear(self) -> None:
        """Clear all memory."""
        self.messages = []
        self.summary = ""
        self._save()

    def _save(self) -> None:
        """Persist to disk."""
        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
        with open(self.persist_path, "w") as f:
            json.dump({
                "messages": self.messages[-50:],  # keep last 50
                "summary": self.summary,
            }, f, indent=2)

    def _load(self) -> None:
        """Load from disk if exists."""
        if not os.path.exists(self.persist_path):
            return
        try:
            with open(self.persist_path, "r") as f:
                data = json.load(f)
                self.messages = data.get("messages", [])[-self.window_size:]
                self.summary = data.get("summary", "")
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    def __len__(self) -> int:
        return len(self.messages)


# Module-level singleton for chat mode
_chat_memory: Optional[ChatMemory] = None


def get_chat_memory() -> ChatMemory:
    """Get or create the chat memory singleton."""
    global _chat_memory
    if _chat_memory is None:
        _chat_memory = ChatMemory()
    return _chat_memory


def reset_chat_memory() -> None:
    """Reset the chat memory singleton."""
    global _chat_memory
    if _chat_memory:
        _chat_memory.clear()
    _chat_memory = None
