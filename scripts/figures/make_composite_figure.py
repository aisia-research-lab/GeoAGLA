from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# ---------------------------------------------------------------------
# Build the 2x2 composite evidence figure used during M4 integration.
# ---------------------------------------------------------------------

BASE = Path("publication_figures")

files = [
    BASE / "Figure_1_geometry_spectrum.png",
    BASE / "Figure_2_predicted_observed_rates.png",
    BASE / "Figure_3_estimator_maturation.png",
    BASE / "Figure_4_rate_robustness.png",
]

titles = [
    "(a) Geometry \u2192 spectrum",
    "(b) Predicted \u2192 observed rate",
    "(c) Passive edge-estimator maturation",
    "(d) Paired rate vs. basin robustness",
]

fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.4))

for ax, image_file, title in zip(axes.flat, files, titles):
    ax.imshow(mpimg.imread(image_file))
    ax.set_title(title, fontsize=11)
    ax.axis("off")

fig.tight_layout(pad=0.8)

fig.savefig(
    BASE / "Figure_M4_composite_evidence.pdf",
    bbox_inches="tight",
)
fig.savefig(
    BASE / "Figure_M4_composite_evidence.png",
    dpi=400,
    bbox_inches="tight",
)

plt.close(fig)

print("Composite publication figure created.")
