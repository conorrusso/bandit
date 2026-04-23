"""
Shared infrastructure for specialist Bandit agents.

Each agent subclasses BaseAgent and implements analyse().
Documents arrive with text already extracted — no PDF re-reading.
"""
from __future__ import annotations

import json
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, Callable

logger = logging.getLogger("bandit")


@dataclass
class AgentDocument:
    """
    A document passed to a specialist agent.
    Text is already extracted — no PDF re-reading.
    """
    filename: str
    doc_type: str        # DocumentType enum value as str
    text: str            # Already extracted text
    confidence: float    # Classification confidence


@dataclass
class AgentResult:
    """
    Result from any specialist agent.
    Contains signals, findings, and narrative.
    """
    agent_name: str
    vendor_name: str
    success: bool

    # Signals to merge into main signal dict
    signals: dict = field(default_factory=dict)

    # Framework evidence to pass to score_vendor()
    framework_evidence: dict = field(default_factory=dict)

    # Human-readable findings for report
    findings: list[str] = field(default_factory=list)

    # Raw structured result from LLM
    raw_result: dict = field(default_factory=dict)

    # Error message if success=False
    error: Optional[str] = None

    # Which documents were analysed
    documents_analysed: list[str] = field(
        default_factory=list
    )


class BaseAgent:
    """
    Base class for specialist agents.
    Subclass and implement analyse().
    """

    name = "base"

    def __init__(
        self,
        provider,
        on_progress: Optional[Callable] = None,
        max_tokens: int = 4000,
    ):
        self.provider = provider
        self.on_progress = on_progress
        self.max_tokens = max_tokens

    def _progress(self, msg: str) -> None:
        if self.on_progress:
            self.on_progress(msg)

    def _call_llm_json(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        """Call the configured provider and parse JSON response."""
        return self.provider.complete_json(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens or self.max_tokens,
        )

    def _truncate_text(
        self,
        text: str,
        max_chars: int = 40000,
    ) -> str:
        """
        Truncate document text to fit in prompt.
        40k chars ~ 10k tokens — well within context window.
        """
        if len(text) <= max_chars:
            return text
        logger.debug(
            f"Truncating document from "
            f"{len(text)} to {max_chars} chars"
        )
        return text[:max_chars] + "\n[... truncated]"

    def analyse(
        self,
        vendor_name: str,
        documents: list[AgentDocument],
        intake_context: str | None = None,
    ) -> AgentResult:
        """
        Override in subclass.
        Returns AgentResult.
        """
        raise NotImplementedError
