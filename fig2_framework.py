"""
Fig. 2 for the MG manuscript: the three-layer framework.

Output: Fig2_framework.png (600 dpi raster), .pdf (vector),
and .eps (vector, journal-canonical).
Figure size: 174 mm = 6.85 in (MG large-sized full width).
Font: Arial / Helvetica (sans-serif), 8-12 pt (MG spec).
Palette: Okabe-Ito colorblind-safe.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch

# ------------------------------------------------------------------ rc
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.linewidth": 0.5,
    "ps.fonttype": 42,
    "pdf.fonttype": 42,
    # svg.fonttype='none' → text stays as editable <text> SVG elements
    # for Illustrator handoff (校级课题 phase_n technique).
    "svg.fonttype": "none",
})

OKABE = {
    "orange": "#E69F00",
    "sky":    "#56B4E9",
    "green":  "#009E73",
}

# Pre-computed 10%-blend-over-white versions for EPS-safe envelope fills
# (PostScript backend does not support alpha)
OKABE_LIGHT = {
    "orange": "#FCF5E6",
    "sky":    "#EEF8FD",
    "green":  "#E5F5F1",
}

# MG large-sized journal: 174 mm = 6.85 in full text width
FIG_W_IN = 6.85
FIG_H_IN = 5.6

fig, ax = plt.subplots(figsize=(FIG_W_IN, FIG_H_IN), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_aspect("auto")
ax.axis("off")

# ------------------------------------------------------------------ helpers
LAYER_LEFT, LAYER_RIGHT = 4, 96
LAYER_W = LAYER_RIGHT - LAYER_LEFT  # 92


def draw_layer_envelope(y, h, color, light_color, header):
    """Outer rectangle with light fill + saturated header band + title."""
    ax.add_patch(patches.Rectangle(
        (LAYER_LEFT, y), LAYER_W, h,
        linewidth=1.2, edgecolor=color, facecolor=light_color,
    ))
    head_h = 4
    ax.add_patch(patches.Rectangle(
        (LAYER_LEFT, y + h - head_h), LAYER_W, head_h,
        linewidth=0, edgecolor="none", facecolor=color,
    ))
    ax.text(
        LAYER_LEFT + 1, y + h - head_h / 2, header,
        color="white", fontsize=10.5, fontweight="bold",
        va="center", ha="left",
    )


def draw_simple_subbox(x, y, w, h, text, edge_color, fontsize=8.5):
    ax.add_patch(patches.Rectangle(
        (x, y), w, h,
        linewidth=0.7, edgecolor=edge_color, facecolor="white",
    ))
    ax.text(x + w / 2, y + h / 2, text,
            ha="center", va="center", fontsize=fontsize, color="black")


# ------------------------------------------------------------------ layout y
L1_y, L1_h = 4,  20
L2_y, L2_h = 32, 42
L3_y, L3_h = 82, 17

# ============ Layer 1 ============
draw_layer_envelope(
    L1_y, L1_h, OKABE["sky"], OKABE_LIGHT["sky"],
    "  LAYER 1   Standardized, machine-actionable data",
)
l1_pad = 2
l1_inner_w = LAYER_W - 2 * l1_pad
sub_w_l1 = (l1_inner_w - 2 * 2) / 3
sub_h_l1 = L1_h - 4 - 4
sub_y_l1 = L1_y + 2
for i, text in enumerate([
    "Shared facies\nontology\n(Walker, Miall,\nCatuneanu)",
    "Harmonized\nchronostratigraphic\nmapping\n(ICS-anchored)",
    "FAIR metadata\nwith explicit\nuncertainty\ndescriptors",
]):
    x = LAYER_LEFT + l1_pad + i * (sub_w_l1 + 2)
    draw_simple_subbox(x, sub_y_l1, sub_w_l1, sub_h_l1, text, OKABE["sky"])

# ============ Layer 2 ============
draw_layer_envelope(
    L2_y, L2_h, OKABE["green"], OKABE_LIGHT["green"],
    "  LAYER 2   Methods (technical core; Eqs. 6.1 to 6.4)",
)
l2_pad_x = 3
l2_inner_w = LAYER_W - 2 * l2_pad_x
sub_w_l2 = (l2_inner_w - 3) / 2
header_h_l2 = 4
inner_h_l2 = L2_h - header_h_l2 - 2 * 2 - 3
sub_h_l2 = inner_h_l2 / 2

texts_l2 = [
    # top row
    [
        ("Unified forward model",
         r"$d = F(\theta) + \varepsilon$",
         "Eq. (6.1)"),
        ("Joint multi-modal likelihood",
         r"$p(d\,|\,\theta) = \prod_k p(d_k\,|\,\theta)$",
         "Eq. (6.2)"),
    ],
    # bottom row
    [
        ("Physics-informed surrogate",
         r"$\mathcal{L}(\psi) = \|N - F\|^2 + \lambda\,\mathcal{L}_{\mathrm{phys}}$",
         "Eq. (6.3)"),
        ("Uncertainty-aware inversion",
         r"$p(\theta\,|\,d) \propto p(d\,|\,N)\,p(\theta)$",
         "Eq. (6.4)"),
    ],
]
for row_i, row in enumerate(texts_l2):
    # top row visually higher: row_i=0 → upper position
    y = L2_y + 2 + (1 - row_i) * (sub_h_l2 + 3)
    for col_i, (label, math, eq) in enumerate(row):
        x = LAYER_LEFT + l2_pad_x + col_i * (sub_w_l2 + 3)
        ax.add_patch(patches.Rectangle(
            (x, y), sub_w_l2, sub_h_l2,
            linewidth=0.7, edgecolor=OKABE["green"], facecolor="white",
        ))
        cx = x + sub_w_l2 / 2
        ax.text(cx, y + sub_h_l2 * 0.80, label,
                ha="center", va="center", fontsize=9, fontweight="bold")
        ax.text(cx, y + sub_h_l2 * 0.50, math,
                ha="center", va="center", fontsize=10)
        ax.text(cx, y + sub_h_l2 * 0.18, eq,
                ha="center", va="center", fontsize=8, style="italic",
                color="dimgrey")

# ============ Layer 3 ============
draw_layer_envelope(
    L3_y, L3_h, OKABE["orange"], OKABE_LIGHT["orange"],
    "  LAYER 3   Validated case studies",
)
l3_pad = 2
l3_inner_w = LAYER_W - 2 * l3_pad
sub_w_l3 = (l3_inner_w - 2 * 2) / 3
sub_h_l3 = L3_h - 4 - 4
sub_y_l3 = L3_y + 2
for i, text in enumerate([
    "NE Asia\nCretaceous basins\n(Sect. 5.4)",
    "Independent constraints:\nthermochronology, palaeomag,\nseismic reflection",
    "Posterior predictive\nchecks on\nheld-out data",
]):
    x = LAYER_LEFT + l3_pad + i * (sub_w_l3 + 2)
    draw_simple_subbox(x, sub_y_l3, sub_w_l3, sub_h_l3, text, OKABE["orange"])

# ============ Arrows ============
def up_arrow(x, y_start, y_end, label, color="black"):
    ax.add_patch(FancyArrowPatch(
        (x, y_start), (x, y_end),
        arrowstyle="-|>", color=color,
        linewidth=1.2, mutation_scale=12,
    ))
    ax.text(x + 1.5, (y_start + y_end) / 2, label,
            fontsize=8.5, color=color,
            va="center", ha="left", style="italic")


def down_arrow(x, y_start, y_end, label, color="dimgrey"):
    ax.add_patch(FancyArrowPatch(
        (x, y_start), (x, y_end),
        arrowstyle="-|>", color=color,
        linewidth=1.2, mutation_scale=12,
    ))
    ax.text(x - 1.5, (y_start + y_end) / 2, label,
            fontsize=8.5, color=color,
            va="center", ha="right", style="italic")


# L1 -> L2 (left, up): data flows into methods
up_arrow(14, L1_y + L1_h + 0.3, L2_y - 0.3, "data")
# L2 -> L1 (right, down): methods impose requirements on data
down_arrow(86, L2_y - 0.3, L1_y + L1_h + 0.3, "requires standards")

# L2 -> L3 (left, up): methods produce inferences for validation
up_arrow(14, L2_y + L2_h + 0.3, L3_y - 0.3, "inferences")
# L3 -> L2 (right, down): validation exposes gaps in methods
down_arrow(86, L3_y - 0.3, L2_y + L2_h + 0.3, "exposes gaps")

# ------------------------------------------------------------------ save
out_dir = Path(__file__).parent / "figures"
out_base = out_dir / "Fig2_framework"
plt.savefig(f"{out_base}.png", dpi=600, bbox_inches="tight")
plt.savefig(f"{out_base}.pdf",          bbox_inches="tight")
plt.savefig(f"{out_base}.eps", format="eps", bbox_inches="tight")
plt.savefig(f"{out_base}.svg", format="svg", bbox_inches="tight")
print(f"Saved: {out_base}.[png|pdf|eps|svg]   (svg = Illustrator handoff)")
