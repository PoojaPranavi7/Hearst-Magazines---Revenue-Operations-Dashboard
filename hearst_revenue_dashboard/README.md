# Hearst Magazines — Revenue Operations Dashboard

A Streamlit dashboard powered by a fully synthetic, reproducible SQLite dataset
modelled on realistic benchmarks for a premium digital publisher.

## Project structure

```
hearst_revenue_dashboard/
├── app.py                  # Streamlit entry point
├── data/
│   └── generate_data.py    # Synthetic data generation + SQLite loader
├── sql/
│   └── queries.py          # Named SQL query constants
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
cd hearst_revenue_dashboard
streamlit run app.py
```

## Data model

| Table | Rows | Description |
|---|---|---|
| `brand_inventory` | 288 | Monthly impressions, fill rate, CPM, revenue per brand × channel (6 brands × 12 months × 4 channels) |
| `advertiser_spend` | 432 | Monthly spend per brand × vertical (6 × 12 × 6) |
| `pitch_to_pay` | 432 | Pipeline funnel with deal count, value, and leakage at each stage (6 × 12 × 6 stages) |
| `data_qa_status` | 216 | Cross-system data completeness, variance, anomaly flags, and freshness (3 sources × 6 brands × 12 months) |

All data is generated with `numpy.random.seed(42)` for full reproducibility.

## Dashboard tabs

1. **Inventory & Revenue** — portfolio revenue KPIs, monthly trend, channel mix, CPM benchmarks
2. **Advertiser Spend** — vertical spend breakdown, brand × vertical heatmap, seasonal trends
3. **Pitch-to-Pay** — funnel visualisation, leakage by brand and stage, end-to-end conversion rate
4. **Data QA** — system health overview, anomaly scatter, stale feed alerts
