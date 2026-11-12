"""Trade evidence for a probiotic tomato-based drink.

Reads the Eurostat Comext extracts in ../data (product CN/HS 200950, tomato juice),
computes the indicators quoted in the README and draws the three figures in ../figures.

Run:  python analysis/trade_analysis.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA, FIG = ROOT / "data", ROOT / "figures"
FIG.mkdir(exist_ok=True)

# ---- chart style (validated categorical slots; recessive chrome) -------------------
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASE = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, OTHER = "#2a78d6", "#eb6834", "#1baf7a", "#c9c7bf"
plt.rcParams.update({
    "font.family": ["Inter", "DejaVu Sans"], "font.size": 10,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": BASE, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlesize": 12,
})


def tidy(ax, grid_axis="y"):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def title(fig, main, sub):
    fig.text(0.02, 0.965, main, fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 0.905, sub, fontsize=9.5, color=INK2, va="top")


def source(fig, text):
    fig.text(0.02, 0.02, text, fontsize=8, color=MUTED, va="bottom")


SRC = "Source: Eurostat Comext DS-045409, product 200950 (tomato juice, unfermented); extracted 8 Nov 2026."

# ---- data ---------------------------------------------------------------------------
ts = pd.read_csv(DATA / "italy_tomato_juice_trade_2010_2025.csv")
ts["tonnes"] = ts["qty_100kg"] / 10
exp = ts[ts.flow == 2].set_index("year")
imp = ts[ts.flow == 1].set_index("year")
exp["unit_value_eur_kg"] = exp["value_eur"] / (exp["qty_100kg"] * 100)

partners = pd.read_csv(DATA / "italy_tomato_juice_exports_by_partner.csv")
eu = pd.read_csv(DATA / "eu_member_states_tomato_juice_trade.csv")

# ---- indicators quoted in the README ----------------------------------------------
y0, y1 = 2010, 2025
ind = {
    "IT exports 2025, EUR m": exp.loc[y1, "value_eur"] / 1e6,
    "IT exports 2010, EUR m": exp.loc[y0, "value_eur"] / 1e6,
    "IT exports 2025, tonnes": exp.loc[y1, "tonnes"],
    "IT exports 2010, tonnes": exp.loc[y0, "tonnes"],
    "Value index 2025 (2010=100)": 100 * exp.loc[y1, "value_eur"] / exp.loc[y0, "value_eur"],
    "Volume index 2025 (2010=100)": 100 * exp.loc[y1, "tonnes"] / exp.loc[y0, "tonnes"],
    "Unit value 2010, EUR/kg": exp.loc[y0, "unit_value_eur_kg"],
    "Unit value 2025, EUR/kg": exp.loc[y1, "unit_value_eur_kg"],
    "IT exports growth 2024->2025, %": 100 * (exp.loc[2025, "value_eur"] / exp.loc[2024, "value_eur"] - 1),
    "IT imports 2025, EUR m": imp.loc[y1, "value_eur"] / 1e6,
}

p25 = partners[(partners.year == 2025) & (partners.partner.str.len() == 2)].copy()
world25 = partners.query("partner == 'WORLD' and year == 2025").value_eur.item()
p25["share_pct"] = 100 * p25.value_eur / world25
p25["unit_value_eur_kg"] = p25.value_eur / (p25.qty_100kg * 100)
p25 = p25.sort_values("value_eur", ascending=False)
extra25 = partners.query("partner == 'EXT_EU27_2020' and year == 2025").value_eur.item()
ind["Share of exports to Germany 2025, %"] = p25.set_index("partner").loc["DE", "share_pct"]
ind["Share of exports outside the EU 2025, %"] = 100 * extra25 / world25

e25 = eu[eu.year == 2025]
exporters = e25[e25.flow == 2].sort_values("value_eur", ascending=False)
importers = e25[e25.flow == 1].sort_values("value_eur", ascending=False)
ind["EU27 exports 2025 (sum of member states), EUR m"] = exporters.value_eur.sum() / 1e6
ind["Italy rank among EU exporters 2025"] = int(exporters.reporter.tolist().index("IT") + 1)
ind["Italy share of EU member-state exports 2025, %"] = 100 * exporters.set_index("reporter").loc["IT", "value_eur"] / exporters.value_eur.sum()
ind["Germany reported imports 2025, EUR m"] = importers.set_index("reporter").loc["DE", "value_eur"] / 1e6

lines = ["| Indicator | Value |", "| --- | --- |"]
for k, v in ind.items():
    lines.append(f"| {k} | {v:,.2f} |" if isinstance(v, float) else f"| {k} | {v} |")
lines += ["", "Top destinations of Italian tomato-juice exports, 2025", "",
          "| Partner | EUR m | Share % | EUR/kg |", "| --- | --- | --- | --- |"]
for _, r in p25.head(8).iterrows():
    lines.append(f"| {r.partner_label} | {r.value_eur/1e6:.2f} | {r.share_pct:.1f} | {r.unit_value_eur_kg:.2f} |")
(ROOT / "analysis" / "indicators.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))

# ---- Figure 1: indexed value / volume / unit value ---------------------------------
idx = pd.DataFrame({
    "Value (EUR)": 100 * exp.value_eur / exp.loc[y0, "value_eur"],
    "Volume (tonnes)": 100 * exp.tonnes / exp.loc[y0, "tonnes"],
    "Unit value (EUR/kg)": 100 * exp.unit_value_eur_kg / exp.loc[y0, "unit_value_eur_kg"],
})
fig, ax = plt.subplots(figsize=(8, 4.6))
fig.subplots_adjust(top=0.80, bottom=0.14, left=0.08, right=0.80)
for col, colr in zip(idx.columns, (BLUE, ORANGE, AQUA)):
    ax.plot(idx.index, idx[col], color=colr, linewidth=2, label=col)
    ax.annotate(f"{col}  {idx[col].iloc[-1]:.0f}", (idx.index[-1], idx[col].iloc[-1]),
                xytext=(8, 0), textcoords="offset points", va="center", fontsize=9, color=INK2)
ax.axhline(100, color=BASE, linewidth=1)
ax.set_xlim(y0, y1)
ax.set_ylabel("Index, 2010 = 100")
ax.set_xticks(range(2010, 2026, 3))
tidy(ax)
ax.legend(frameon=False, loc="upper left", fontsize=9)
title(fig, "Italy's tomato-juice exports: value up almost 3x since 2010, volume flat",
      f"Exports EUR {ind['IT exports 2010, EUR m']:.1f} m -> EUR {ind['IT exports 2025, EUR m']:.1f} m; "
      f"unit value EUR {ind['Unit value 2010, EUR/kg']:.2f} -> {ind['Unit value 2025, EUR/kg']:.2f} per kg")
source(fig, SRC)
fig.savefig(FIG / "fig1_italy_exports_index.png", dpi=200)
plt.close(fig)

# ---- Figure 2: destinations 2025 ----------------------------------------------------
top = p25.head(8).iloc[::-1]
fig, ax = plt.subplots(figsize=(8, 4.6))
fig.subplots_adjust(top=0.80, bottom=0.19, left=0.20, right=0.95)
bars = ax.barh(top.partner_label, top.value_eur / 1e6, color=BLUE, height=0.62)
for b, (_, r) in zip(bars, top.iterrows()):
    ax.text(b.get_width() + 0.12, b.get_y() + b.get_height() / 2,
            f"EUR {r.value_eur/1e6:.2f} m · {r.share_pct:.1f}% · EUR {r.unit_value_eur_kg:.2f}/kg",
            va="center", fontsize=8.5, color=INK2)
ax.set_xlim(0, 14)
ax.set_xlabel("Export value, EUR million (2025)")
tidy(ax, "x")
ax.tick_params(axis="y", labelcolor=INK)
title(fig, "Seven in ten euros of Italy's tomato-juice exports go to Germany",
      f"Top destinations, 2025 (total EUR {world25/1e6:.1f} m). Labels: value · share · unit value")
source(fig, SRC)
fig.savefig(FIG / "fig2_italy_export_destinations_2025.png", dpi=200)
plt.close(fig)

# ---- Figure 3: EU exporters vs importers 2025 ----------------------------------------
names = {"ES": "Spain", "IT": "Italy", "PL": "Poland", "DE": "Germany", "NL": "Netherlands", "CY": "Cyprus",
         "FR": "France", "LV": "Latvia", "AT": "Austria", "BE": "Belgium", "LT": "Lithuania", "CZ": "Czechia",
         "RO": "Romania", "EE": "Estonia"}
fig, axes = plt.subplots(1, 2, figsize=(9, 4.6), sharex=False)
fig.subplots_adjust(top=0.78, bottom=0.17, left=0.12, right=0.97, wspace=0.55)
for ax, df, lab, hl in ((axes[0], exporters, "Exports", "IT"), (axes[1], importers, "Imports", None)):
    d = df.head(8).iloc[::-1]
    cols = [BLUE if r == hl else OTHER for r in d.reporter]
    bars = ax.barh([names.get(r, r) for r in d.reporter], d.value_eur / 1e6, color=cols, height=0.62)
    for b, v in zip(bars, d.value_eur / 1e6):
        ax.text(b.get_width() + 0.3, b.get_y() + b.get_height() / 2, f"{v:.1f}", va="center", fontsize=8.5, color=INK2)
    ax.set_title(f"{lab}, EUR million", loc="left", fontsize=10, color=INK2)
    ax.set_xlim(0, df.value_eur.max() / 1e6 * 1.18)
    tidy(ax, "x")
    ax.tick_params(axis="y", labelcolor=INK)
title(fig, "Spain and Italy supply Europe's tomato juice; Germany is the largest buyer",
      "EU member states' trade in tomato juice with all partners, 2025 (top 8 each)")
source(fig, SRC + "\nMirror flows differ: Germany reports EUR 6.4 m imports from all partners, while Italy reports EUR 10.0 m exports to Germany.")
fig.savefig(FIG / "fig3_eu_exporters_importers_2025.png", dpi=200)
plt.close(fig)
print("figures written to", FIG)
