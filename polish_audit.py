"""polish_audit.py — Tier-4 vague-discourse audit for the QN2025106 MG
manuscript, adapted from the 校级课题 review-manuscript vague_discourse_audit.

Input source: build_mg_manuscript.js (the source of truth for citations and
prose). Extracts string content from body()/bodyIndent() calls and runs the
four-tier audit. Reports file:line for each hit so the author can decide
case-by-case which to fix.

Tiers
-----
4A  High-precision targets — almost always cut/replace:
      now, currently, nowadays, at present, these days,
      recently, recent, thing(s), stuff, get/got/...,
      look at, in order to
4B  Discipline imprecision (with light whitelists):
      area, zone, region, part
4D  Hedge stacking (multi-word patterns):
      may possibly, could potentially, tend(s|ing) to suggest,
      is consistent with the possibility that, it is likely that ... may,
      might possibly, perhaps may
Cleft
      "It is well known that", "It should be noted that", "It is worth
      noting that", "It is important to note that", "It is interesting
      (to note) that", "It is clear that", "It is evident that",
      "It has been (long) established/recognised/argued/shown/
      demonstrated that"

Body extraction
---------------
We treat lines containing body("...") or bodyIndent("...") with a quoted
string argument as prose. JS r("plain text") inside body([...]) arrays is
also captured. Italic-math runs via mi("...") are *not* prose and are
skipped. The line number reported is the JS line in build_mg_manuscript.js.

Usage
-----
    python polish_audit.py
    python polish_audit.py --src build_mg_manuscript.js --report polish_audit_report.md
"""
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


HERE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Body-text extraction from build_mg_manuscript.js
# ---------------------------------------------------------------------------
# Match any of these prose-bearing JS string forms and capture the contents:
#   body("...")               — single-string body paragraph
#   bodyIndent("...")         — single-string indented paragraph
#   r("...")                  — plain text run (used inside body([...]) arrays)
# We exclude:
#   mi("...")                 — italic math var, not prose
#   refEntry("...")           — references list, not body
#   todo("...") / expand(...) — already-flagged placeholders
#   h1/h2/h3("...")           — headings, not body prose
#
# Implementation: scan JS source line-by-line; for each line, find all matches
# of the prose-bearing helpers and emit (line_no, text). String content is
# matched as `"..."` with escaped quotes allowed.

PROSE_HELPERS = ("body", "bodyIndent", "r")
# Match e.g.   body("text")   or   r("text", { bold: true })
# Group 1 = helper name, group 2 = string content (escaped quotes preserved)
PROSE_RE = re.compile(
    r"\b(" + "|".join(PROSE_HELPERS) + r")\s*\(\s*"
    r"\"((?:\\.|[^\"\\])*)\""
)


def extract_prose_lines(js_src: str) -> list[tuple[int, str]]:
    """Return [(1-based line number, prose chunk), ...] from the JS source.

    Each chunk corresponds to one body()/bodyIndent()/r() string argument.
    Long body paragraphs become a single chunk; multi-run body([...]) arrays
    yield multiple chunks (one per r("...") inside).
    """
    out: list[tuple[int, str]] = []
    for line_no, line in enumerate(js_src.splitlines(), start=1):
        for m in PROSE_RE.finditer(line):
            helper = m.group(1)
            text = m.group(2)
            # Unescape JS string escapes minimally
            text = text.replace(r"\"", "\"").replace(r"\\", "\\")
            # Filter: drop very short r("...") chunks that are pure punctuation
            # spacers like "       " or " = " etc. — these are math glue,
            # not prose
            if helper == "r" and (len(text.strip()) <= 2 or
                                   not re.search(r"[A-Za-z]", text)):
                continue
            out.append((line_no, text))
    return out


# ---------------------------------------------------------------------------
# Tier 4A — high-precision targets
# ---------------------------------------------------------------------------
TIER_4A_RULES = [
    ("now",          re.compile(r"\bnow\b", re.IGNORECASE),
     "delete; or 'has become' / 'since X' / explicit date"),
    ("currently",    re.compile(r"\bcurrently\b", re.IGNORECASE),
     "delete; or 'to date'"),
    ("nowadays",     re.compile(r"\bnowadays\b", re.IGNORECASE),
     "delete unconditionally"),
    ("at present",   re.compile(r"\bat\s+present\b", re.IGNORECASE),
     "delete; or 'to date'"),
    ("these days",   re.compile(r"\bthese\s+days\b", re.IGNORECASE),
     "delete unconditionally"),
    ("recently",     re.compile(r"\brecently\b", re.IGNORECASE),
     "add explicit date or year-bounded scope"),
    ("recent",       re.compile(r"\brecent\b", re.IGNORECASE),
     "'post-[year] work' / specific year-bounded scope"),
    ("thing(s)",     re.compile(r"\bthings?\b", re.IGNORECASE),
     "replace with specific noun"),
    ("get/got/...",  re.compile(r"\b(get|got|gets|getting|gotten)\b",
                                re.IGNORECASE),
     "obtain / acquire / yield / become / receive"),
    ("look at",      re.compile(r"\blook(s|ed|ing)?\s+at\b", re.IGNORECASE),
     "examine / address / investigate"),
    ("in order to",  re.compile(r"\bin\s+order\s+to\b", re.IGNORECASE),
     "'to'"),
]


# ---------------------------------------------------------------------------
# Tier 4B — discipline imprecision (lighter whitelist than校级课题 version)
# ---------------------------------------------------------------------------
TIER_4B_RULES = [
    {
        "name": "area",
        "pattern": re.compile(r"\barea(s)?\b", re.IGNORECASE),
        "rule": "specific noun; 'study area' OK, else 'region / domain'",
        "exempt": [
            re.compile(r"\bstudy\s+areas?\b", re.IGNORECASE),
            re.compile(r"\bgeographic\s+areas?\b", re.IGNORECASE),
            re.compile(r"\barea\s+under\s+the\b", re.IGNORECASE),  # AUC term
        ],
    },
    {
        "name": "zone",
        "pattern": re.compile(r"\bzone(s)?\b", re.IGNORECASE),
        "rule": "defined zones OK; flag bare 'zone'",
        "exempt": [
            re.compile(
                r"\b(?:fault|shear|deformation|tectonic|collision|fold|"
                r"subduction|suture|transition|hadal)\s+zones?\b",
                re.IGNORECASE,
            ),
            re.compile(r"\bTan-?Lu\s+(?:fault\s+)?zones?\b", re.IGNORECASE),
            re.compile(r"\bfault\s+zone\b", re.IGNORECASE),
        ],
    },
    {
        "name": "region",
        "pattern": re.compile(r"\bregion(s)?\b", re.IGNORECASE),
        "rule": "specific noun or drop bare 'the region'",
        "exempt": [
            re.compile(r"\bsource\s+regions?\b", re.IGNORECASE),
            re.compile(r"\bbasin\s+regions?\b", re.IGNORECASE),
            re.compile(
                r"\b(?:eastern|northern|southern|western|northeast|"
                r"northwest|southeast|southwest|hinge|continental|coastal)"
                r"[\s\-]+regions?\b",
                re.IGNORECASE,
            ),
        ],
    },
    {
        "name": "part",
        "pattern": re.compile(r"\bpart(s)?\b", re.IGNORECASE),
        "rule": "'eastern part of' → 'east of' / 'eastern margin of'",
        "exempt": [
            re.compile(r"\bin\s+part\b", re.IGNORECASE),
            re.compile(r"\bpart-and-parcel\b", re.IGNORECASE),
            re.compile(r"\bparts?\s+per\s+(?:million|thousand)\b",
                       re.IGNORECASE),
            re.compile(r"\bpart\s+of\s+a\b", re.IGNORECASE),
        ],
    },
]


# ---------------------------------------------------------------------------
# Tier 4E — contrastive connectors (校级课题 phase_g rule)
# ---------------------------------------------------------------------------
# Author-imposed rule (校级课题 v6 phase G): zero `but`, zero `yet`, zero
# `though` as contrastive conjunctions. Replacements drawn from
# {while, whereas, nevertheless, however-via-split, where, parataxis,
# participial -ing, despite + gerund}.
#
# Negative-temporal "not yet" / "yet exists" / "has not yet been"
# patterns are KEPT — they are idiomatic English, not contrastive.
NEG_YET_RE = re.compile(
    r"\b(?:not|never|nor|no|hardly|barely|hasn't|haven't|hadn't|isn't|"
    r"aren't|wasn't|weren't|won't|wouldn't|cannot|can't|couldn't|"
    r"shouldn't|doesn't|don't|didn't)\s+(?:\w+\s+){0,4}yet\b",
    re.IGNORECASE,
)
# Also "no systematic X yet exists" / "no Y yet exists" patterns
NEG_YET_EXISTS_RE = re.compile(
    r"\bno\s+(?:\w+\s+){0,4}yet\s+(?:exists?|exist|appears?|appeared)\b",
    re.IGNORECASE,
)


TIER_4E_PATTERNS = [
    ("yet (contrastive)", re.compile(r"\byet\b", re.IGNORECASE),
     "→ split into two sentences; or use 'while' / 'whereas' / 'however'"),
    ("but",               re.compile(r"\bbut\b", re.IGNORECASE),
     "→ 'while' / 'whereas' / 'however (via split)' / parataxis / participial"),
    ("though (concessive)", re.compile(r"\bthough\b", re.IGNORECASE),
     "→ 'despite + gerund' / split + 'nevertheless'"),
    ("even though",       re.compile(r"\beven\s+though\b", re.IGNORECASE),
     "→ 'despite + gerund' / split + 'nevertheless'"),
]


# ---------------------------------------------------------------------------
# Tier 4F — `which` (校级课题 phase_e + phase_f rule: zero `which` in body)
# ---------------------------------------------------------------------------
# Strict rule: zero `which` relative pronouns in body. Replace via:
#   - drop + participial (-ing): ", which captures X" → ", capturing X"
#   - preposition + which → `where` (locative): "in which X happens" → "where"
#   - drop + restructure: "the methods by which X is Y-ed" → "the methods that Y X"
#   - sentence split: ", which Z" → ". This Z" / "; this Z"
#   - drop + adjective: "operators on which inversion relies" → "underpinning"
#
# EXEMPT: interrogative-`which` (the question-word use, not the relative pronoun).
# Detected heuristically by looking for a preceding verb of inquiry/perception
# (knowing/asking/interrogating/identifying/determining/showing/specifying/...).
INTERROGATIVE_WHICH_TRIGGERS_RE = re.compile(
    r"\b(?:know(?:s|ing|n)?|ask(?:s|ing|ed)?|interrogat(?:e|es|ing|ed)|"
    r"identif(?:y|ies|ying|ied)|determin(?:e|es|ing|ed)|"
    r"specif(?:y|ies|ying|ied)|select(?:s|ing|ed)?|"
    r"distinguish(?:es|ing|ed)?|decid(?:e|es|ing|ed))\b",
    re.IGNORECASE,
)

TIER_4F_PATTERNS = [
    ("which (relative)", re.compile(r"\bwhich\b"),
     "→ drop + participial / 'where' / sentence split / restructure"),
]


# ---------------------------------------------------------------------------
# Tier 4G — `because` (校级课题 phase_h rule: zero `because` in body)
# ---------------------------------------------------------------------------
TIER_4G_PATTERNS = [
    ("because", re.compile(r"\bbecause\b", re.IGNORECASE),
     "→ 'given that' / 'as' / 'since' / sentence inversion"),
]


# ---------------------------------------------------------------------------
# Tier 4H — B4 weak verb / nominalization patterns (校级课题 refs精读 B4 table)
# ---------------------------------------------------------------------------
TIER_4H_PATTERNS = [
    ("show that",        re.compile(r"\bshow(?:s|ed|n)?\s+that\b",
                                     re.IGNORECASE),
     "→ 'demonstrate / document / record / reveal / resolve that'"),
    ("similar to",       re.compile(r"\bsimilar\s+to\b", re.IGNORECASE),
     "→ 'mirrors' / 'closely matches' / 'echoes'"),
    ("caused by",        re.compile(r"\b(?:is|are|was|were)\s+caused\s+by\b",
                                     re.IGNORECASE),
     "→ 'is/are attributed to' / 'is/are ascribed to'"),
    ("important role",   re.compile(r"\bimportant\s+role\b", re.IGNORECASE),
     "→ 'governs' / 'underpins' / 'drives' (rewrite as verb)"),
    ("of great importance", re.compile(r"\bof\s+great\s+importance\b",
                                        re.IGNORECASE),
     "→ rewrite as verb: 'enables ...'"),
    ("make a contribution", re.compile(
        r"\bmake\s+(?:a|an)?\s*contribution(?:s)?\s+to\b", re.IGNORECASE),
     "→ 'contributes to' / 'advances'"),
    ("there is/are many", re.compile(
        r"\bthere\s+(?:is|are|exists?|exist)\s+(?:many|a\s+number\s+of|"
        r"a\s+lot\s+of|several|numerous)\b", re.IGNORECASE),
     "→ recast with active verb"),
    ("In this paper, we", re.compile(
        r"\bIn\s+this\s+(?:paper|study|review|work)[,\s]+we\b", re.IGNORECASE),
     "→ 'Here we'"),
    ("it is found that", re.compile(
        r"\b(?:it\s+is\s+found|it\s+can\s+be\s+seen|we\s+can\s+see)\s+that\b",
        re.IGNORECASE),
     "→ '<subject> reveals/demonstrates/resolves that'"),
    ("respectively",     re.compile(r"\brespectively\b", re.IGNORECASE),
     "→ direct pairing; drop 'respectively' (校级课题 B4)"),
    ("combining with",   re.compile(r"\bcombining\s+with\b", re.IGNORECASE),
     "→ 'combined with' / 'integrated with' (dangling participle)"),
    ("plays a role",     re.compile(
        r"\bplay(?:s|ed|ing)?\s+(?:a|an|the)?\s*(?:role|part)\s+in\b",
        re.IGNORECASE),
     "→ 'governs/underpins/drives X'"),
]


# ---------------------------------------------------------------------------
# Tier 4D — hedge stacking
# ---------------------------------------------------------------------------
TIER_4D_PATTERNS = [
    (re.compile(r"\bmay\s+possibly\b", re.IGNORECASE), "drop one → 'may'"),
    (re.compile(r"\bcould\s+potentially\b", re.IGNORECASE),
     "drop one → 'could'"),
    (re.compile(r"\btend(s|ing)?\s+to\s+suggest\b", re.IGNORECASE),
     "→ 'suggest'"),
    (re.compile(r"\bis\s+consistent\s+with\s+the\s+possibility\s+that\b",
                re.IGNORECASE),
     "drop 'the possibility that' → 'is consistent with'"),
    (re.compile(r"\bit\s+is\s+likely\s+that\b[^.]{1,40}\bmay\b",
                re.IGNORECASE),
     "drop one of 'is likely' / 'may'"),
    (re.compile(r"\bmight\s+possibly\b", re.IGNORECASE), "drop one"),
    (re.compile(r"\bperhaps\s+may\b", re.IGNORECASE), "drop one"),
]


# ---------------------------------------------------------------------------
# Cleft / discourse-throat-clearing
# ---------------------------------------------------------------------------
CLEFT_PATTERNS = [
    (re.compile(r"\bIt\s+is\s+well\s+known\s+that\b", re.IGNORECASE),
     "delete; assert directly"),
    (re.compile(r"\bIt\s+should\s+be\s+noted\s+that\b", re.IGNORECASE),
     "delete; assert directly"),
    (re.compile(r"\bIt\s+is\s+worth\s+noting\s+that\b", re.IGNORECASE),
     "delete; assert directly"),
    (re.compile(r"\bIt\s+is\s+important\s+to\s+note\s+that\b",
                re.IGNORECASE),
     "delete; assert directly"),
    (re.compile(r"\bIt\s+is\s+interesting\s+(?:to\s+note\s+)?that\b",
                re.IGNORECASE),
     "delete; assert directly"),
    (re.compile(r"\bIt\s+is\s+clear\s+that\b", re.IGNORECASE),
     "delete; assert directly"),
    (re.compile(r"\bIt\s+is\s+evident\s+that\b", re.IGNORECASE),
     "delete; assert directly"),
    (re.compile(
        r"\bIt\s+has\s+been\s+(?:long\s+)?"
        r"(?:established|recognised|recognized|argued|shown|demonstrated)"
        r"\s+that\b",
        re.IGNORECASE,
    ),
     "rewrite as direct citation: '(Author Year) showed that ...'"),
]


# ---------------------------------------------------------------------------
# Hit collection
# ---------------------------------------------------------------------------
@dataclass
class Hit:
    line_no: int
    matched: str
    context: str
    rule: str


def context_window(text: str, start: int, end: int, width: int = 60) -> str:
    left = text[max(0, start - width):start]
    right = text[end:end + width]
    if start - width > 0:
        left = "…" + left
    if end + width < len(text):
        right = right + "…"
    marked = f"**{text[start:end]}**"
    return f"{left}{marked}{right}"


def _is_exempt(text: str, start: int, end: int,
               exempts: list[re.Pattern]) -> bool:
    for ex in exempts:
        for em in ex.finditer(text):
            if em.start() <= start and em.end() >= end:
                return True
    return False


def collect_hits(prose: list[tuple[int, str]]) -> dict[str, list[Hit]]:
    results: dict[str, list[Hit]] = defaultdict(list)

    for line_no, text in prose:
        for name, pat, rule in TIER_4A_RULES:
            for m in pat.finditer(text):
                results[f"4A:{name}"].append(Hit(
                    line_no=line_no,
                    matched=text[m.start():m.end()],
                    context=context_window(text, m.start(), m.end()),
                    rule=rule,
                ))
        for entry in TIER_4B_RULES:
            for m in entry["pattern"].finditer(text):
                if _is_exempt(text, m.start(), m.end(), entry["exempt"]):
                    continue
                results[f"4B:{entry['name']}"].append(Hit(
                    line_no=line_no,
                    matched=text[m.start():m.end()],
                    context=context_window(text, m.start(), m.end()),
                    rule=entry["rule"],
                ))
        for pat, rule in TIER_4D_PATTERNS:
            for m in pat.finditer(text):
                results["4D"].append(Hit(
                    line_no=line_no,
                    matched=text[m.start():m.end()],
                    context=context_window(text, m.start(), m.end()),
                    rule=rule,
                ))
        # Tier 4E — contrastive connectors. For `yet`, exempt "not yet"
        # negative-temporal idiom (校级课题 rule applies only to contrastive
        # `yet`, not adverbial-temporal `yet`).
        for name, pat, rule in TIER_4E_PATTERNS:
            for m in pat.finditer(text):
                s, e = m.start(), m.end()
                if name.startswith("yet"):
                    if (NEG_YET_RE.search(text[max(0, s - 60):e]) or
                            NEG_YET_EXISTS_RE.search(
                                text[max(0, s - 30):e + 30])):
                        continue  # KEEP: "not yet" / "no X yet exists"
                results[f"4E:{name}"].append(Hit(
                    line_no=line_no,
                    matched=text[m.start():m.end()],
                    context=context_window(text, m.start(), m.end()),
                    rule=rule,
                ))
        # Tier 4F — `which`. Exempt interrogative-`which` (question word).
        # Heuristic: a verb of inquiry/perception within ~80 chars before
        # (covers parallel double-interrogative "which X ... with which Y").
        for name, pat, rule in TIER_4F_PATTERNS:
            for m in pat.finditer(text):
                s, e = m.start(), m.end()
                lookback = text[max(0, s - 80):s]
                if INTERROGATIVE_WHICH_TRIGGERS_RE.search(lookback):
                    continue  # KEEP: interrogative "ask/know which X..."
                results[f"4F:{name}"].append(Hit(
                    line_no=line_no,
                    matched=text[m.start():m.end()],
                    context=context_window(text, m.start(), m.end()),
                    rule=rule,
                ))
        # Tier 4G — `because`
        for name, pat, rule in TIER_4G_PATTERNS:
            for m in pat.finditer(text):
                results[f"4G:{name}"].append(Hit(
                    line_no=line_no,
                    matched=text[m.start():m.end()],
                    context=context_window(text, m.start(), m.end()),
                    rule=rule,
                ))
        # Tier 4H — B4 weak verbs / nominalizations
        for name, pat, rule in TIER_4H_PATTERNS:
            for m in pat.finditer(text):
                results[f"4H:{name}"].append(Hit(
                    line_no=line_no,
                    matched=text[m.start():m.end()],
                    context=context_window(text, m.start(), m.end()),
                    rule=rule,
                ))
        for pat, rule in CLEFT_PATTERNS:
            for m in pat.finditer(text):
                results["cleft"].append(Hit(
                    line_no=line_no,
                    matched=text[m.start():m.end()],
                    context=context_window(text, m.start(), m.end()),
                    rule=rule,
                ))
    return results


def render(hits: dict[str, list[Hit]], src_name: str,
           prose_chunk_count: int, total_words: int) -> str:
    out: list[str] = []
    out.append(f"# Polish audit — `{src_name}`")
    out.append("")
    out.append(f"- Prose chunks scanned: **{prose_chunk_count}**")
    out.append(f"- Body words audited:   **{total_words:,}**")
    out.append("")

    def section(title: str, rows: list[Hit], rule_header: bool = False):
        if not rows:
            out.append(f"### {title} — _0 hits, clean_")
            out.append("")
            return
        out.append(f"### {title} — **{len(rows)} hits**")
        out.append("")
        out.append("| JS line | Match | Context | Rule |")
        out.append("|---:|---|---|---|")
        for h in rows:
            ctx = h.context.replace("|", r"\|")
            out.append(
                f"| {h.line_no} | `{h.matched}` | {ctx} | {h.rule} |"
            )
        out.append("")

    # Tier 4A
    out.append("## Tier 4A — High-precision (almost always cut/replace)")
    out.append("")
    for name, _, _ in TIER_4A_RULES:
        section(f"`{name}`", hits.get(f"4A:{name}", []))

    # Tier 4B
    out.append("## Tier 4B — Discipline imprecision "
               "(non-exempt only)")
    out.append("")
    for entry in TIER_4B_RULES:
        section(f"`{entry['name']}`", hits.get(f"4B:{entry['name']}", []))

    # Tier 4D
    out.append("## Tier 4D — Hedge stacking")
    out.append("")
    section("Hedge stacks", hits.get("4D", []))

    # Tier 4E
    out.append("## Tier 4E — Contrastive connectors "
               "(but / yet / though / even though)")
    out.append("")
    out.append(
        "_Rule (校级课题 phase_g): zero `but`, `yet`, `though`. "
        "'not yet' negative-temporal is auto-exempted._")
    out.append("")
    for name, _, _ in TIER_4E_PATTERNS:
        section(f"`{name}`", hits.get(f"4E:{name}", []))

    # Tier 4F
    out.append("## Tier 4F — Relative `which`")
    out.append("")
    out.append(
        "_Rule (校级课题 phase_e + phase_f): zero `which` in body. "
        "Interrogative-`which` ('know/ask/interrogate which X') auto-exempted._")
    out.append("")
    for name, _, _ in TIER_4F_PATTERNS:
        section(f"`{name}`", hits.get(f"4F:{name}", []))

    # Tier 4G
    out.append("## Tier 4G — `because`")
    out.append("")
    out.append("_Rule (校级课题 phase_h): zero `because` in body._")
    out.append("")
    for name, _, _ in TIER_4G_PATTERNS:
        section(f"`{name}`", hits.get(f"4G:{name}", []))

    # Tier 4H
    out.append("## Tier 4H — Weak verbs / nominalizations "
               "(校级课题 refs精读 B4)")
    out.append("")
    for name, _, _ in TIER_4H_PATTERNS:
        section(f"`{name}`", hits.get(f"4H:{name}", []))

    # Cleft
    out.append("## Cleft / throat-clearing")
    out.append("")
    section("Cleft constructions", hits.get("cleft", []))

    # Summary
    t4a = sum(len(v) for k, v in hits.items() if k.startswith("4A:"))
    t4b = sum(len(v) for k, v in hits.items() if k.startswith("4B:"))
    t4d = len(hits.get("4D", []))
    t4e = sum(len(v) for k, v in hits.items() if k.startswith("4E:"))
    t4f = sum(len(v) for k, v in hits.items() if k.startswith("4F:"))
    t4g = sum(len(v) for k, v in hits.items() if k.startswith("4G:"))
    t4h = sum(len(v) for k, v in hits.items() if k.startswith("4H:"))
    tcl = len(hits.get("cleft", []))
    out.append("## Summary")
    out.append("")
    out.append(f"- Tier 4A (high-precision):     **{t4a}**")
    out.append(f"- Tier 4B (post-whitelist):     **{t4b}**")
    out.append(f"- Tier 4D (hedge stacking):     **{t4d}**")
    out.append(f"- Tier 4E (contrastive conn.):  **{t4e}**")
    out.append(f"- Tier 4F (relative which):     **{t4f}**")
    out.append(f"- Tier 4G (because):            **{t4g}**")
    out.append(f"- Tier 4H (weak verbs / B4):    **{t4h}**")
    out.append(f"- Cleft constructions:          **{tcl}**")
    total = t4a + t4b + t4d + t4e + t4f + t4g + t4h + tcl
    out.append(f"- **Grand total:                 {total}**")
    out.append("")
    out.append("**Suggested review order**: "
               "4G → 4E → 4F → 4H → 4A → cleft → 4D → 4B.")
    return "\n".join(out) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--src", type=Path,
                   default=HERE / "build_mg_manuscript.js")
    p.add_argument("--report", type=Path,
                   default=HERE / "第一篇_MG_DZ方法" / "polish_audit_report.md")
    args = p.parse_args()
    if not args.src.exists():
        p.error(f"Source not found: {args.src}")

    js_src = args.src.read_text(encoding="utf-8")
    prose = extract_prose_lines(js_src)
    total_words = sum(len(t.split()) for _, t in prose)
    hits = collect_hits(prose)
    report = render(hits, args.src.name, len(prose), total_words)
    args.report.write_text(report, encoding="utf-8")

    t4a = sum(len(v) for k, v in hits.items() if k.startswith("4A:"))
    t4b = sum(len(v) for k, v in hits.items() if k.startswith("4B:"))
    t4d = len(hits.get("4D", []))
    t4e = sum(len(v) for k, v in hits.items() if k.startswith("4E:"))
    t4f = sum(len(v) for k, v in hits.items() if k.startswith("4F:"))
    t4g = sum(len(v) for k, v in hits.items() if k.startswith("4G:"))
    t4h = sum(len(v) for k, v in hits.items() if k.startswith("4H:"))
    tcl = len(hits.get("cleft", []))
    total = t4a + t4b + t4d + t4e + t4f + t4g + t4h + tcl
    print(f"polish-audit: 4A={t4a} 4B={t4b} 4D={t4d} 4E={t4e} 4F={t4f} "
          f"4G={t4g} 4H={t4h} cleft={tcl} total={total}")
    print(f"chunks={len(prose)}  body_words={total_words:,}")
    print(f"report → {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
