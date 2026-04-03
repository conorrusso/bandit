"""
Legal Bandit — HTML Report Generator
======================================
Generates the standalone legal redline brief.
Self-contained HTML, no external dependencies.
Bandit brand — cream background, monospaced font.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime

from core.agents.legal_bandit_models import (
    LegalBanditResult, ProvisionStatus, ChangeType,
    ConflictSeverity,
)

APP_VERSION = "1.2.0"


def generate_legal_brief(
    result: LegalBanditResult,
    output_path: str | None = None,
) -> str:
    """
    Generate standalone HTML legal brief.
    Returns the HTML string.
    If output_path provided, also saves to file.
    """

    # ── CSS ──────────────────────────────────────
    css = """
:root{--cr:#F4EFE4;--br:#8B5A2B;--ink:#1A1510;
  --mu:#6B5B4E;--bd:#D4C9B8;--red:#8B1A1A;
  --grn:#1A5C2A;--amb:#7A5500;--blue:#1A2A5A}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'SF Mono','Fira Code',
  'Courier New',monospace;font-size:13px;
  line-height:1.65;max-width:1040px;margin:0 auto;
  padding:40px 24px 80px;color:var(--ink);
  background:var(--cr)}
h1{font-size:20px;font-weight:700;margin-bottom:6px}
h2{font-size:10px;font-weight:700;
  letter-spacing:.16em;text-transform:uppercase;
  color:var(--br);border-bottom:1px solid var(--bd);
  padding-bottom:6px;margin:32px 0 12px}
h3{font-size:12px;font-weight:700;
  margin-bottom:8px;color:var(--ink)}
.hdr{border-bottom:2px solid var(--br);
  padding-bottom:20px;margin-bottom:16px}
.brand{color:var(--br);font-size:10px;
  letter-spacing:.18em;text-transform:uppercase;
  margin-bottom:6px}
.meta{font-size:12px;color:var(--mu);line-height:2}
.summary-grid{display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:12px;margin-bottom:24px}
.sum-card{background:#fff;border:1px solid var(--bd);
  border-radius:4px;padding:12px;text-align:center}
.sum-num{font-size:28px;font-weight:700;
  margin-bottom:4px}
.sum-lbl{font-size:10px;color:var(--mu);
  letter-spacing:.1em;text-transform:uppercase}
.req{color:var(--red)}.rec{color:var(--amb)}
.ok{color:var(--grn)}.conf{color:#7A2A7A}
.provision{border:1px solid var(--bd);
  border-radius:4px;margin-bottom:12px;
  overflow:hidden}
.prov-hdr{padding:10px 14px;display:flex;
  align-items:center;gap:12px;
  background:rgba(139,90,43,.04)}
.prov-num{font-size:11px;font-weight:700;
  color:var(--mu);min-width:24px}
.prov-name{font-weight:700;flex:1}
.prov-ref{font-size:11px;color:var(--mu)}
.status-badge{font-size:9px;font-weight:700;
  padding:2px 8px;border-radius:2px;
  letter-spacing:.08em}
.s-required{background:#FDECEA;color:var(--red);
  border:1px solid #F5C6C6}
.s-recommended{background:#FEF9E7;color:var(--amb);
  border:1px solid #F5E6A3}
.s-acceptable{background:#EAF5EA;color:var(--grn);
  border:1px solid #A8D5A8}
.prov-body{padding:12px 16px}
.quote-box{background:#F8F5F0;border:1px solid var(--bd);
  border-left:3px solid var(--br);border-radius:0 4px 4px 0;
  padding:10px 12px;font-style:italic;
  font-size:12px;color:var(--ink);
  line-height:1.7;margin:8px 0}
.quote-ref{font-size:10px;color:var(--mu);
  font-style:normal;margin-top:4px}
.redline-box{background:#E8F0FE;
  border:1px solid #B0C8F8;border-radius:4px;
  padding:10px 14px;color:var(--blue);
  font-style:italic;line-height:1.7;
  font-size:12px;margin:8px 0}
.problem{background:#FDECEA;border-left:3px solid var(--red);
  padding:8px 12px;border-radius:0 4px 4px 0;
  font-size:12px;color:var(--red);margin:8px 0}
.gap-list{list-style:none;padding:0;margin:6px 0}
.gap-list li{padding:2px 0 2px 14px;
  font-size:12px;color:var(--amb)}
.gap-list li::before{content:"✗  ";color:var(--red)}
.prec{font-size:11px;color:var(--mu);
  font-style:italic;margin-top:6px}
.conflict{border:1px solid #D4A0D4;
  border-radius:4px;margin-bottom:12px;
  overflow:hidden}
.conflict-hdr{background:#F8EAF8;padding:10px 14px;
  font-weight:700;font-size:12px;color:#7A2A7A}
.conflict-body{padding:12px 16px}
.disclaimer{background:rgba(139,90,43,.06);
  border:1px solid var(--bd);border-radius:4px;
  padding:16px;margin-top:32px;font-size:11px;
  color:var(--mu);line-height:1.8}
.section-lbl{font-size:10px;color:var(--mu);
  font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;margin-bottom:4px}
@media(max-width:640px){
  .summary-grid{grid-template-columns:1fr 1fr}}
"""

    # ── Header ───────────────────────────────────
    docs_reviewed = []
    if result.dpa_source:
        docs_reviewed.append(f"DPA — {result.dpa_source}")
    if result.msa_source:
        docs_reviewed.append(f"MSA — {result.msa_source}")
    if result.scc_source:
        docs_reviewed.append(f"SCCs — {result.scc_source}")

    docs_html = "<br>".join(docs_reviewed)

    header = f"""
<div class="hdr">
  <div class="brand">🦝 BANDIT · LEGAL BRIEF</div>
  <h1>{_h(result.vendor_name)}</h1>
  <div class="meta">
    Assessment date: {result.assessment_date}<br>
    Documents reviewed:<br>
    {docs_html}<br>
    Generated by Bandit Legal Bandit v{APP_VERSION}
  </div>
</div>"""

    # ── Executive summary ─────────────────────────
    summary = f"""
<h2>Executive Summary</h2>
<div class="summary-grid">
  <div class="sum-card">
    <div class="sum-num req">{result.required_changes}</div>
    <div class="sum-lbl">Required<br>before signing</div>
  </div>
  <div class="sum-card">
    <div class="sum-num rec">{result.recommended_changes}</div>
    <div class="sum-lbl">Recommended<br>improvements</div>
  </div>
  <div class="sum-card">
    <div class="sum-num ok">{result.acceptable_provisions}</div>
    <div class="sum-lbl">Acceptable<br>provisions</div>
  </div>
  <div class="sum-card">
    <div class="sum-num conf">{result.conflicts_count}</div>
    <div class="sum-lbl">Policy/contract<br>conflicts</div>
  </div>
</div>"""

    # ── Provision renderer ────────────────────────
    def render_provision(p, num):
        if p.status == ProvisionStatus.PRESENT_SPECIFIC:
            badge = (
                '<span class="status-badge s-acceptable">'
                'ACCEPTABLE</span>'
            )
        elif p.status == ProvisionStatus.PRESENT_VAGUE:
            if p.change_type == ChangeType.REQUIRED:
                badge = (
                    '<span class="status-badge s-required">'
                    'REQUIRED — TOO VAGUE</span>'
                )
            else:
                badge = (
                    '<span class="status-badge s-recommended">'
                    'RECOMMENDED</span>'
                )
        else:
            if p.change_type == ChangeType.REQUIRED:
                badge = (
                    '<span class="status-badge s-required">'
                    'REQUIRED — ABSENT</span>'
                )
            else:
                badge = (
                    '<span class="status-badge s-recommended">'
                    'RECOMMENDED</span>'
                )

        quote_html = ""
        if p.verbatim_quote:
            ref = (
                f'<div class="quote-ref">{_h(p.section_reference)}</div>'
                if p.section_reference else ""
            )
            quote_html = f"""
<div class="section-lbl">Current language</div>
<div class="quote-box">
  &ldquo;{_h(p.verbatim_quote)}&rdquo;
  {ref}
</div>"""
        elif p.status != ProvisionStatus.PRESENT_SPECIFIC:
            quote_html = """
<div class="section-lbl">Current language</div>
<div class="problem">No clause found in document.</div>"""

        problem_html = ""
        if p.vague_phrases:
            phrases = ", ".join(
                f'&ldquo;{_h(ph)}&rdquo;' for ph in p.vague_phrases
            )
            problem_html = f"""
<div class="problem">
  Vague or unenforceable language: {phrases}
</div>"""

        gaps_html = ""
        if p.gaps:
            items = "".join(f"<li>{_h(g)}</li>" for g in p.gaps)
            gaps_html = f'<ul class="gap-list">{items}</ul>'

        redline_html = ""
        if (p.redline_recommendation
                and p.change_type != ChangeType.ACCEPTABLE):
            redline_html = f"""
<div class="section-lbl">Recommended language</div>
<div class="redline-box">{_h(p.redline_recommendation)}</div>"""

        prec_html = ""
        if (p.enforcement_precedent
                and p.change_type == ChangeType.REQUIRED):
            prec_html = (
                f'<div class="prec">Enforcement precedent: '
                f'{_h(p.enforcement_precedent)}</div>'
            )

        return f"""
<div class="provision">
  <div class="prov-hdr">
    <span class="prov-num">{_h(str(num))}</span>
    <span class="prov-name">{_h(p.provision_name)}</span>
    <span class="prov-ref">{_h(p.regulatory_ref)}</span>
    {badge}
  </div>
  <div class="prov-body">
    {quote_html}
    {problem_html}
    {gaps_html}
    {redline_html}
    {prec_html}
  </div>
</div>"""

    # ── Required section ──────────────────────────
    required = [p for p in result.provisions if p.change_type == ChangeType.REQUIRED]
    req_html = ""
    if required:
        items = "".join(
            render_provision(p, f"1.{i+1}")
            for i, p in enumerate(required)
        )
        req_html = (
            "<h2>Section 1 — Required Before Signing</h2>" + items
        )

    # ── Recommended section ───────────────────────
    recommended = [p for p in result.provisions if p.change_type == ChangeType.RECOMMENDED]
    rec_html = ""
    if recommended:
        items = "".join(
            render_provision(p, f"2.{i+1}")
            for i, p in enumerate(recommended)
        )
        rec_html = (
            "<h2>Section 2 — Recommended Improvements</h2>" + items
        )

    # ── Acceptable section ────────────────────────
    acceptable = [p for p in result.provisions if p.change_type == ChangeType.ACCEPTABLE]
    acc_html = ""
    if acceptable:
        items = "".join(
            f'<div style="padding:6px 0;border-bottom:'
            f'1px solid var(--bd);font-size:12px;">'
            f'<span style="color:var(--grn)">✓</span>'
            f'&nbsp; {_h(p.provision_name)}'
            f'<span style="color:var(--mu);font-size:11px">'
            f' — {_h(p.regulatory_ref)} — acceptable</span>'
            f'</div>'
            for p in acceptable
        )
        acc_html = (
            "<h2>Section 3 — Acceptable Provisions</h2>" + items
        )

    # ── Conflicts section ─────────────────────────
    conf_html = ""
    if result.conflicts:
        items = ""
        for i, c in enumerate(result.conflicts):
            sev_colour = (
                "var(--red)"
                if c.severity == ConflictSeverity.HIGH
                else "var(--amb)"
            )
            items += f"""
<div class="conflict">
  <div class="conflict-hdr">
    {i+1}. {_h(c.dimension)} — Policy commitment not backed by DPA
  </div>
  <div class="conflict-body">
    <div class="section-lbl">Policy states</div>
    <div class="quote-box">{_h(c.policy_claim)}</div>
    <div class="section-lbl">DPA reality</div>
    <div class="problem">{_h(c.contract_reality)}</div>
    <div style="font-size:12px;margin-top:8px;color:{sev_colour}">
      Risk: This policy commitment is not contractually
      enforceable. The DPA is the binding document.
    </div>
    <div style="font-size:12px;margin-top:6px">
      Action: {_h(c.recommendation)}
    </div>
  </div>
</div>"""

        conf_html = (
            "<h2>Section 4 — Policy Commitments Without DPA Backing</h2>"
            + items
        )

    # ── MSA section ───────────────────────────────
    msa_html = ""
    if result.msa:
        msa = result.msa
        rows = []
        if msa.governing_law:
            rows.append(
                f"<tr><td>Governing law</td>"
                f"<td>{_h(msa.governing_law)}</td></tr>"
            )
        if msa.liability_cap_value:
            cap_risk = (
                ' <span style="color:var(--red)">'
                '⚠ Excludes data breach claims</span>'
                if msa.liability_cap_excludes_breaches else ""
            )
            rows.append(
                f"<tr><td>Liability cap</td>"
                f"<td>{_h(msa.liability_cap_value)}{cap_risk}</td></tr>"
            )
        if msa.data_return_on_termination_days:
            rows.append(
                f"<tr><td>Data return on termination</td>"
                f"<td>{msa.data_return_on_termination_days} days</td></tr>"
            )
        if msa.dispute_resolution:
            rows.append(
                f"<tr><td>Dispute resolution</td>"
                f"<td>{_h(msa.dispute_resolution)}</td></tr>"
            )

        concerns_html = ""
        if msa.concerns:
            items_c = "".join(
                f"<li>{_h(c)}</li>" for c in msa.concerns
            )
            concerns_html = (
                f'<div class="problem" style="margin-top:12px">'
                f'<strong>Concerns:</strong><ul '
                f'style="margin:6px 0 0 16px">{items_c}'
                f'</ul></div>'
            )

        table = (
            f'<table style="margin-bottom:12px">{"".join(rows)}</table>'
            if rows else ""
        )

        msa_html = (
            "<h2>MSA — Commercial Data Protection Terms</h2>"
            + table
            + concerns_html
        )

    # ── SCC section ───────────────────────────────
    scc_html = ""
    if result.sccs:
        scc = result.sccs
        outdated_warning = ""
        if scc.outdated:
            outdated_warning = """
<div class="problem">
  ⚠ OUTDATED SCCs DETECTED — Pre-2021 Standard
  Contractual Clauses are invalid following the
  European Commission's decision. New 2021/914 SCCs
  must be executed immediately.
  Precedent: Any transfer relying on outdated SCCs
  is unlawful under GDPR Chapter V.
</div>"""

        scc_html = f"""
<h2>Standard Contractual Clauses</h2>
{outdated_warning}
<div style="font-size:12px">
  Version: {_h(scc.scc_version or 'Unknown')}<br>
  Module: {_h(scc.module or 'Not specified')}<br>
  Annex I(a) — Parties: {'✓' if scc.annex_1a_completed else '✗'}<br>
  Annex I(b) — Transfer description: {'✓' if scc.annex_1b_completed else '✗'}<br>
  Annex II — Technical measures: {'✓' if scc.annex_2_completed else '✗'}<br>
  TIA referenced: {'✓' if scc.tia_referenced else '✗'}
</div>"""

    # ── Disclaimer ────────────────────────────────
    disclaimer = f"""
<div class="disclaimer">
  <strong>Disclaimer</strong><br>
  This brief was generated by Bandit Legal Bandit
  v{APP_VERSION} on {result.assessment_date}.
  It identifies contractual gaps against GDPR
  Art. 28(3) and related requirements based on
  automated document analysis.<br><br>
  This brief does not constitute legal advice and
  should not be relied upon as such. The assessment
  may not identify all contractual risks. Have
  qualified legal counsel review the DPA and MSA
  before relying on this brief in negotiations
  or making contract decisions.
</div>"""

    # ── Assemble ──────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Legal Brief — {_h(result.vendor_name)}</title>
<style>{css}</style>
</head>
<body>
{header}
{summary}
{req_html}
{rec_html}
{conf_html}
{acc_html}
{msa_html}
{scc_html}
{disclaimer}
</body>
</html>"""

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")

    return html


def _h(text: str) -> str:
    """HTML-escape a string."""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
