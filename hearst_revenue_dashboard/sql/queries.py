"""
Pre-built SQL queries for the Hearst Revenue Operations Dashboard.
Each function returns a SQL string (and optionally parameters) ready
to be executed against the SQLite connection from generate_data.py.
"""


# ---------------------------------------------------------------------------
# brand_inventory queries
# ---------------------------------------------------------------------------

INVENTORY_SUMMARY_BY_BRAND = """
SELECT
    brand,
    SUM(revenue)                                        AS total_revenue,
    ROUND(AVG(fill_rate) * 100, 2)                      AS avg_fill_rate_pct,
    ROUND(AVG(cpm), 2)                                  AS avg_cpm,
    SUM(available_impressions)                          AS total_available_imps,
    SUM(sold_impressions)                               AS total_sold_imps
FROM brand_inventory
GROUP BY brand
ORDER BY total_revenue DESC;
"""

INVENTORY_BY_CHANNEL = """
SELECT
    channel,
    SUM(revenue)                                        AS total_revenue,
    ROUND(AVG(fill_rate) * 100, 2)                      AS avg_fill_rate_pct,
    ROUND(AVG(cpm), 2)                                  AS avg_cpm
FROM brand_inventory
GROUP BY channel
ORDER BY total_revenue DESC;
"""

MONTHLY_REVENUE_TREND = """
SELECT
    month,
    SUM(revenue)                                        AS portfolio_revenue,
    ROUND(AVG(fill_rate) * 100, 2)                      AS avg_fill_rate_pct
FROM brand_inventory
GROUP BY month
ORDER BY month;
"""

REVENUE_BY_BRAND_CHANNEL = """
SELECT
    brand,
    channel,
    ROUND(SUM(revenue), 2)                              AS total_revenue,
    ROUND(AVG(cpm), 2)                                  AS avg_cpm,
    ROUND(AVG(fill_rate) * 100, 2)                      AS avg_fill_rate_pct
FROM brand_inventory
GROUP BY brand, channel
ORDER BY brand, total_revenue DESC;
"""

QUARTERLY_REVENUE = """
SELECT
    brand,
    CASE
        WHEN SUBSTR(month, 6, 2) IN ('01','02','03') THEN 'Q1'
        WHEN SUBSTR(month, 6, 2) IN ('04','05','06') THEN 'Q2'
        WHEN SUBSTR(month, 6, 2) IN ('07','08','09') THEN 'Q3'
        ELSE 'Q4'
    END                                                 AS quarter,
    ROUND(SUM(revenue), 2)                              AS total_revenue
FROM brand_inventory
GROUP BY brand, quarter
ORDER BY brand, quarter;
"""


# ---------------------------------------------------------------------------
# advertiser_spend queries
# ---------------------------------------------------------------------------

SPEND_BY_VERTICAL = """
SELECT
    vertical,
    ROUND(SUM(spend_amount), 2)                         AS total_spend,
    ROUND(AVG(spend_amount), 2)                         AS avg_monthly_spend
FROM advertiser_spend
GROUP BY vertical
ORDER BY total_spend DESC;
"""

SPEND_BY_BRAND_VERTICAL = """
SELECT
    brand,
    vertical,
    ROUND(SUM(spend_amount), 2)                         AS total_spend
FROM advertiser_spend
GROUP BY brand, vertical
ORDER BY brand, total_spend DESC;
"""

MONTHLY_PORTFOLIO_SPEND = """
SELECT
    month,
    ROUND(SUM(spend_amount), 2)                         AS total_spend
FROM advertiser_spend
GROUP BY month
ORDER BY month;
"""

TOP_VERTICALS_BY_BRAND = """
SELECT
    brand,
    vertical,
    ROUND(SUM(spend_amount), 2)                         AS total_spend,
    ROUND(
        100.0 * SUM(spend_amount) /
        SUM(SUM(spend_amount)) OVER (PARTITION BY brand),
        2
    )                                                   AS share_of_brand_pct
FROM advertiser_spend
GROUP BY brand, vertical
ORDER BY brand, total_spend DESC;
"""


# ---------------------------------------------------------------------------
# pitch_to_pay queries
# ---------------------------------------------------------------------------

PIPELINE_FUNNEL_SUMMARY = """
SELECT
    stage,
    SUM(deal_count)                                     AS total_deals,
    ROUND(SUM(deal_value), 2)                           AS total_value,
    ROUND(SUM(revenue_leakage), 2)                      AS total_leakage
FROM pitch_to_pay
GROUP BY stage
ORDER BY
    CASE stage
        WHEN 'CRM Opportunity'      THEN 1
        WHEN 'Order Created'        THEN 2
        WHEN 'Campaign Trafficked'  THEN 3
        WHEN 'Delivered'            THEN 4
        WHEN 'Billed'               THEN 5
        WHEN 'Reconciled'           THEN 6
    END;
"""

LEAKAGE_BY_BRAND = """
SELECT
    brand,
    ROUND(SUM(revenue_leakage), 2)                      AS total_leakage,
    ROUND(
        100.0 * SUM(revenue_leakage) /
        SUM(SUM(revenue_leakage)) OVER (),
        2
    )                                                   AS leakage_share_pct
FROM pitch_to_pay
GROUP BY brand
ORDER BY total_leakage DESC;
"""

CONVERSION_RATES_BY_BRAND = """
WITH stage_vals AS (
    SELECT
        brand,
        stage,
        AVG(deal_value)                                 AS avg_value
    FROM pitch_to_pay
    GROUP BY brand, stage
)
SELECT
    brand,
    ROUND(
        100.0 *
        MAX(CASE WHEN stage = 'Reconciled'      THEN avg_value ELSE NULL END) /
        MAX(CASE WHEN stage = 'CRM Opportunity' THEN avg_value ELSE NULL END),
        2
    )                                                   AS end_to_end_conversion_pct
FROM stage_vals
GROUP BY brand
ORDER BY end_to_end_conversion_pct DESC;
"""

MONTHLY_PIPELINE_VALUE = """
SELECT
    month,
    stage,
    ROUND(SUM(deal_value), 2)                           AS total_value
FROM pitch_to_pay
WHERE stage IN ('CRM Opportunity', 'Reconciled')
GROUP BY month, stage
ORDER BY month, stage;
"""


# ---------------------------------------------------------------------------
# data_qa_status queries
# ---------------------------------------------------------------------------

ANOMALY_SUMMARY = """
SELECT
    source,
    brand,
    month,
    completeness_pct,
    variance_pct,
    anomaly_flag,
    last_refresh
FROM data_qa_status
WHERE anomaly_flag = 1
ORDER BY variance_pct DESC;
"""

STALE_SOURCES = """
SELECT
    source,
    brand,
    month,
    last_refresh,
    ROUND(
        (JULIANDAY('now') - JULIANDAY(last_refresh)) * 24,
        1
    )                                                   AS hours_since_refresh
FROM data_qa_status
WHERE (JULIANDAY('now') - JULIANDAY(last_refresh)) * 24 > 24
ORDER BY hours_since_refresh DESC;
"""

COMPLETENESS_BY_SOURCE = """
SELECT
    source,
    ROUND(AVG(completeness_pct), 2)                     AS avg_completeness_pct,
    SUM(CASE WHEN completeness_pct < 95 THEN 1 ELSE 0 END) AS low_completeness_months
FROM data_qa_status
GROUP BY source
ORDER BY avg_completeness_pct DESC;
"""

REVENUE_VARIANCE_HEATMAP = """
SELECT
    source,
    brand,
    ROUND(AVG(variance_pct), 4)                         AS avg_variance_pct,
    MAX(variance_pct)                                   AS max_variance_pct,
    SUM(anomaly_flag)                                   AS anomaly_count
FROM data_qa_status
GROUP BY source, brand
ORDER BY avg_variance_pct DESC;
"""

SYSTEM_HEALTH_OVERVIEW = """
SELECT
    source,
    COUNT(*)                                            AS total_records,
    ROUND(AVG(completeness_pct), 2)                     AS avg_completeness_pct,
    ROUND(AVG(variance_pct), 4)                         AS avg_variance_pct,
    SUM(anomaly_flag)                                   AS total_anomalies,
    SUM(
        CASE
            WHEN (JULIANDAY('now') - JULIANDAY(last_refresh)) * 24 > 24
            THEN 1 ELSE 0
        END
    )                                                   AS stale_feeds
FROM data_qa_status
GROUP BY source
ORDER BY total_anomalies DESC;
"""
