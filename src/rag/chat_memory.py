"""
Chat Memory — sliding window conversation history with summary compression.

Manages conversation context for chat mode:
- Keeps the last N messages in full (sliding window)
- Compresses older messages into a running summary
- Supports session-isolated conversation memories
"""

from __future__ import annotations

import json
import os
import time
from typing import Optional, Dict


class ChatMemory:
    """Conversation history manager for chat mode.

    Architecture:
        - Recent window: last `window_size` messages kept verbatim
        - Summary: older messages compressed into a running summary string
        - Persisted to disk as JSON for session continuity
    """

    def __init__(
        self,
        session_id: str = "default",
        window_size: int = 10,
        max_summary_length: int = 500,
        persist_path: str = "",
    ) -> None:
        self.session_id = session_id
        self.window_size = window_size
        self.max_summary_length = max_summary_length
        self.messages: list[dict] = []  # [{role, content, timestamp}]
        self.summary: str = ""

        if not persist_path:
            safe_session = "".join(c if c.isalnum() else "_" for c in session_id)
            persist_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "data", f"chat_memory_{safe_session}.json",
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

        to_compress = self.messages[: -self.window_size]
        self.messages = self.messages[-self.window_size :]

        old_text = "\n".join(
            f"[{m['role']}]: {m['content'][:200]}" for m in to_compress
        )

        new_summary = self._generate_summary(old_text)
        if self.summary:
            self.summary = f"{self.summary}\n{new_summary}"
        else:
            self.summary = new_summary

        if len(self.summary) > self.max_summary_length:
            self.summary = self.summary[-self.max_summary_length:]

    def _generate_summary(self, text: str) -> str:
        """Generate a brief summary of conversation segment.

        Prefers a cheap LLM summary when available; falls back to heuristics.
        """
        # Try LLM summary (fast tier) — best-effort, never blocks chat hard
        try:
            from src.llm import call_llm
            summary = call_llm(
                "Summarize the conversation excerpt in 1-2 short sentences. "
                "Keep key facts and open questions. No preamble.",
                text[:2000],
                model="fast",
            )
            if summary and len(summary.strip()) > 10:
                return f"[summary: {summary.strip()[: self.max_summary_length]}]"
        except Exception:
            pass

        sentences = [s.strip() for s in text.replace("\n", ". ").split(".") if s.strip()]
        key_indicators = ["?", "important", "key", "main", "note", "result"]
        key_sentences = [
            s for s in sentences
            if any(ind in s.lower() for ind in key_indicators)
        ]
        if not key_sentences:
            key_sentences = sentences[:2]

        condensed = " | ".join(s[:80] for s in key_sentences[:3])
        return f"[summary: {condensed}]"

    def build_context(self, system_prompt: str = "") -> list[dict]:
        """Build the full context for the next LLM call."""
        messages: list[dict] = []

        if system_prompt:
            if self.summary:
                system_prompt = (
                    f"{system_prompt}\n\n"
                    f"[Previous conversation summary: {self.summary}]"
                )
            messages.append({"role": "system", "content": system_prompt})

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
                "messages": self.messages[-50:],
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


# Module-level registry for chat memories by session_id
_chat_memories: Dict[str, ChatMemory] = {}


def get_chat_memory(session_id: str = "default") -> ChatMemory:
    """Get or create the session chat memory."""
    global _chat_memories
    if session_id not in _chat_memories:
        _chat_memories[session_id] = ChatMemory(session_id=session_id)
    return _chat_memories[session_id]


def reset_chat_memory(session_id: str = "default") -> None:
    """Reset a chat memory session."""
    global _chat_memories
    if session_id in _chat_memories:
        _chat_memories[session_id].clear()
        del _chat_memories[session_id]
