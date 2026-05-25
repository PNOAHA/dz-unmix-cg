"""
render_equations_cg.py — render the 6 displayed equations of the C&G manuscript
(第一篇 Computers & Geosciences 版) as standalone PNGs using matplotlib mathtext.
Computer Modern font (LaTeX default look) without requiring a system LaTeX install.

Output: Eq_1.png ... Eq_6.png  (600 dpi, white bg, tight bbox) in figures/.
The equation number is NOT baked into the image — build_cg_manuscript.js (Phase D)
emits "(1)" etc. as a right-flushed TextRun beside the centered image.

Parallel to render_equations.py (which renders the v23/MATG version's 7 equations).
Original render_equations.py is preserved unchanged for v23 archival reproducibility.

Mapping vs v23 (REBUILD_BLUEPRINT_v1.md):
  v23 Eq 3.1 / 3.2 / 6.3  → dropped (general inverse / regularized inverse / surrogate loss not in C&G scope)
  v23 Eq 6.1 → new Eq 1   (simplified: zircon-only, no multi-modal)
  v23 Eq 6.2 → new Eq 2   (rewritten: multinomial + Gaussian, not generic conditional indep)
  (new) Eq 3              (constraints: non-negativity + simplex — was implicit in v23)
  v23 Eq 6.4 → new Eq 4   (Bayesian posterior — unchanged in form)
  v23 Eq 4.1 → new Eq 5   (source-to-sink mass balance — simplified continuity form)
  (new) Eq 6              (KL multiplicative update — the §4 algorithm core, not in v23)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- Font setup: Computer Modern via mathtext, no system LaTeX needed ----
plt.rcParams["mathtext.fontset"] = "cm"       # Computer Modern, LaTeX default look
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["DejaVu Serif"]

HERE = Path(__file__).parent

# 6 displayed equations from 08_manuscript_cg_draft.md, in LaTeX form.
# Each entry: (output_filename_stem, latex_body)
# Wrapped in $...$ at render time. No equation numbers — those go in docx.
EQUATIONS = [
    # Eq 1 — Forward operator (§3.2). Simplified zircon-only single-modal form.
    ("Eq_1",
     r"d = F(w) + \varepsilon = w\,H + \varepsilon"),

    # Eq 2 — Joint likelihood (§3.3). Multinomial grain allocation × Gaussian
    # analytical noise, conditional independence under invariant LA-ICP-MS pipeline.
    ("Eq_2",
     r"p(x\,|\,w) = \prod_{j}\,"
     r"p_{\mathrm{multi}}\!\left(x_{j}\,|\,g,\,(wH)_{j}\right)\,\cdot\,"
     r"p_{\mathrm{gauss}}\!\left(x_{j}\,|\,\sigma_{j}\right)"),

    # Eq 3 — Physical constraints (§3.4). Non-negativity + simplex.
    ("Eq_3",
     r"w_{k}\,\geq\,0\;\;\mathrm{for}\;\,k=1,\ldots,K,\quad "
     r"\sum_{k=1}^{K} w_{k} = 1"),

    # Eq 4 — Bayesian posterior (§3.4). Dirichlet prior on the simplex.
    ("Eq_4",
     r"p(w\,|\,x)\;\propto\;p(x\,|\,w)\,p(w)"),

    # Eq 5 — Source-to-sink mass balance (§3.5). Continuity equation linking
    # source erosion E_k, routing efficiency K_k, sink deposition D, transit storage S.
    ("Eq_5",
     r"\partial_{t} D(x,t) = "
     r"\sum_{k=1}^{K} K_{k}(x,t)\,E_{k}(t) - \partial_{t} S(x,t)"),

    # Eq 6 — KL multiplicative update (§4.1). Lee & Seung 2001 algorithm,
    # adapted to supervised setting with H held fixed. Element-wise division
    # X/(W^(t) H); row-normalize W after each iteration to project onto simplex.
    ("Eq_6",
     r"W^{(t+1)}_{ij} = W^{(t)}_{ij}\,\cdot\,"
     r"\frac{\left[\,\left(X\,/\,(W^{(t)} H)\right)\,H^{\top}\,\right]_{ij}}"
     r"{\left[\,\mathbf{1}\,H^{\top}\,\right]_{ij}}"),
]

FONTSIZE = 16
DPI = 600
PAD = 0.05


def render_one(stem: str, latex: str) -> Path:
    """Render a single equation to <stem>.png and return the output path.

    Same figtext + bbox_inches='tight' trick as render_equations.py:
    yields per-equation aspect ratios proportional to formula length.
    """
    out = HERE / "figures" / f"{stem}.png"

    fig = plt.figure(figsize=(10.0, 1.5), dpi=DPI)
    fig.text(
        0.5, 0.5,
        f"${latex}$",
        ha="center", va="center",
        fontsize=FONTSIZE,
        color="black",
    )

    fig.savefig(
        out,
        dpi=DPI,
        bbox_inches="tight",
        pad_inches=PAD,
        transparent=False,
        facecolor="white",
    )
    plt.close(fig)
    return out


def main() -> int:
    print(f"Rendering {len(EQUATIONS)} C&G equations to {HERE / 'figures'} ...")
    for stem, latex in EQUATIONS:
        out = render_one(stem, latex)
        size_kb = out.stat().st_size / 1024.0
        print(f"  {stem}.png  ({size_kb:6.1f} KB)")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
