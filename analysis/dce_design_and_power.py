"""Discrete choice experiment (DCE) for a probiotic tomato drink: design + sample-size check.

What this does
1. Builds a blocked choice design: 3 blocks x 8 tasks; each task = 2 product profiles + "neither".
2. Simulates respondents from ASSUMED preferences (planning values, not data) and re-estimates a
   multinomial (conditional) logit, to check that the design identifies the parameters and to see
   how precisely willingness to pay (WTP) is estimated at different sample sizes.

Nothing here is a result about consumers: the real parameters come from the survey.

Run:  python analysis/dce_design_and_power.py
"""
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
rng = np.random.default_rng(2026)

# ---- attributes and levels (to be calibrated with store checks and the lab) --------------
PRICES = [1.50, 2.00, 2.50, 3.00]   # EUR per 250 ml bottle
ORIGINS = ["not stated", "Italian tomato", "Campanian tomato"]
COLS = ["price", "probiotic", "italian", "campanian", "organic", "no_added_salt"]
prof = []
for price, probio, origin, organic, nosalt in product(PRICES, [0, 1], range(3), [0, 1], [0, 1]):
    prof.append([price, probio, int(origin == 1), int(origin == 2), organic, nosalt])
P = np.array(prof, dtype=float)                    # 96 profiles x 6 coded attributes
LEVEL_KEYS = np.c_[P[:, 0], P[:, 1], P[:, 2] + 2 * P[:, 3], P[:, 4], P[:, 5]]   # one column per attribute


def build_design(n_blocks=3, tasks=8, tries=3000):
    """Random pairs: different prices, >= 3 attributes differ, no dominated alternative.
    Keeps the draw with the best level balance across the whole design."""
    need = n_blocks * tasks
    best, best_score = None, np.inf
    for _ in range(tries):
        a, b = rng.integers(0, len(P), size=(2, 400))
        ka, kb = LEVEL_KEYS[a], LEVEL_KEYS[b]
        differs = (ka != kb).sum(1)
        qa, qb = P[a][:, 1:], P[b][:, 1:]
        dom_a = (qa >= qb).all(1) & (P[a, 0] <= P[b, 0])
        dom_b = (qb >= qa).all(1) & (P[b, 0] <= P[a, 0])
        ok = (P[a, 0] != P[b, 0]) & (differs >= 3) & ~dom_a & ~dom_b
        idx = np.flatnonzero(ok)[:need]
        if len(idx) < need:
            continue
        pairs = np.c_[a[idx], b[idx]]
        keys = LEVEL_KEYS[pairs.ravel()]
        score = 0.0
        for j in range(keys.shape[1]):
            _, counts = np.unique(keys[:, j], return_counts=True)
            score += (counts / counts.sum()).std()
        if score < best_score:
            best, best_score = pairs, score
    return best.reshape(n_blocks, tasks, 2)


design_idx = build_design()                                   # (block, task, alt) -> profile index
rows = []
for bl in range(design_idx.shape[0]):
    for t in range(design_idx.shape[1]):
        for alt in range(2):
            p = P[design_idx[bl, t, alt]]
            rows.append({"block": bl + 1, "task": t + 1, "alt": alt + 1, "price_eur": p[0],
                         "probiotic": int(p[1]), "origin": ORIGINS[int(p[2] + 2 * p[3])],
                         "organic": int(p[4]), "no_added_salt": int(p[5])})
pd.DataFrame(rows).to_csv(ROOT / "analysis" / "dce_design.csv", index=False)

# X for each block/task/alternative: [asc_product, price, probiotic, italian, campanian, organic, no_salt]
K = 1 + len(COLS)
XB = np.zeros((design_idx.shape[0], design_idx.shape[1], 3, K))
XB[:, :, :2, 0] = 1.0
XB[:, :, :2, 1:] = P[design_idx]
NAMES = ["asc_product"] + COLS

# ---- assumed preferences for the simulation (planning values) ----------------------------
TRUE = np.array([2.2, -1.2, 0.7, 0.4, 0.6, 0.3, 0.35])
WTP_ATTR = ["probiotic", "italian", "campanian", "organic", "no_added_salt"]
TRUE_WTP = {k: TRUE[NAMES.index(k)] / -TRUE[1] for k in WTP_ATTR}


def simulate(n_resp):
    blocks = np.arange(n_resp) % XB.shape[0]
    X = XB[blocks].reshape(-1, 3, K)                         # (n_resp*tasks, 3, K)
    U = X @ TRUE + rng.gumbel(size=X.shape[:2])
    return X, U.argmax(1)


def mnl_fit(X, y):
    def nll(b):
        V = X @ b
        V -= V.max(1, keepdims=True)
        logp = V - np.log(np.exp(V).sum(1, keepdims=True))
        Pr = np.exp(logp)
        ll = logp[np.arange(len(y)), y].sum()
        grad = (X[np.arange(len(y)), y] - (Pr[..., None] * X).sum(1)).sum(0)
        return -ll, -grad
    r = minimize(nll, np.zeros(X.shape[2]), jac=True, method="BFGS")
    return r.x


SIZES, REPS = [150, 300, 500], 300
records, none_shares = [], []
for n in SIZES:
    for _ in range(REPS):
        X, y = simulate(n)
        none_shares.append((y == 2).mean())
        b = mnl_fit(X, y)
        records.append({"n": n, **{k: b[NAMES.index(k)] / -b[1] for k in WTP_ATTR}})
sim = pd.DataFrame(records)

summary = []
for n, g in sim.groupby("n"):
    for k in WTP_ATTR:
        lo, hi = np.percentile(g[k], [2.5, 97.5])
        summary.append({"n_respondents": n, "attribute": k, "assumed_wtp": TRUE_WTP[k], "mean_estimate": g[k].mean(),
                        "p2_5": lo, "p97_5": hi, "half_width": (hi - lo) / 2})
summary = pd.DataFrame(summary)
summary.round(3).to_csv(ROOT / "analysis" / "dce_power_summary.csv", index=False)
print("Average share choosing 'neither':", round(float(np.mean(none_shares)), 3))
print(summary.round(3).to_string(index=False))

# ---- figure: precision of WTP for the probiotic claim by sample size ---------------------
SURFACE, INK, INK2, MUTED, GRID, BASE, BLUE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#2a78d6"
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 10, "figure.facecolor": SURFACE,
                     "axes.facecolor": SURFACE, "axes.edgecolor": BASE, "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": INK2})
s = summary[summary.attribute == "probiotic"].reset_index(drop=True)
fig, ax = plt.subplots(figsize=(8, 4.4))
fig.subplots_adjust(top=0.78, bottom=0.2, left=0.11, right=0.95)
ax.axhline(TRUE_WTP["probiotic"], color=BASE, linewidth=1, linestyle="--")
ax.errorbar(range(len(s)), s.mean_estimate, yerr=[s.mean_estimate - s.p2_5, s.p97_5 - s.mean_estimate],
            fmt="o", color=BLUE, ecolor=BLUE, elinewidth=2, capsize=0, markersize=8)
for i, r in s.iterrows():
    ax.text(i + 0.07, r.mean_estimate, f"± EUR {r.half_width:.2f}", va="center", fontsize=9, color=INK2,
            bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))
ax.set_xticks(range(len(s)), [f"{n} respondents" for n in s.n_respondents])
ax.set_xlim(-0.5, len(s) - 0.4)
ax.set_ylabel("WTP for 'live probiotic cultures',\nEUR per 250 ml bottle")
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.tick_params(length=0)
fig.text(0.02, 0.965, "Design check: how precisely the survey would measure the probiotic premium",
         fontsize=12.5, fontweight="bold", va="top")
fig.text(0.02, 0.905, f"Simulated choices from assumed preferences · {REPS} replications per sample size · 8 tasks per respondent · multinomial logit",
         fontsize=9, color=INK2, va="top")
fig.text(0.02, 0.02, f"Bars: 95% range of the WTP estimates across replications. Dashed line: assumed true WTP (EUR {TRUE_WTP['probiotic']:.2f}).\nPlanning exercise on simulated data, not a result about consumers.",
         fontsize=8, color=MUTED, va="bottom")
fig.savefig(FIG / "fig4_dce_power_check.png", dpi=200)
print("figure written")
