"""Refresh the Eurostat Comext extracts used in this repository.

Dataset DS-045409 (EU trade since 1988 by HS2-4-6 and CN8), product 200950 (tomato juice).
Rewrites the three CSV files in ../data with the same columns the analysis reads. If Eurostat has
not revised the figures, the files come out unchanged. Requires internet access and `requests`.

Run:  python analysis/fetch_eurostat.py
"""
import re
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
API = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"
EU27 = ["AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE", "IT",
        "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"]
IND = [("indicators", "VALUE_IN_EUROS"), ("indicators", "QUANTITY_IN_100KG")]
AGGREGATES = ["INT_EU27_2020", "EXT_EU27_2020", "WORLD"]      # partner totals kept, in this order
SHORT_LABELS = {"KR": "South Korea", "RU": "Russia", "WORLD": "All countries"}


def get(params):
    """Download one JSON-stat query. Returns (long DataFrame with one row per cell, partner labels)."""
    r = requests.get(API, params=[("format", "JSON"), ("lang", "EN"), ("freq", "A"), ("product", "200950")] + params,
                     timeout=120)
    r.raise_for_status()
    js = r.json()
    ids, size = js["id"], js["size"]
    cats = [sorted(js["dimension"][d]["category"]["index"], key=js["dimension"][d]["category"]["index"].get) for d in ids]
    values = js["value"]
    cells = values.items() if isinstance(values, dict) else enumerate(values)
    rows = []
    for k, v in cells:
        if v is None:
            continue
        n, rec = int(k), {}
        for i in range(len(ids) - 1, -1, -1):          # the cell number is a mixed-radix index over the dimensions
            rec[ids[i]] = cats[i][n % size[i]]
            n //= size[i]
        rec["v"] = v
        rows.append(rec)
    labels = js["dimension"].get("partner", {}).get("category", {}).get("label", {})
    return pd.DataFrame(rows), labels


def wide(df, keys):
    """One row per key combination, with value_eur and qty_100kg as columns."""
    out = df.pivot_table(index=keys, columns="indicators", values="v", aggfunc="first").reset_index()
    out = out.rename(columns={"VALUE_IN_EUROS": "value_eur", "QUANTITY_IN_100KG": "qty_100kg", "time": "year"})
    out["year"] = out["year"].astype(int)
    if "flow" in out:
        out["flow"] = out["flow"].astype(int)
    return out[[c if c != "time" else "year" for c in keys] + ["value_eur", "qty_100kg"]]


def short_label(code, label):
    """'Germany (incl. German Democratic Republic ...)' -> 'Germany'."""
    return SHORT_LABELS.get(code, re.sub(r"\s*\(.*$", "", label).strip())


def num(x):
    """Write 70677.0 as 70677 and 1127.20 as 1127.2, as in the Eurostat output."""
    return "" if pd.isna(x) else f"{x:.2f}".rstrip("0").rstrip(".")


def save(df, name):
    df = df.copy()
    for c in ("value_eur", "qty_100kg"):
        df[c] = df[c].map(num)
    df.to_csv(DATA / name, index=False, lineterminator="\n")


def main():
    years = [("time", "2024"), ("time", "2025")]

    # 1) EU member states, trade with all partners, imports (flow 1) and exports (flow 2)
    a, _ = get([("reporter", c) for c in EU27] + [("partner", "WORLD"), ("flow", "1"), ("flow", "2")] + IND + years)
    save(wide(a, ["reporter", "flow", "time"]).sort_values(["reporter", "flow", "year"]),
         "eu_member_states_tomato_juice_trade.csv")

    # 2) Italy's exports by partner country, plus the intra-EU, extra-EU and world totals
    b, labels = get([("reporter", "IT"), ("flow", "2")] + IND + years)
    b = wide(b, ["partner", "time"])
    b = b[(b.value_eur > 0) & (b.partner.str.fullmatch("[A-Z]{2}") | b.partner.isin(AGGREGATES))].copy()
    b.insert(1, "partner_label", [short_label(c, labels.get(c, c)) for c in b.partner])
    b["rank"] = [AGGREGATES.index(c) + 1 if c in AGGREGATES else 0 for c in b.partner]
    b = b.sort_values(["rank", "partner", "year"]).drop(columns="rank")
    for year, g in b.groupby("year"):                  # the countries must add up to the world total
        countries = g[g.partner.str.len() == 2].value_eur.sum()
        world = g[g.partner == "WORLD"].value_eur.sum()
        if abs(countries - world) > 1:
            print(f"warning: {year} partner countries sum to {countries:,.0f}, world total is {world:,.0f}")
    save(b, "italy_tomato_juice_exports_by_partner.csv")

    # 3) Italy's imports and exports with all partners, 2010-2025
    c, _ = get([("reporter", "IT"), ("partner", "WORLD"), ("flow", "1"), ("flow", "2")] + IND
               + [("time", str(y)) for y in range(2010, 2026)])
    save(wide(c, ["flow", "time"]).sort_values(["flow", "year"]), "italy_tomato_juice_trade_2010_2025.csv")
    print("Eurostat extracts refreshed in", DATA)


if __name__ == "__main__":
    main()
