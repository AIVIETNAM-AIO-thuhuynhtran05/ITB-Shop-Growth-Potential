# Shop Growth Potential | Python, DuckDB, LightGBM

Final round of the **ITB Competition (Business Intelligence Season 10, UEL)**, where our team finished **runner-up of 200 teams**. The question: *how far can a specific partner shop realistically grow, what constrains it, and what should Sales Management do to close the gap?*

Two shops can sign the same number of loan contracts today, yet one still has room to grow and the other is at its limit. For each of a consumer-finance lender's **11,795 shops**, we estimated four levels and kept them strictly apart:

| Level | Meaning | Network result |
|---|---|---|
| **Current Actual** | What the shop achieves today (Q3/2026) | 41,467 contracts a month, VND 539 bn |
| **Business-as-Usual** | What it reaches in Q4/2026 if nothing changes | 41,186 a month (−0.7%), range about ±7% |
| **Attainable Potential** | What feasible actions within Sales' control add | +1,574 a month for active shops (+6.1%) |
| **Addressable Market Ceiling** | Demand that could in theory be served | 72,242 a month (base); the network uses ~57% |

`BAU ≤ Attainable ≤ Ceiling` holds for every shop.

> Competition project by team *Đường sắt Bắc – Nam*, continuing the storyline of [Round 2](https://github.com/AIVIETNAM-AIO-thuhuynhtran05/ITB-Customer-Health-Engagement-Scoring). The internal dataset belongs to the organisers and is not included; the external data is.

## Key findings

1. **No action means no growth.** 93% of growth came from opening shops; contracts per shop are flat and 51% of shops sign less than one contract a month.
2. **Weak shops lack customers, not skills.** Strong shops get about 8× more applications than weak ones at nearly the same approval and completion rates. Two-thirds of active shops are short of customers.
3. **Benchmarks overstate potential.** Taking the peer P75 at face value implies +52%; levers with measured impact support +6.1%.
4. **Market size is not the limit for most shops.** Hà Nội uses 37% of its base ceiling and Hải Phòng 32%, while Đồng Nai is already at 100%.
5. **Same sales, different headroom.** Shops #117673569 and #96605617 both sign ~4 contracts a month in the same segment; the first can add +1.8 a month, the second is near its limit.

## Recommendations

- Invest in 3,954 tier-A shops ranked by risk-adjusted headroom; the top 500 return about +392 contracts and +VND 6.4 bn a month (range 2.6–13.8 bn).
- Route ~21.8K campaign leads a quarter to shops below their peer P75; add sales agents only at under-staffed Aldi shops; coach lead handling where closing is weak.
- No growth targets for 465 high-risk shops; reactivate 696 inactive shops and exit 1,464; expand in Hà Nội, Hải Phòng, Ninh Bình and Hưng Yên.
- Prove it with a 3-month controlled pilot of about 1,270 shops per arm before scaling.

## Method

| Step | Technique | Tools |
|---|---|---|
| Data (01, 02) | Null / duplicate / outlier checks; placeholders to NULL with flags; 54 province names mapped to the 34 post-merger provinces; lead → contract link by the brief's three rules, one-to-one within 30 days | DuckDB SQL, pandas |
| Current Actual (03) | Funnel KPIs (application → approval → signed → first payment), network growth split into new shops vs output per shop, shop life cycle | DuckDB, pandas, matplotlib |
| BAU (04) | 17 methods backtested on three quarters; chosen blend of LightGBM, Random Forest and exponential smoothing; P10–P90 from backtest errors; Monte Carlo; Shapley values by factor group | LightGBM, scikit-learn |
| Attainable (05) | Lever impact measured in the same shop across two quarters, net of segment trend; funnel recalculated; capped at peer P75 and the ceiling; risk guardrail at peer P90 first-payment default | pandas, NumPy |
| Ceiling (05) | Population × applications per 100K people (quantile regression on income and density across 34 provinces) × approval × completion; low / base / high scenarios | scikit-learn (QuantileRegressor) |
| Priority (05) | (Attainable − BAU) × expected loan size, discounted for risk and thin evidence; tiers A–D | pandas |
| Validation (04, 05) | Out-of-time check that "headroom" shops grow faster, P70/P80 sensitivity, bootstrap, pilot sample size | SciPy, NumPy |

## Repository structure

```
├── 01_EDA.ipynb                               # data quality, keys, lead → contract rules
├── 02_clean_data.py                           # cleaning, 34 provinces, lead → contract link
├── 02b_Overview_Market_Customer_Lead_SA.ipynb # market, customers (Round 2 labels), leads, sales agents
├── 03_Current_Actual.ipynb                    # Current Actual by segment and shop
├── 04_BAU.ipynb                               # Business-as-Usual forecast and backtests
├── 05_Potential_Prioritization.ipynb          # Attainable, Ceiling, gaps, priority, validation
├── data_external/                             # population and income for 34 provinces + README
├── output/                                    # summary tables and recommendation lists
├── slides/ITB_Final_Shop_Growth_Potential_Slides.pdf
└── README_vi.md                               # original working notes (Vietnamese)
```

Notebook comments and output column names are in Vietnamese; the slides are in English. The two largest outputs (`bau_2026Q4.csv`, `shop_potential_2026Q3.csv`) are regenerated by notebooks 04 and 05.

## External data

| File | Source and period | Coverage | Mapping |
|---|---|---|---|
| `population_34_provinces.csv` | 2024 mid-term population census (National Statistics Office), aggregated to the 34 provinces | Province level | `province_std`, 34/34 matched |
| `income_2025_34_provinces.csv` | Average monthly income per capita by source, 2025 | Province level | `province_std`, 34/34 matched |

Limits: only 34 observations, total population rather than adults, average rather than distributed income, and a one-year gap between the two sources. Details are in [`data_external/README.md`](data_external/README.md).

## How to run

1. Place the competition files in `Round3_BI10_dataset/` (not included).
2. Run from the repository root: `python 02_clean_data.py`, then notebooks `02b` → `03` → `04` → `05` (05 reads the output of 04).

## Tools

Python (pandas, DuckDB, NumPy, SciPy), LightGBM, scikit-learn, matplotlib.
