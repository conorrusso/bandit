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
5. Stop when you have substantive policy text (2,000+ words of actual
   policy/legal content, not navigation).
6. Do not fetch more than 8 pages total.

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

    def __init__(self, provider: BaseLLMProvider) -> None:
        super().__init__(provider)
        self._fetched_pages: dict[str, str] = {}  # url → clean text

    # ── Tool implementation ───────────────────────────────────────────

    # Minimum chars of parsed text before we consider a page usable.
    # Pages below this threshold are JS-rendered shells — retry via Jina.
    _MIN_PARSED_CHARS = 500

    def _fetch(self, url: str) -> str:
        """Fetch, parse, cache, and return clean text for a URL.

        If the parsed text is below _MIN_PARSED_CHARS (JS-rendered shell),
        retries via Jina Reader which renders JavaScript before returning.
        """
        if url in self._fetched_pages:
            preview = self._fetched_pages[url][:300]
            return f"[already fetched — preview]\n{preview}…"

        raw, source = fetch_url(url)
        text = html_to_text(raw)

        # JS-rendered shell check: if direct fetch gave almost nothing, try Jina
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
        return f"[fetched via {source} — {len(text):,} chars]\n\n{text[:40_000]}"

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

    def assess(self, vendor: str) -> AssessmentResult:
        """Run a full privacy assessment for a vendor.

        Parameters
        ----------
        vendor:
            Vendor name (e.g. "Acme Corp"), domain (e.g. "acme.com"),
            or full URL (e.g. "https://acme.com/privacy-policy").

        Returns
        -------
        AssessmentResult
            Fully scored assessment with all 8 dimensions.

        Raises
        ------
        RuntimeError
            If no policy content could be retrieved.
        """
        self._fetched_pages = {}
        url = _start_url(vendor)

        # ── Phase 1: Discovery + fetch ────────────────────────────────
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
        extraction_prompt = build_extraction_prompt(vendor, policy_text)
        raw_json = self.provider.complete_json(
            prompt=extraction_prompt,
            max_tokens=2048,
        )

        # ── Phase 3: Deterministic scoring ───────────────────────────
        per_dim, fw_list = self._reshape_signals(raw_json)
        return score_vendor(
            vendor_name=vendor,
            evidence=per_dim,
            extracted_text=policy_text,
            framework_evidence=fw_list,
        )
