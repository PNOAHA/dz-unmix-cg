"""Fig 4 — Workflow / pipeline diagram for the proposed sediment–tectonic
inversion (operational view of Section 6.2.2).

Four merged stages in a single LTR row. Each stage's body is rendered as
a stack of independent text rows, so multi-line math (∏, ∝) does not
overflow the box. Feedback arc uses an explicit cubic-Bezier path that
dips well below the boxes.

Output: Fig4_workflow.png/pdf/eps at MG full-width (174 mm).
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path as MplPath
from matplotlib.patches import FancyArrowPatch, PathPatch

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.linewidth": 0.5,
    "ps.fonttype": 42,
    "pdf.fonttype": 42,
    # svg.fonttype='none' keeps text as <text> SVG elements referencing the
    # named font (Arial). Illustrator opens these as fully editable text,
    # NOT as paths. This is the校级课题 phase_n technique for SVG-Illustrator
    # handoff. Tradeoff: math via $...$ still renders as paths (mathtext
    # path-rendering), so equation glyphs are not directly editable — but
    # text labels (headers, captions, reference tags) are.
    "svg.fonttype": "none",
})

OKABE = {
    "orange":     "#E69F00",
    "sky":        "#56B4E9",
    "green":      "#009E73",
    "blue":       "#0072B2",
    "vermilion":  "#D55E00",
}
OKABE_LIGHT = {
    "orange":     "#FCF5E6",
    "sky":        "#EEF8FD",
    "green":      "#E5F5F1",
    "vermilion":  "#FBEEE5",
}

FIG_W_IN, FIG_H_IN = 6.85, 4.2
fig, ax = plt.subplots(figsize=(FIG_W_IN, FIG_H_IN), dpi=300)
ax.set_xlim(0, 100); ax.set_ylim(0, 100)
ax.set_aspect("auto"); ax.axis("off")


# ---------------------------------------------------------------- 4 stages
# Each stage's "rows" is a list of (text, fontsize) rendered as a vertical
# stack inside the box body area.
STAGES = [
    {"header_top":    "1. Data",
     "header_bottom": "Layer 1",
     "rows": [
         (r"$d_z,\;d_f,\;d_s$", 10),
         ("FAIR-standardized", 8),
     ],
     "ref":           "Sect. 6.2.1",
     "color":         "sky"},

    {"header_top":    "2. Model",
     "header_bottom": "F + likelihood",
     "rows": [
         (r"$d = F(\theta) + \varepsilon$", 9.5),
         (r"$p(d|\theta) = \prod_k p(d_k|\theta)$", 8.5),
     ],
     "ref":           "Eqs. (6.1)–(6.2)",
     "color":         "orange"},

    {"header_top":    "3. Inversion",
     "header_bottom": "PIML + Bayesian",
     "rows": [
         (r"$N(\theta;\psi) \approx F(\theta)$", 9.5),
         (r"$p(\theta|d) \propto p(d|N)\,p(\theta)$", 8.5),
     ],
     "ref":           "Eqs. (6.3)–(6.4)",
     "color":         "green"},

    {"header_top":    "4. Validation",
     "header_bottom": "Layer 3",
     "rows": [
         ("Posterior", 10),
         ("predictive checks", 9.5),
     ],
     "ref":           "Sect. 6.2.3",
     "color":         "vermilion"},
]


# ---------------------------------------------------------------- layout
# margin_x 2→1.5 and gap 6→4 widens each box from 19.5 to 21.25 units
# (+9% horizontal room), needed because the prod formula `p(d|θ) = ∏_k p(d_k|θ)`
# overflowed at the prior layout. Forward-arrow length is still gap-1=3 units
# at scale 14 which renders cleanly.
margin_x = 1.5
gap = 4
n = len(STAGES)
box_w = (100 - 2 * margin_x - (n - 1) * gap) / n
box_h = 44
box_y = 50

for i, s in enumerate(STAGES):
    x = margin_x + i * (box_w + gap)
    color = OKABE[s["color"]]
    light = OKABE_LIGHT[s["color"]]

    # Box body
    ax.add_patch(patches.Rectangle(
        (x, box_y), box_w, box_h,
        linewidth=1.0, edgecolor=color, facecolor=light,
    ))
    # Header band — taller for 2 lines
    head_h = 14
    ax.add_patch(patches.Rectangle(
        (x, box_y + box_h - head_h), box_w, head_h,
        linewidth=0, edgecolor="none", facecolor=color,
    ))
    cx = x + box_w / 2

    # 2-line header
    ax.text(cx, box_y + box_h - 4.0, s["header_top"],
            color="white", fontsize=10, fontweight="bold",
            ha="center", va="center")
    ax.text(cx, box_y + box_h - 9.5, s["header_bottom"],
            color="white", fontsize=8.5,
            ha="center", va="center", style="italic")

    # Body rows: stack vertically, centered in body area
    rows = s["rows"]
    body_top = box_y + box_h - head_h - 2     # below header band
    body_bot = box_y + 7                       # above ref text
    body_mid = (body_top + body_bot) / 2
    if len(rows) == 1:
        ax.text(cx, body_mid, rows[0][0],
                fontsize=rows[0][1], ha="center", va="center", color="#1A1A1A")
    elif len(rows) == 2:
        spacing = 5
        ax.text(cx, body_mid + spacing / 2, rows[0][0],
                fontsize=rows[0][1], ha="center", va="center", color="#1A1A1A")
        ax.text(cx, body_mid - spacing - 1, rows[1][0],
                fontsize=rows[1][1], ha="center", va="center", color="#1A1A1A")

    # Reference at bottom (italic gray)
    ax.text(cx, box_y + 3, s["ref"],
            fontsize=8, style="italic", color="#666666",
            ha="center", va="center")


# ---------------------------------------------------------------- forward arrows
arrow_y = box_y + box_h / 2
for i in range(n - 1):
    x_from = margin_x + i * (box_w + gap) + box_w
    x_to   = margin_x + (i + 1) * (box_w + gap)
    ax.add_patch(FancyArrowPatch(
        (x_from + 0.5, arrow_y), (x_to - 0.5, arrow_y),
        arrowstyle="-|>", color="#1A1A1A",
        linewidth=2.2, mutation_scale=14,
    ))


# ---------------------------------------------------------------- feedback arc (validation → model + inversion)
# Cubic Bezier U-shape spanning from stage 4 back to stage 2 — visually showing
# the loop closes the entire forward chain. Arc starts well below boxes and
# ends well below boxes, with arrowhead pointing back UP into stage 2.
fb_start_x = margin_x + 3 * (box_w + gap) + box_w / 2  # stage 4 center bottom
fb_end_x   = margin_x + 1 * (box_w + gap) + box_w / 2  # stage 2 center bottom
fb_y_top   = box_y - 4                                  # 4 units below box bottom
fb_y_dip   = 18                                          # arc dips to here

# Bezier path with control points pulling the curve DOWN
verts = [
    (fb_start_x, fb_y_top),
    (fb_start_x, fb_y_dip),
    (fb_end_x,   fb_y_dip),
    (fb_end_x,   fb_y_top + 1.5),     # leave room for arrowhead
]
codes = [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4]
ax.add_patch(PathPatch(MplPath(verts, codes),
                       fill=False, color=OKABE["blue"], linewidth=1.8))
# Arrowhead at end pointing UP into stage 2 (clearly below the box bottom)
ax.add_patch(FancyArrowPatch(
    (fb_end_x, fb_y_top + 1.5),
    (fb_end_x, fb_y_top - 1.2),
    arrowstyle="-|>", color=OKABE["blue"],
    linewidth=1.8, mutation_scale=14,
))

# Feedback label — centered below the arc dip, on its OWN line
ax.text((fb_start_x + fb_end_x) / 2, fb_y_dip - 5,
        "Feedback: validation gaps drive surrogate refinement",
        fontsize=9, style="italic", color=OKABE["blue"],
        ha="center", va="center")


# ---------------------------------------------------------------- output line
# Spaced well below feedback label
ax.text(50, 3,
        r"Output: tectonic-state posterior $p(\hat{\theta}\,|\,d)$ with calibrated credible intervals",
        fontsize=10, color="#1A1A1A", ha="center", va="center", weight="bold")


# ---------------------------------------------------------------- save
out_dir = Path(__file__).parent / "figures"
out_base = out_dir / "Fig4_workflow"
plt.savefig(f"{out_base}.png", dpi=600, bbox_inches="tight")
plt.savefig(f"{out_base}.pdf",          bbox_inches="tight")
plt.savefig(f"{out_base}.eps", format="eps", bbox_inches="tight")
# SVG with editable text for Illustrator handoff (svg.fonttype='none' above).
# Open in Illustrator via File > Open. Each text label appears as an
# editable text object on its own layer; boxes / arrows / arcs as
# editable vector paths.
plt.savefig(f"{out_base}.svg", format="svg", bbox_inches="tight")
print(f"Saved: {out_base}.[png|pdf|eps|svg]")
print(f"  → {out_base}.svg is the Illustrator handoff file.")
