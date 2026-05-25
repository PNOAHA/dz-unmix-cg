"""Fig 3 — Schematic of the unified forward model F(θ) (visualizes Eq 6.1).

Shows: tectonic state vector θ = (θ_u, θ_s, θ_r) → F + ε → multi-modal
observations d = (d_zircon, d_flux, d_seq), with a small reverse arrow
indicating the Bayesian inversion direction (Eq 6.4).

Output: Fig3_forward_model.png/pdf/eps at MG full-width (174 mm),
Okabe-Ito colorblind-safe, EPS-safe (no transparency).
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch

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
    "blue":   "#0072B2",
}
OKABE_LIGHT = {
    "orange": "#FCF5E6",
    "sky":    "#EEF8FD",
    "green":  "#E5F5F1",
}

FIG_W_IN, FIG_H_IN = 6.85, 4.6
fig, ax = plt.subplots(figsize=(FIG_W_IN, FIG_H_IN), dpi=300)
ax.set_xlim(0, 100); ax.set_ylim(0, 100)
ax.set_aspect("auto"); ax.axis("off")

LAYER_LEFT, LAYER_RIGHT = 4, 96
LAYER_W = LAYER_RIGHT - LAYER_LEFT


def draw_layer(y, h, color, light_color, header):
    ax.add_patch(patches.Rectangle(
        (LAYER_LEFT, y), LAYER_W, h,
        linewidth=1.2, edgecolor=color, facecolor=light_color,
    ))
    head_h = 4
    ax.add_patch(patches.Rectangle(
        (LAYER_LEFT, y + h - head_h), LAYER_W, head_h,
        linewidth=0, edgecolor="none", facecolor=color,
    ))
    ax.text(LAYER_LEFT + 1, y + h - head_h / 2, header,
            color="white", fontsize=10.5, fontweight="bold",
            va="center", ha="left")


def draw_subbox(x, y, w, h, lines, edge_color, fontsize_lines=None):
    ax.add_patch(patches.Rectangle(
        (x, y), w, h, linewidth=0.7,
        edgecolor=edge_color, facecolor="white",
    ))
    n = len(lines)
    if fontsize_lines is None:
        fontsize_lines = [9.5] + [8.5] * (n - 1)
    cx = x + w / 2
    if n == 1:
        ax.text(cx, y + h / 2, lines[0], ha="center", va="center",
                fontsize=fontsize_lines[0])
        return
    spacing = h * 0.7 / (n - 1)
    y_start = y + h * 0.85
    for i, (line, fs) in enumerate(zip(lines, fontsize_lines)):
        ax.text(cx, y_start - i * spacing, line,
                ha="center", va="center", fontsize=fs)


# ---------------------------------------------------------------- layout
TOP_y, TOP_h = 64, 28     # Tectonic state θ — taller box
BOT_y, BOT_h =  6, 28     # Sedimentary observations d
# The middle ~30 axis units (34→64) hosts the arrow + equation


# ============ TOP: Tectonic state θ ============
draw_layer(TOP_y, TOP_h, OKABE["orange"], OKABE_LIGHT["orange"],
           "  Tectonic state θ   (unknown — to be inferred)")

pad = 2
sub_w = (LAYER_W - 2 * pad - 2 * 2) / 3
sub_h = TOP_h - 4 - 4
sub_y = TOP_y + 2

contents_top = [
    ["Uplift history", r"$\theta_u(x, t)$", "at sources"],
    ["Subsidence history", r"$\theta_s(x, t)$", "at basin sinks"],
    ["Routing field", r"$\theta_r(x, t)$", "source → sink paths"],
]
fontsizes_top = [[10, 10, 8.5]] * 3   # title slightly larger, equation italic-feel

for i, lines in enumerate(contents_top):
    x = LAYER_LEFT + pad + i * (sub_w + 2)
    draw_subbox(x, sub_y, sub_w, sub_h, lines, OKABE["orange"],
                fontsize_lines=fontsizes_top[i])


# ============ MIDDLE: forward arrow + equation ============
# Big down arrow spanning the empty middle ~30 axis units
ARR_TOP = TOP_y - 0.5    # just below top layer
ARR_BOT = BOT_y + BOT_h + 0.5   # just above bottom layer
arrow_x = 35
ax.add_patch(FancyArrowPatch(
    (arrow_x, ARR_TOP), (arrow_x, ARR_BOT),
    arrowstyle="-|>", color="#1A1A1A", linewidth=2.8, mutation_scale=24,
))
mid_y = (ARR_TOP + ARR_BOT) / 2

# Annotate left of arrow: "forward map F"
ax.text(arrow_x - 2, mid_y, "forward\nmap F",
        fontsize=10, va="center", ha="right", style="italic",
        color="#1A1A1A", linespacing=1.3)

# Equation: d = F(θ) + ε      Eq. (6.1)
ax.text(arrow_x + 4, mid_y + 2,
        r"$d = F(\theta) + \varepsilon$",
        fontsize=18, va="center", ha="left", color="#1A1A1A")
ax.text(arrow_x + 4, mid_y - 4,
        "Eq. (6.1)",
        fontsize=10, va="center", ha="left", color="#666666", style="italic")

# Reverse-direction (Bayesian inversion) arrow on far right
inv_x = 80
ax.add_patch(FancyArrowPatch(
    (inv_x, ARR_BOT), (inv_x, ARR_TOP),
    arrowstyle="-|>", color=OKABE["blue"], linewidth=2.4, mutation_scale=20,
))
ax.text(inv_x + 2, mid_y,
        "Bayesian\ninversion\n(Eq. 6.4)",
        fontsize=9, va="center", ha="left", style="italic",
        color=OKABE["blue"], linespacing=1.3)


# ============ BOTTOM: Sedimentary observations d ============
draw_layer(BOT_y, BOT_h, OKABE["green"], OKABE_LIGHT["green"],
           "  Sedimentary observations d   (measured at basins)")

sub_h_b = BOT_h - 4 - 4
sub_y_b = BOT_y + 2

contents_bot = [
    ["Detrital zircon", "U–Pb age density", r"$d_{\mathrm{zircon}}(t)$"],
    ["Sediment flux", "time series", r"$d_{\mathrm{flux}}(t)$"],
    ["Sequence-strat", "boundaries / tracts", r"$d_{\mathrm{seq}}(z)$"],
]

for i, lines in enumerate(contents_bot):
    x = LAYER_LEFT + pad + i * (sub_w + 2)
    draw_subbox(x, sub_y_b, sub_w, sub_h_b, lines, OKABE["green"],
                fontsize_lines=[10, 8.5, 11])


# ---------------------------------------------------------------- save
out_dir = Path(__file__).parent / "figures"
out_base = out_dir / "Fig3_forward_model"
plt.savefig(f"{out_base}.png", dpi=600, bbox_inches="tight")
plt.savefig(f"{out_base}.pdf",          bbox_inches="tight")
plt.savefig(f"{out_base}.eps", format="eps", bbox_inches="tight")
plt.savefig(f"{out_base}.svg", format="svg", bbox_inches="tight")
print(f"Saved: {out_base}.[png|pdf|eps|svg]   (svg = Illustrator handoff)")
