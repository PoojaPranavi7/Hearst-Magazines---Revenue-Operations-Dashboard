"""
Synthetic data generation for Hearst Revenue Operations Dashboard.
Generates realistic data grounded in premium digital publisher industry benchmarks.
"""

import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

BRANDS = [
    "Cosmopolitan",
    "ELLE",
    "Esquire",
    "Harper's BAZAAR",
    "Good Housekeeping",
    "Popular Mechanics",
]

FASHION_BRANDS = {"ELLE", "Harper's BAZAAR", "Cosmopolitan"}

MONTHS = pd.date_range(start="2024-01-01", periods=12, freq="MS")

CHANNELS = [
    "Direct-Sold",
    "Programmatic Guaranteed",
    "Private Marketplace",
    "Open Auction",
]

CHANNEL_CONFIG = {
    "Direct-Sold":                {"cpm_range": (18, 28), "fill_range": (0.85, 0.95)},
    "Programmatic Guaranteed":    {"cpm_range": (14, 20), "fill_range": (0.80, 0.90)},
    "Private Marketplace":        {"cpm_range": (10, 16), "fill_range": (0.70, 0.85)},
    "Open Auction":               {"cpm_range": (4,   8), "fill_range": (0.55, 0.75)},
}

VERTICALS = ["Beauty", "Automotive", "Finance", "Retail", "Fashion", "Technology"]

STAGES = [
    "CRM Opportunity",
    "Order Created",
    "Campaign Trafficked",
    "Delivered",
    "Billed",
    "Reconciled",
]

STAGE_CONVERSION = {
    "CRM Opportunity":    (0.75, 0.85),   # → Order Created
    "Order Created":      (0.88, 0.95),   # → Campaign Trafficked
    "Campaign Trafficked":(0.90, 0.97),   # → Delivered
    "Delivered":          (0.92, 0.98),   # → Billed
    "Billed":             (0.85, 0.95),   # → Reconciled
}

SOURCES = ["Salesforce", "AdPoint", "GAM"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def seasonal_multiplier(month: pd.Timestamp) -> float:
    """Return a revenue multiplier based on quarter seasonality."""
    q = month.quarter
    if q == 4:
        return np.random.uniform(1.20, 1.30)
    if q == 2:
        return np.random.uniform(0.85, 0.90)
    return np.random.uniform(0.97, 1.03)


def fashion_cpm_premium(brand: str, base_cpm: float) -> float:
    """Fashion brands command a 15-25% CPM premium."""
    if brand in FASHION_BRANDS:
        return base_cpm * np.random.uniform(1.15, 1.25)
    return base_cpm


# ---------------------------------------------------------------------------
# Table 1: brand_inventory
# ---------------------------------------------------------------------------

def generate_brand_inventory() -> pd.DataFrame:
    rows = []
    for brand in BRANDS:
        for month in MONTHS:
            for channel in CHANNELS:
                cfg = CHANNEL_CONFIG[channel]
                base_cpm = np.random.uniform(*cfg["cpm_range"])
                cpm = fashion_cpm_premium(brand, base_cpm)

                fill_rate = np.random.uniform(*cfg["fill_range"])

                # Available impressions: 5M–50M depending on brand/channel
                available = int(np.random.uniform(5_000_000, 50_000_000))
                sold = int(available * fill_rate * np.random.uniform(0.97, 1.03))
                sold = min(sold, available)

                base_revenue = (sold / 1_000) * cpm
                revenue = base_revenue * seasonal_multiplier(month)

                rows.append({
                    "brand": brand,
                    "month": month.strftime("%Y-%m"),
                    "channel": channel,
                    "available_impressions": available,
                    "sold_impressions": sold,
                    "fill_rate": round(sold / available, 4),
                    "cpm": round(cpm, 2),
                    "revenue": round(revenue, 2),
                })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Table 2: advertiser_spend
# ---------------------------------------------------------------------------

def vertical_weight(brand: str, vertical: str) -> float:
    """Define realistic vertical spend weights per brand."""
    weights = {
        "Cosmopolitan":       {"Beauty": 0.35, "Fashion": 0.28, "Retail": 0.15, "Finance": 0.08, "Automotive": 0.06, "Technology": 0.08},
        "ELLE":               {"Beauty": 0.30, "Fashion": 0.32, "Retail": 0.14, "Finance": 0.07, "Automotive": 0.05, "Technology": 0.12},
        "Esquire":            {"Beauty": 0.10, "Fashion": 0.12, "Retail": 0.12, "Finance": 0.18, "Automotive": 0.25, "Technology": 0.23},
        "Harper's BAZAAR":    {"Beauty": 0.32, "Fashion": 0.33, "Retail": 0.13, "Finance": 0.08, "Automotive": 0.05, "Technology": 0.09},
        "Good Housekeeping":  {"Beauty": 0.22, "Fashion": 0.10, "Retail": 0.28, "Finance": 0.15, "Automotive": 0.10, "Technology": 0.15},
        "Popular Mechanics":  {"Beauty": 0.05, "Fashion": 0.05, "Retail": 0.10, "Finance": 0.12, "Automotive": 0.30, "Technology": 0.38},
    }
    return weights[brand][vertical]


def retail_seasonal(month: pd.Timestamp) -> float:
    if month.quarter == 4:
        return np.random.uniform(1.40, 1.60)
    return np.random.uniform(0.90, 1.10)


def auto_seasonal(month: pd.Timestamp) -> float:
    if month.quarter == 2:
        return np.random.uniform(1.20, 1.35)
    return np.random.uniform(0.92, 1.08)


def generate_advertiser_spend() -> pd.DataFrame:
    rows = []
    for brand in BRANDS:
        for month in MONTHS:
            # Total monthly spend per brand: $400k–$1.5M (portfolio $2M–$8M / 6 brands)
            total_brand_spend = np.random.uniform(400_000, 1_500_000)
            for vertical in VERTICALS:
                base_weight = vertical_weight(brand, vertical)
                spend = total_brand_spend * base_weight

                if vertical == "Retail":
                    spend *= retail_seasonal(month)
                elif vertical == "Automotive":
                    spend *= auto_seasonal(month)
                else:
                    spend *= np.random.uniform(0.93, 1.07)

                rows.append({
                    "brand": brand,
                    "month": month.strftime("%Y-%m"),
                    "vertical": vertical,
                    "spend_amount": round(spend, 2),
                })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Table 3: pitch_to_pay
# ---------------------------------------------------------------------------

def generate_pitch_to_pay() -> pd.DataFrame:
    rows = []
    for brand in BRANDS:
        for month in MONTHS:
            # Seed: 100–150 CRM opportunities
            crm_count = int(np.random.uniform(100, 150))
            # Average deal value at CRM stage: $15k–$60k
            avg_deal_value = np.random.uniform(15_000, 60_000)
            crm_value = crm_count * avg_deal_value

            prev_count = crm_count
            prev_value = crm_value

            # CRM Opportunity row
            rows.append({
                "brand": brand,
                "month": month.strftime("%Y-%m"),
                "stage": "CRM Opportunity",
                "deal_count": crm_count,
                "deal_value": round(crm_value, 2),
                "revenue_leakage": 0.0,
            })

            cumulative_leakage = 0.0
            stages_in_order = [
                "Order Created",
                "Campaign Trafficked",
                "Delivered",
                "Billed",
                "Reconciled",
            ]

            for stage in stages_in_order:
                prev_stage = STAGES[STAGES.index(stage) - 1]
                conv_low, conv_high = STAGE_CONVERSION[prev_stage]
                rate = np.random.uniform(conv_low, conv_high)

                new_count = int(prev_count * rate)
                new_value = prev_value * rate
                leakage = round(prev_value - new_value, 2)
                cumulative_leakage += leakage

                rows.append({
                    "brand": brand,
                    "month": month.strftime("%Y-%m"),
                    "stage": stage,
                    "deal_count": new_count,
                    "deal_value": round(new_value, 2),
                    "revenue_leakage": round(leakage, 2),
                })

                prev_count = new_count
                prev_value = new_value

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Table 4: data_qa_status
# ---------------------------------------------------------------------------

def generate_data_qa_status() -> pd.DataFrame:
    rows = []
    now = datetime.now()

    # Pre-select indices that will be anomalous (>5% variance) — 2–3 per source
    anomaly_slots: dict[str, list[tuple[str, str]]] = {}
    for source in SOURCES:
        brand_month_combos = [
            (b, m.strftime("%Y-%m")) for b in BRANDS for m in MONTHS
        ]
        chosen = [
            brand_month_combos[i]
            for i in np.random.choice(len(brand_month_combos), size=3, replace=False)
        ]
        anomaly_slots[source] = chosen

    # Pre-select 1–2 stale sources (last_refresh > 24 hours ago)
    stale_source_brands = [
        (SOURCES[0], BRANDS[0]),
        (SOURCES[2], BRANDS[3]),
    ]

    for source in SOURCES:
        for brand in BRANDS:
            for month in MONTHS:
                month_str = month.strftime("%Y-%m")

                records_expected = int(np.random.uniform(8_000, 25_000))
                completeness = np.random.uniform(0.96, 1.00)

                is_anomaly_slot = (brand, month_str) in anomaly_slots[source]
                if is_anomaly_slot:
                    completeness = np.random.uniform(0.88, 0.94)

                records_received = int(records_expected * completeness)

                # Revenue figures across three systems
                base_rev = np.random.uniform(200_000, 2_000_000)
                rev_sf = round(base_rev * np.random.uniform(0.995, 1.005), 2)
                rev_ap = round(base_rev * np.random.uniform(0.995, 1.005), 2)
                rev_gam = round(base_rev * np.random.uniform(0.995, 1.005), 2)

                if is_anomaly_slot:
                    # Force a >5% variance on one of the systems
                    rev_sf = round(base_rev * np.random.uniform(1.06, 1.12), 2)

                avg_rev = (rev_sf + rev_ap + rev_gam) / 3
                variance_pct = round(
                    (max(rev_sf, rev_ap, rev_gam) - min(rev_sf, rev_ap, rev_gam))
                    / avg_rev * 100, 4
                )

                anomaly_flag = variance_pct > 5.0 or completeness < 0.95

                # Freshness
                is_stale = (source, brand) in stale_source_brands and month == MONTHS[-1]
                if is_stale:
                    last_refresh = now - timedelta(hours=np.random.uniform(26, 72))
                else:
                    last_refresh = now - timedelta(hours=np.random.uniform(0.5, 23))

                rows.append({
                    "source": source,
                    "brand": brand,
                    "month": month_str,
                    "records_expected": records_expected,
                    "records_received": records_received,
                    "completeness_pct": round(completeness * 100, 2),
                    "revenue_salesforce": rev_sf,
                    "revenue_adpoint": rev_ap,
                    "revenue_gam": rev_gam,
                    "variance_pct": variance_pct,
                    "anomaly_flag": int(anomaly_flag),
                    "last_refresh": last_refresh.strftime("%Y-%m-%d %H:%M:%S"),
                })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Database loader
# ---------------------------------------------------------------------------

def get_database_connection() -> sqlite3.Connection:
    """
    Build all synthetic tables and return a ready-to-query SQLite connection.
    The connection uses an in-memory database; call this function each time
    a fresh connection is needed.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    brand_inventory = generate_brand_inventory()
    advertiser_spend = generate_advertiser_spend()
    pitch_to_pay = generate_pitch_to_pay()
    data_qa_status = generate_data_qa_status()

    brand_inventory.to_sql("brand_inventory", conn, index=False, if_exists="replace")
    advertiser_spend.to_sql("advertiser_spend", conn, index=False, if_exists="replace")
    pitch_to_pay.to_sql("pitch_to_pay", conn, index=False, if_exists="replace")
    data_qa_status.to_sql("data_qa_status", conn, index=False, if_exists="replace")

    # Helpful indices for query performance
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bi_brand_month ON brand_inventory(brand, month)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_as_brand_month ON advertiser_spend(brand, month)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_p2p_brand_month ON pitch_to_pay(brand, month)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_source_brand ON data_qa_status(source, brand)")
    conn.commit()

    return conn


if __name__ == "__main__":
    conn = get_database_connection()
    cur = conn.cursor()
    for table in ["brand_inventory", "advertiser_spend", "pitch_to_pay", "data_qa_status"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"{table}: {cur.fetchone()[0]} rows")
    conn.close()
