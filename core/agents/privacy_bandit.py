"""
Privacy Bandit — vendor privacy policy assessment agent.

Flow
----
Phase 1 — Discovery + fetch (tool-use loop)
  Claude receives a system prompt explaining its task and a user message
  with the vendor name and a starting URL. It calls fetch_url() until it
  has retrieved the full privacy policy (and optionally the DPA).

Phase 2 — Signal extraction (single LLM call)
  The accumulated policy text is passed to build_extraction_prompt() from
  the rubric engine. The LLM returns a flat JSON object with signal keys.
  This is a plain complete_json() call — no tools, deterministic output.

Phase 3 — Scoring (deterministic, no LLM)
  score_vendor() in rubric.py processes the signals and returns a fully
  scored AssessmentResult.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from core.agents.base_bandit import BaseBandit
from core.llm.base import BaseLLMProvider
from core.scoring.rubric import (
    RUBRIC,
    AssessmentResult,
    build_extraction_prompt,
    score_vendor,
)
from core.tools.fetch import fetch_url
from core.tools.parse import html_to_text


@dataclass
class FetchedSource:
    """Metadata for a single page retrieved during assessment."""
    url: str
    chars: int
    via: str  # "direct" or "jina"


@dataclass
class PrivacyAssessment:
    """Assessment result plus provenance — which pages were analysed."""
    result: AssessmentResult
    sources: list[FetchedSource] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────────────────────────────

_SYSTEM = """\
You are Privacy Bandit, an expert privacy compliance analyst.

Your task: retrieve the FULL TEXT of the vendor's privacy policy and,
if available, their Data Processing Agreement (DPA) or Data Processing
Addendum. These are the documents needed to score the vendor.

Instructions:
1. Start by fetching the starting URL provided.
2. If that page is a landing/overview page (short, mostly links), find and
   fetch the FULL privacy statement/policy linked from it — not the overview.
3. Also fetch the DPA / Data Processing Addendum / Data Processing Agreement
   if you find a link to one. This is critical for D8 scoring.
4. Prioritise pages with "full", "statement", "addendum", "DPA", or
   "processing" in the URL or page title.
5. Stop as soon as you have substantive policy text (1,500+ words of
   actual policy/legal content). Do not keep fetching once you have it.
6. You may fetch at most 5 pages total. The tool will block further fetches
   after 5, so choose carefully.

Common patterns:
  Privacy policy: /privacy, /privacy-policy, /privacy-statement,
                  /legal/privacy, /policies/privacy
  DPA:            /dpa, /data-processing-addendum, /legal/dpa,
                  /company/privacy/full_privacy, /gdpr

When done, end with:
<policy_retrieved>
List the URL(s) you fetched.
</policy_retrieved>

If you cannot find the policy after reasonable attempts, end with:
<policy_not_found>
Reason.
</policy_not_found>
"""

# ─────────────────────────────────────────────────────────────────────
# Tool schema
# ─────────────────────────────────────────────────────────────────────

_TOOL_FETCH_URL: dict = {
    "name": "fetch_url",
    "description": (
        "Fetch the content of a URL. Returns the page text. "
        "Use this to retrieve privacy policies, DPAs, and linked pages."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": (
                    "Full URL to fetch. Must start with http:// or https://."
                ),
            }
        },
        "required": ["url"],
    },
}


# ─────────────────────────────────────────────────────────────────────
# Domain inference
# ─────────────────────────────────────────────────────────────────────

def _start_url(vendor: str) -> str:
    """Return a starting URL to begin discovery from a vendor string."""
    vendor = vendor.strip()
    if re.match(r"^https?://", vendor):
        return vendor
    if "." in vendor and " " not in vendor:
        return f"https://{vendor}"
    # Name like "Acme Corp" → try www.acme.com
    slug = re.sub(r"[^a-z0-9]", "", vendor.lower().split()[0])
    return f"https://www.{slug}.com"


# ─────────────────────────────────────────────────────────────────────
# Privacy Bandit agent
# ─────────────────────────────────────────────────────────────────────

class PrivacyBandit(BaseBandit):
    """Assess a vendor's privacy practices against the 8-dimension rubric."""

    def __init__(
        self,
        provider: BaseLLMProvider,
        on_progress: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(provider)
        self._fetched_pages: dict[str, str] = {}   # url → clean text
        self._fetch_meta: list[FetchedSource] = []  # ordered fetch log
        self._on_progress = on_progress

    def _progress(self, msg: str) -> None:
        if self._on_progress:
            self._on_progress(msg)

    # ── Tool implementation ───────────────────────────────────────────

    # Minimum chars of parsed text before we consider a page usable.
    _MIN_PARSED_CHARS = 500  # below this → JS-rendered shell, retry via Jina
    _MAX_FETCHES = 5         # hard cap on pages fetched per assessment

    def _fetch(self, url: str) -> str:
        """Fetch, parse, cache, and return clean text for a URL."""
        # Hard cap — tell the agent to stop rather than raising
        if len(self._fetch_meta) >= self._MAX_FETCHES:
            return (
                f"[fetch limit reached — {self._MAX_FETCHES} pages already retrieved] "
                "You have enough content. Stop fetching and emit <policy_retrieved>."
            )

        if url in self._fetched_pages:
            # Return full cached text so the agent knows it already has it
            text = self._fetched_pages[url]
            return f"[already fetched — {len(text):,} chars, no need to fetch again]\n\n{text[:5_000]}…"

        raw, source = fetch_url(url)
        text = html_to_text(raw)

        # JS-rendered shell check
        if len(text) < self._MIN_PARSED_CHARS and source == "direct":
            try:
                from core.tools.fetch import _fetch_jina
                raw2 = _fetch_jina(url)
                text2 = html_to_text(raw2)
                if len(text2) > len(text):
                    text, source = text2, "jina"
            except Exception:
                pass

        self._fetched_pages[url] = text
        self._fetch_meta.append(FetchedSource(url=url, chars=len(text), via=source))

        remaining = self._MAX_FETCHES - len(self._fetch_meta)
        note = f"[{remaining} fetch(es) remaining]" if remaining > 0 else "[fetch limit reached — stop now]"
        return f"[fetched via {source} — {len(text):,} chars]  {note}\n\n{text[:40_000]}"

    # ── Signal reshaping ─────────────────────────────────────────────

    @staticmethod
    def _reshape_signals(raw_json: dict) -> dict[str, dict[str, bool]]:
        """Reshape flat signal dict into per-dimension dicts for score_vendor().

        The extraction prompt returns all signals in a flat dict keyed by
        signal slugs (e.g. "d1_purposes_stated"). score_vendor() expects
        {"D1": {"d1_purposes_stated": True, ...}, "D2": {...}, ...}.
        """
        signals: dict = raw_json.get("signals", {})
        art28: dict = raw_json.get("art28_checklist", {})
        frameworks: dict = raw_json.get("framework_certifications", {})

        per_dim: dict[str, dict[str, bool]] = {}
        for dim_key in RUBRIC:
            prefix = dim_key.lower() + "_"
            per_dim[dim_key] = {
                k: bool(v)
                for k, v in signals.items()
                if k.startswith(prefix)
            }

        # art28 checklist signals feed into D8
        per_dim.setdefault("D8", {}).update(
            {k: bool(v) for k, v in art28.items()}
        )

        return per_dim, [k for k, v in frameworks.items() if v]

    # ── Main assess method ───────────────────────────────────────────

    def assess(self, vendor: str) -> PrivacyAssessment:
        """Run a full privacy assessment for a vendor.

        Parameters
        ----------
        vendor:
            Vendor name (e.g. "Acme Corp"), domain (e.g. "acme.com"),
            or full URL (e.g. "https://acme.com/privacy-policy").

        Returns
        -------
        PrivacyAssessment
            Scored assessment with all 8 dimensions plus source provenance.

        Raises
        ------
        RuntimeError
            If no policy content could be retrieved.
        """
        self._fetched_pages = {}
        self._fetch_meta = []
        url = _start_url(vendor)

        # ── Phase 1: Discovery + fetch ────────────────────────────────
        self._progress(f"Phase 1/3  Discovering privacy policy for {vendor}…")
        messages = [
            {
                "role": "user",
                "content": (
                    f"Find and retrieve the complete privacy policy for "
                    f"**{vendor}**.\n\nStart here: {url}"
                ),
            }
        ]
        self.run_tool_loop(
            messages=messages,
            tools=[_TOOL_FETCH_URL],
            tool_registry={"fetch_url": self._fetch},
            system=_SYSTEM,
        )

        policy_text = "\n\n---\n\n".join(self._fetched_pages.values())
        if not policy_text.strip():
            raise RuntimeError(
                f"Could not retrieve any content for vendor: {vendor!r}"
            )

        # ── Phase 2: Signal extraction ────────────────────────────────
        self._progress(f"Phase 2/3  Extracting evidence signals from {len(self._fetch_meta)} page(s)…")
        extraction_prompt = build_extraction_prompt(vendor, policy_text)
        raw_json = self.provider.complete_json(
            prompt=extraction_prompt,
            max_tokens=2048,
        )

        # ── Phase 3: Deterministic scoring ───────────────────────────
        self._progress("Phase 3/3  Scoring against rubric…")
        per_dim, fw_list = self._reshape_signals(raw_json)
        result = score_vendor(
            vendor_name=vendor,
            evidence=per_dim,
            extracted_text=policy_text,
            framework_evidence=fw_list,
        )
        return PrivacyAssessment(result=result, sources=list(self._fetch_meta))
