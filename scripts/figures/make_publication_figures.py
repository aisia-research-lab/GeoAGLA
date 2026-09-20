from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shutil

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
# Adjust these three input paths if your local folder structure differs.
GEOMETRY_CSV = Path("real_audio_audit/geometry_results.csv")
RATE_CSV = Path("real_audio_audit/rate_results.csv")
C1_CSV = Path("C1_capture_ratio_audit.csv")

# Frozen Student-B estimator-maturation figure generated from the audited
# Student-B package. This script copies it as Figure 3 rather than regenerating
# it from a potentially different ledger.
ONLINE_EVALUATOR_ESTIMATOR_FIG = Path(
    "Online Evaluator_Final_Freeze_Candidate_v1/figures/"
    "Figure_B1_estimator_maturation_traces.png"
)

OUT = Path("publication_figures")
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# Load frozen ledgers
# ---------------------------------------------------------------------
geom = pd.read_csv(GEOMETRY_CSV)
rate = pd.read_csv(RATE_CSV)
c1 = pd.read_csv(C1_CSV)

# ---------------------------------------------------------------------
# Figure 1 — Geometry-spectrum correspondence
# ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.8, 5.0))

x = geom["cos_theta_sq"].to_numpy()
y = geom["lambda_plus"].to_numpy()

ax.scatter(x, y, s=22, alpha=0.7)

lo = min(x.min(), y.min())
hi = max(x.max(), y.max())
ax.plot(
    [lo, hi], [lo, hi],
    linestyle="--",
    linewidth=1.4,
    label="identity",
)

ax.set_xlabel(r"Principal-angle prediction $\cos^2\theta$")
ax.set_ylabel(r"Direct Jacobian edge $\lambda_+$")
ax.set_title("Geometry predicts the local spectral edge")
ax.legend(frameon=False)
ax.grid(alpha=0.2)

fig.tight_layout()
fig.savefig(OUT / "Figure_1_geometry_spectrum.pdf", bbox_inches="tight")
fig.savefig(
    OUT / "Figure_1_geometry_spectrum.png",
    dpi=400,
    bbox_inches="tight",
)
plt.close(fig)

# ---------------------------------------------------------------------
# Figure 2 — Predicted versus observed local contraction factors
# ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.8, 5.0))

series = [
    ("q_gla_pred",    "q_gla_obs",    "GLA",             "o"),
    ("q_fgla_pred",   "q_fgla_obs",   "FGLA",            "s"),
    ("q_oracle_pred", "q_oracle_obs", "Geometry Oracle", "^"),
]

for pred_col, obs_col, label, marker in series:
    ax.scatter(
        rate[pred_col],
        rate[obs_col],
        s=24,
        alpha=0.65,
        label=label,
        marker=marker,
    )

all_cols = [
    "q_gla_pred", "q_fgla_pred", "q_oracle_pred",
    "q_gla_obs", "q_fgla_obs", "q_oracle_obs",
]
lo = min(rate[all_cols].min())
hi = max(rate[all_cols].max())

ax.plot(
    [lo, hi], [lo, hi],
    linestyle="--",
    linewidth=1.4,
    label="identity",
)

ax.set_xlabel("Predicted local contraction factor")
ax.set_ylabel("Observed fitted contraction factor")
ax.set_title("Geometry-designed rates track observed local dynamics")
ax.legend(frameon=False)
ax.grid(alpha=0.2)

fig.tight_layout()
fig.savefig(
    OUT / "Figure_2_predicted_observed_rates.pdf",
    bbox_inches="tight",
)
fig.savefig(
    OUT / "Figure_2_predicted_observed_rates.png",
    dpi=400,
    bbox_inches="tight",
)
plt.close(fig)

# ---------------------------------------------------------------------
# Figure 3 — Passive edge-estimator maturation
# ---------------------------------------------------------------------
# The manuscript version used the frozen Student-B audit figure directly.
# This preserves the exact audited trajectory display.
shutil.copy2(
    ONLINE_EVALUATOR_ESTIMATOR_FIG,
    OUT / "Figure_3_estimator_maturation.png",
)
from PIL import Image
with Image.open(OUT / "Figure_3_estimator_maturation.png") as _img:
    _img.convert("RGB").save(OUT / "Figure_3_estimator_maturation.pdf", "PDF", resolution=400.0)

# ---------------------------------------------------------------------
# Figure 4 — Paired-rate behavior versus basin robustness
# ---------------------------------------------------------------------
# Canonical C1 ledger: 15 cases at each H in {60,120,180,360}.
# Win = fitted q_online < fitted q_fgla.
win = (
    c1.groupby("horizon")
      .apply(
          lambda d: 100.0 * np.mean(d["q_online"] < d["q_fgla"]),
          include_groups=False,
      )
)

labels = [
    "Rate win\nH=60",
    "Rate win\nH=120",
    "Rate win\nH=180",
    "Rate win\nH=360",
    "Basin success\nOnline",
    "Basin success\nFGLA",
]

vals = [
    win.loc[60],
    win.loc[120],
    win.loc[180],
    win.loc[360],
    74.94,   # frozen Student-B basin result
    54.87,   # frozen Student-B FGLA basin result
]

fig, ax = plt.subplots(figsize=(8.0, 4.8))

bars = ax.bar(np.arange(len(vals)), vals)
ax.axhline(50, linestyle="--", linewidth=1.2)

ax.set_xticks(np.arange(len(vals)), labels)
ax.set_ylabel("Percentage (%)")
ax.set_ylim(0, 100)
ax.set_title(
    "Online adaptation: paired-rate behavior versus empirical robustness"
)
ax.grid(axis="y", alpha=0.2)

for i, (bar, value) in enumerate(zip(bars, vals)):
    # Shift H=120 text up slightly so it does not collide with the dashed horizontal line at 50%
    y_offset = 5.2 if i == 1 else 2.0
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + y_offset,
        f"{value:.1f}%",
        ha="center",
        va="bottom",
        fontsize=9,
    )

fig.tight_layout()
fig.savefig(
    OUT / "Figure_4_rate_robustness.pdf",
    bbox_inches="tight",
)
fig.savefig(
    OUT / "Figure_4_rate_robustness.png",
    dpi=400,
    bbox_inches="tight",
)
plt.close(fig)

print(f"Publication figures written to: {OUT.resolve()}")
