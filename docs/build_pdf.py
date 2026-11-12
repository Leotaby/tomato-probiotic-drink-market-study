"""Build docs/market_study_plan.pdf (plan + two pages of figures) from the figures. Needs Playwright + Chromium."""
import base64
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def img(name):
    return "data:image/png;base64," + base64.b64encode((ROOT / "figures" / name).read_bytes()).decode()


HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 14mm 15mm 13mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: Inter, 'DejaVu Sans', sans-serif; color: #1b1f24; font-size: 8.9pt; line-height: 1.38; margin: 0; }}
h1 {{ font-size: 16.5pt; margin: 0; color: #0b0b0b; letter-spacing: -0.01em; }}
.by {{ color: #52514e; font-size: 8.4pt; margin: 3pt 0 8pt; }}
.by a {{ color: #1c5cab; text-decoration: none; }}
sup {{ font-size: 0.7em; line-height: 0; }}
.lead {{ font-size: 9.8pt; margin: 0 0 9pt; padding: 7pt 9pt; background: #f2f6fc; border-left: 2.5pt solid #2a78d6; }}
h2 {{ font-size: 8.4pt; text-transform: uppercase; letter-spacing: .14em; color: #1c5cab; margin: 10pt 0 4pt;
      padding-bottom: 2pt; border-bottom: 0.6pt solid #d9dee6; }}
ol, ul {{ margin: 0; padding-left: 13pt; }} li {{ margin-bottom: 2pt; }}
table {{ width: 100%; border-collapse: collapse; font-size: 8.4pt; }}
th {{ text-align: left; color: #52514e; font-weight: 600; border-bottom: 0.8pt solid #c3c2b7; padding: 3pt 4pt; }}
td {{ border-bottom: 0.5pt solid #e1e0d9; padding: 3pt 4pt; vertical-align: top; }}
td.m {{ white-space: nowrap; color: #1c5cab; font-weight: 600; width: 13mm; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 9mm; }}
.note {{ color: #6b6a66; font-size: 7.6pt; margin-top: 5pt; }}
.page2 {{ break-before: page; }}
.fig {{ width: 100%; margin: 2pt 0 6pt; }}
.figrow {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; }}
</style></head><body>
<h1>Market study plan: a probiotic tomato-based drink</h1>
<div class="by">Hatef Tabbakhian · November 2026 · public data only · code and data:
<a href="https://github.com/Leotaby/tomato-probiotic-drink-market-study">github.com/Leotaby/tomato-probiotic-drink-market-study</a></div>
<p class="lead">A probiotic tomato drink can start where tomato juice is already a habit: <b>Germany buys 70% of Italy's
tomato-juice exports</b>. It can also try to build a new wellness category in Italy. The study tests both routes
and prices the probiotic claim with a choice experiment.</p>

<div class="two"><div>
<h2>Questions the study answers</h2>
<ol>
<li><b>Where</b> is the demand: Italy, or export markets with a tomato-juice habit?</li>
<li><b>Who</b> buys: which segments, how many?</li>
<li><b>What</b> sells it: probiotic claim, origin, organic, salt, and the premium people accept.</li>
<li><b>How much:</b> realistic volumes and revenues, under explicit scenarios.</li>
</ol>
<h2>What public data already shows</h2>
<ul>
<li>Italy's tomato-juice exports: <b>EUR 4.8 m (2010) → EUR 14.2 m (2025)</b>, volume nearly flat
(12.4 → 13.3 thousand t). Value per kg EUR 0.39 → 1.06: partly up-market, partly raw-material costs
(tomato prices +50% in four years, ANICAV).</li>
<li><b>Germany 70.5%</b> of Italy's exports, South Korea 11.3%, France 8.7%; only 16.5% leaves the EU.</li>
<li>Italy is the <b>EU's second exporter</b> (24%, after Spain); Germany is the largest importer; Italy imports almost none.</li>
<li>Italy processed <b>5.8 m t</b> of tomatoes in 2025, second in the world (ANICAV).</li>
<li>Plant-based probiotic juices kept <b>&gt; 6 log CFU/mL for 33 days</b> refrigerated, liked 6.9–8.9/9 (Condurso et al., 2025): chilled distribution.</li>
<li>Label: Italy allows "probiotico" if a daily serving has at least 10<sup>9</sup> live cells (6.6 log CFU/mL in a
250 ml bottle); no EU health claim is authorised, so test only usable wording.</li>
</ul>
</div><div>
<h2>Seven-month plan</h2>
<table>
<tr><th>Month</th><th>Work → output</th></tr>
<tr><td class="m">1</td><td>Desk research, price checks in Italy and Germany, top-down sizing → price map</td></tr>
<tr><td class="m">2</td><td>Survey and choice-experiment design with the lab and producers; pilot (n ≈ 30)</td></tr>
<tr><td class="m">3–4</td><td>Online panel: Italy n = 500, Germany n = 300; tasting session with the prototype (n = 60–80)</td></tr>
<tr><td class="m">5</td><td>Choice models, purchase intention, segments, sensory analysis → WTP per attribute</td></tr>
<tr><td class="m">6</td><td>Bottom-up market model with Monte Carlo ranges, by country and channel</td></tr>
<tr><td class="m">7</td><td>Report and presentation to the producers; draft paper</td></tr>
</table>
<h2>Choice experiment</h2>
<table>
<tr><th>Attribute</th><th>Levels</th></tr>
<tr><td>Price, 250 ml</td><td>EUR 1.50 · 2.00 · 2.50 · 3.00</td></tr>
<tr><td>Probiotic</td><td>none · "with live probiotic cultures"</td></tr>
<tr><td>Origin</td><td>not stated · Italian · Campanian tomato</td></tr>
<tr><td>Organic · Salt</td><td>no / yes · standard / no added salt</td></tr>
</table>
<p style="margin:5pt 0 0">8 tasks × (2 products + "neither"), 3 blocks. <b>Models:</b> multinomial logit → mixed logit and latent class;
WTP = −β<sub>attr</sub>/β<sub>price</sub>. Also ordered logit (purchase intention), quantile regression (stated WTP),
ANOVA and penalty analysis (tasting).</p>
<p style="margin:5pt 0 0"><b>Sample size:</b> simulation from assumed preferences recovers the probiotic premium within
±EUR 0.14 (150 respondents), ±0.09 (300), ±0.08 (500) → <b>at least 300 per country</b>.</p>
</div></div>
<p class="note">Sources: Eurostat Comext DS-045409, product 200950 (extracted 8 Nov 2026); ANICAV, 1 Dec 2025; Condurso et al., Foods 14(12):2148, 2025;
Ministero della Salute, guidelines on probiotics (rev. March 2018); Reg. (EC) 1924/2006. Trade code 200950 is a proxy (unfermented juice) and trade values are not retail sales.</p>

<div class="page2">
<img class="fig" src="{img('fig1_italy_exports_index.png')}" alt="Italy tomato juice exports index">
<img class="fig" src="{img('fig2_italy_export_destinations_2025.png')}" alt="Export destinations 2025">
</div>
<div class="page2">
<img class="fig" src="{img('fig3_eu_exporters_importers_2025.png')}" alt="EU exporters and importers">
<img class="fig" src="{img('fig4_dce_power_check.png')}" alt="Design check">
</div>
</body></html>"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.set_content(HTML, wait_until="load")
    pg.pdf(path=str(ROOT / "docs" / "market_study_plan.pdf"), format="A4", print_background=True,
           margin={"top": "14mm", "right": "15mm", "bottom": "13mm", "left": "15mm"})
    b.close()
print("wrote docs/market_study_plan.pdf")
