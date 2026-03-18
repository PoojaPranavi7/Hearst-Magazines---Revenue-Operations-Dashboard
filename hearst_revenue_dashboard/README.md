# Hearst Magazines — Revenue Operations Intelligence Dashboard

A full-stack analytics dashboard simulating the Revenue Operations reporting layer for a premium digital publishing portfolio, built with Python, SQL, Streamlit, and Plotly.

---

## What This Demonstrates

Each section of the dashboard maps directly to a core competency for the Hearst Revenue Operations role:

| Dashboard Section | Role Requirement It Proves |
|---|---|
| **Portfolio KPIs** — Total Revenue, Fill Rate, Weighted CPM, Impression Volume | Ability to define and surface the top-line metrics a Revenue Operations team monitors daily; fluency with digital advertising KPIs (CPM, fill rate, sold vs. available inventory) |
| **Brand Performance by Channel** — Grouped bar chart, conditional-formatted summary table | Cross-brand performance analysis across revenue channels (Direct-Sold, PG, PMP, Open Auction); ability to identify which channel mix is driving yield per brand |
| **Advertiser Spend Trends** — 12-month vertical spend lines, concentration risk alert | Advertiser category analysis and revenue diversification; proactive identification of concentration risk before it becomes a revenue exposure (a core RevOps responsibility) |
| **Pitch-to-Pay Lifecycle** — Funnel chart, leakage analysis table, bottleneck callout | End-to-end deal pipeline visibility from CRM opportunity through billing reconciliation; quantifying revenue leakage by stage, which directly informs process improvement priorities |
| **Data QA & Pipeline Health** — System status cards, cross-source reconciliation, anomaly log | Data governance and pipeline monitoring across Salesforce, AdPoint, and GAM — the exact three systems Hearst's revenue operations team reconciles; ability to flag data quality issues before they affect financial reporting |
| **Key Insights** — Narrative insight cards with recommended actions | Translating data findings into business language for non-technical stakeholders (Sales, Finance, Editorial leadership); pairing each insight with a specific, quantified recommendation |

---

## Data Sources

The dataset is entirely synthetic and generated programmatically in `data/generate_data.py` using `numpy.random.seed(42)` for full reproducibility. All values are grounded in real industry benchmarks:

- **CPM ranges** are derived from IAB Digital Advertising Revenue Reports and public programmatic benchmarks for premium lifestyle and enthusiast publishers (Direct-Sold: $18–28, PG: $14–20, PMP: $10–16, Open Auction: $4–8)
- **Fill rate ranges** reflect industry norms by channel type (Direct-Sold 85–95%, Open Auction 55–75%)
- **Fashion brand CPM premium** (+15–25%) reflects the documented yield advantage of Vogue, ELLE, and Harper's BAZAAR over general-interest titles, as reported in Condé Nast and Hearst public media kits
- **Seasonal patterns** (Q4 +20–30%, Q2 −10–15%) reflect the standard digital advertising calendar documented in IAB and Magna Global seasonal indices
- **Advertiser vertical weights** (Beauty/Fashion dominant on ELLE and Cosmopolitan; Technology/Automotive dominant on Popular Mechanics and Esquire) mirror the publicly available audience composition and advertiser category data in Hearst's media kit

No proprietary Hearst data was used. This project is a portfolio demonstration only.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.9+ |
| **Data Layer** | SQL (SQLite3 — Python standard library) |
| **Data Manipulation** | Pandas 2.2 — display and formatting only; all aggregations are performed in SQL |
| **Numerical Simulation** | NumPy 1.26 — synthetic data generation with controlled randomness |
| **Dashboard Framework** | Streamlit 1.32 — single-page app with custom CSS |
| **Visualisation** | Plotly 5.19 — interactive charts (funnel, grouped bar, line, area, horizontal bar) |

### Architecture decisions

- **SQL-first aggregation** — all GROUP BY, window functions (LAG, ROW_NUMBER, SUM OVER), and CTEs are written in `sql/queries.py` and executed directly against SQLite. Pandas is used only for rendering and conditional formatting, keeping the SQL skill clearly visible.
- **In-memory SQLite** — no database server required; the connection is created fresh on app load and cached via `@st.cache_resource`.
- **Reproducible data** — `numpy.random.seed(42)` ensures every run produces identical numbers, making the dashboard suitable for a live demo without a live data source.

---

## Project Structure

```
hearst_revenue_dashboard/
├── app.py                  # Streamlit entry point — single-page dashboard
├── data/
│   └── generate_data.py    # Synthetic data generation + get_database_connection()
├── sql/
│   └── queries.py          # 10 SQL query functions returning pd.DataFrames
├── requirements.txt
└── README.md
```

**Database tables**

| Table | Rows | Description |
|---|---|---|
| `brand_inventory` | 288 | Monthly impressions, fill rate, CPM, revenue — 6 brands × 12 months × 4 channels |
| `advertiser_spend` | 432 | Monthly spend — 6 brands × 12 months × 6 verticals |
| `pitch_to_pay` | 432 | Pipeline funnel — 6 brands × 12 months × 6 stages, with deal count, value, and leakage |
| `data_qa_status` | 216 | Cross-system data quality — 3 sources × 6 brands × 12 months, with anomaly flags |

---

## How to Run Locally

**1. Clone the repository**

```bash
git clone https://github.com/<your-username>/hearst-revenue-dashboard.git
cd hearst-revenue-dashboard/hearst_revenue_dashboard
```

**2. Create a virtual environment (recommended)**

```bash
python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the app**

```bash
streamlit run app.py
```

The dashboard will open automatically at `http://localhost:8501`.

---

## How to Deploy to Streamlit Community Cloud

Streamlit Community Cloud is a free hosting platform for Streamlit apps directly connected to GitHub.

**1. Push to GitHub**

```bash
git add .
git commit -m "Initial deploy"
git push origin main
```

**2. Connect to Streamlit Community Cloud**

- Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account
- Click **"New app"**
- Select your repository, set the branch to `main`, and set the main file path to `hearst_revenue_dashboard/app.py`
- Click **"Deploy"**

**3. Share**

Streamlit Community Cloud will provide a public URL (e.g. `https://<your-app>.streamlit.app`) within a few minutes. No server configuration required.

> **Note:** The app uses an in-memory SQLite database that is re-created on each session, so no external database or credentials are needed for deployment.

---

*Built by Pooja Pranavi Nalamothu | Revenue Operations Portfolio Project*
*Data: Synthetic dataset grounded in IAB benchmark CPMs and Hearst public media kit audience figures*
*Built with Python, SQL, Streamlit, Plotly*
