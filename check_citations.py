"""Cross-check in-text citations against the reference list in
build_mg_manuscript.js. Reports refs that aren't cited and citations
that don't have a matching ref entry.

Matching key: "FirstAuthorSurname YEAR" (e.g., "Wang 2016").
The reference list entries all have unique (surname, year) pairs.
"""
import re
from pathlib import Path

src = Path(__file__).parent / "build_mg_manuscript.js"
content = src.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# 1) Extract reference list entries
# ---------------------------------------------------------------------------
ref_strings = re.findall(r'refEntry\("([^"]+)"\)', content)

ref_db = {}   # key="Surname YEAR" → first 65 chars of full ref
for ref in ref_strings:
    # First "word" — handles unicode (Métivier), letters and apostrophes
    m_surname = re.match(r"^([A-Z][\wÀ-ÿé]*)", ref)
    m_year = re.search(r"\((\d{4})\)", ref)
    if not (m_surname and m_year):
        print(f"WARN: failed to parse ref → {ref[:80]}")
        continue
    key = f"{m_surname.group(1)} {m_year.group(1)}"
    if key in ref_db:
        print(f"WARN: duplicate ref key {key!r}")
    ref_db[key] = ref[:70] + ("…" if len(ref) > 70 else "")

# ---------------------------------------------------------------------------
# 2) Extract body text — everything except refEntry() lines
# ---------------------------------------------------------------------------
body_text_lines = [
    ln for ln in content.split("\n")
    if "refEntry(" not in ln
]
body_text = "\n".join(body_text_lines)

# ---------------------------------------------------------------------------
# 3) Find in-text citations
#    Patterns:
#      Smith (2020)
#      Smith and Jones (2020)
#      Smith et al. (2020)
#      (Smith 2020)
#      (Smith and Jones 2020)
#      (Smith et al. 2020; Jones et al. 2021)
#      (Smith et al. 2018, 2019)        ← same first author, two years
# ---------------------------------------------------------------------------
SURNAME = r"([A-Z][\wÀ-ÿé']+)"
ETAL = r"(?:\s+et\s+al\.?)?"
COAUTH = r"(?:\s+(?:and|&)\s+[A-Z][\wÀ-ÿé']+)?"
PRE = SURNAME + COAUTH + ETAL

citations = set()

# Pattern A:  Surname [coauth] [et al.] (YYYY)   —— inline form
for m in re.finditer(PRE + r"\s+\((\d{4})\)", body_text):
    s, y = m.group(1), m.group(2)
    if 1900 <= int(y) <= 2030:
        citations.add(f"{s} {y}")

# Pattern A2: Surname [coauth] [et al.] (YYYY, YYYY)  —— same author, two years inline
for m in re.finditer(PRE + r"\s+\((\d{4}),\s*(\d{4})\)", body_text):
    s, y1, y2 = m.group(1), m.group(2), m.group(3)
    if 1900 <= int(y1) <= 2030 and 1900 <= int(y2) <= 2030:
        citations.add(f"{s} {y1}")
        citations.add(f"{s} {y2}")

# Pattern B:  Surname [coauth] [et al.] YYYY    —— inside parens
# Match year preceded by surname, separated by space; followed by ),; or end
for m in re.finditer(PRE + r"\s+(\d{4})(?=[\),;\s])", body_text):
    s, y = m.group(1), m.group(2)
    if 1900 <= int(y) <= 2030:
        citations.add(f"{s} {y}")

# Pattern C:  Surname et al. YYYYa, YYYYb       —— two years same author
for m in re.finditer(PRE + r"\s+(\d{4}),\s*(\d{4})", body_text):
    s, y1, y2 = m.group(1), m.group(2), m.group(3)
    if 1900 <= int(y1) <= 2030 and 1900 <= int(y2) <= 2030:
        citations.add(f"{s} {y1}")
        citations.add(f"{s} {y2}")

# Filter false positives that are clearly not author surnames
NOT_SURNAMES = {
    "Section", "Sect", "Equation", "Eq", "Figure", "Fig", "Layer",
    "Table", "Chapter", "January", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    "Macrostrat", "Geological", "Hailar", "Songliao", "Erlian",
    "Cretaceous", "Mesozoic", "Late", "Early", "China", "Asia",
    "FaultSeg3D", "ClinoformNet", "Mongol", "Paleo", "Pacific",
    "FastScape", "Badlands", "PANGAEA", "GPlates", "EaDz", "OneSediment",
    "K2", "GeoGalactica", "Bayesian", "American", "After", "Before",
    "Since", "During", "From",
}

# Aliases for multi-word surnames where the in-text canonical surname differs
# from the first word of the reference entry. Maps: parsed → ref-list key.
SURNAME_ALIAS = {
    "Lima": "Pires",   # Pires de Lima R, Duarte D, ... (2020)
}

# Apply alias and filter
citations_remapped = set()
for c in citations:
    s, y = c.rsplit(" ", 1)
    if s in NOT_SURNAMES:
        continue
    s = SURNAME_ALIAS.get(s, s)
    citations_remapped.add(f"{s} {y}")
citations = citations_remapped

# ---------------------------------------------------------------------------
# 4) Compare and report
# ---------------------------------------------------------------------------
ref_keys = set(ref_db.keys())

uncited_refs = sorted(ref_keys - citations)
unmatched_cites = sorted(citations - ref_keys)
matched = sorted(ref_keys & citations)

print(f"\n========== Citation cross-check report ==========")
print(f"References in list:        {len(ref_keys):>4}")
print(f"Unique in-text citations:  {len(citations):>4}")
print(f"Matched both ways:         {len(matched):>4}")
print(f"Refs not cited in text:    {len(uncited_refs):>4}")
print(f"Cites with no ref entry:   {len(unmatched_cites):>4}")

print("\n========== Refs in list but NOT cited in text ==========")
if uncited_refs:
    for k in uncited_refs:
        print(f"  - {k:<28}  {ref_db[k][:80]}")
else:
    print("  (none — every ref is cited)")

print("\n========== Cites in text but NOT in ref list ==========")
if unmatched_cites:
    for k in unmatched_cites:
        print(f"  -{k}")
else:
    print("  (none — every cite resolves to a ref)")

print("\n========== Matched references (sanity) ==========")
print(f"  {len(matched)} successful matches.")
