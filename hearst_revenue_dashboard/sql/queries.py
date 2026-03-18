"""
SQL query functions for the Hearst Revenue Operations Dashboard.
All data retrieval uses explicit SQL executed against the SQLite database.
Results are returned as pandas DataFrames via pd.read_sql_query().
No pandas aggregations — SQL does all the heavy lifting.
Each function creates its own fresh connection to avoid SQLite
serialisation errors on Streamlit Cloud.
"""

import sys
import os
import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.generate_data import get_database_connection


@st.cache_data
def get_portfolio_kpis() -> pd.DataFrame:
    """
    Single-row KPI summary across all brands and months for FY2024.
    Returns: total_revenue, total_available_impressions, total_sold_impressions,
             portfolio_fill_rate, weighted_avg_cpm.
    """
    sql = """
    SELECT
        ROUND(SUM(revenue), 2)
                                            AS total_revenue,
        SUM(available_impressions)
                                            AS total_available_impressions,
        SUM(sold_impressions)
                                            AS total_sold_impressions,
        ROUND(
            100.0 * CAST(SUM(sold_impressions) AS FLOAT)
            / SUM(available_impressions),
            2
        )                                   AS portfolio_fill_rate,
        ROUND(
            SUM(revenue)
            / (CAST(SUM(sold_impressions) AS FLOAT) / 1000.0),
            2
        )                                   AS weighted_avg_cpm
    FROM brand_inventory
    """
    conn = get_database_connection()
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


@st.cache_data
def get_brand_revenue_by_channel() -> pd.DataFrame:
    """
    Revenue and performance metrics grouped by brand and channel.
    Used for the brand comparison grouped bar chart.
    Returns: brand, channel, total_revenue, total_sold_impressions,
             avg_cpm, avg_fill_rate.
    """
    sql = """
    SELECT
        brand,
        channel,
        ROUND(SUM(revenue), 2)              AS total_revenue,
        SUM(sold_impressions)               AS total_sold_impressions,
        ROUND(AVG(cpm), 2)                  AS avg_cpm,
        ROUND(
            100.0 * CAST(SUM(sold_impressions) AS FLOAT)
            / SUM(available_impressions),
            2
        )                                   AS avg_fill_rate
    FROM brand_inventory
    GROUP BY brand, channel
    ORDER BY brand, total_revenue DESC
    """
    conn = get_database_connection()
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


@st.cache_data
def get_monthly_revenue_trend() -> pd.DataFrame:
    """
    Total portfolio revenue by month for the trend line chart.
    Returns: month, total_revenue.
    """
    sql = """
    SELECT
        month,
        ROUND(SUM(revenue), 2)              AS total_revenue
    FROM brand_inventory
    GROUP BY month
    ORDER BY month
    """
    conn = get_database_connection()
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


@st.cache_data
def get_advertiser_spend_trends() -> pd.DataFrame:
    """
    Monthly spend by vertical across the portfolio.
    concentration_flag = 1 when any single vertical exceeds 35% of
    total portfolio spend in that month.
    Returns: month, vertical, total_spend, concentration_flag.
    """
    sql = """
    WITH monthly_totals AS (
        SELECT
            month,
            SUM(spend_amount)               AS month_total
        FROM advertiser_spend
        GROUP BY month
    ),
    monthly_vertical AS (
        SELECT
            a.month,
            a.vertical,
            ROUND(SUM(a.spend_amount), 2)   AS total_spend,
            mt.month_total
        FROM advertiser_spend a
        JOIN monthly_totals mt ON a.month = mt.month
        GROUP BY a.month, a.vertical
    ),
    concentration_check AS (
        SELECT
            month,
            MAX(
                CAST(total_spend AS FLOAT) / month_total
            )                               AS max_vertical_share
        FROM monthly_vertical
        GROUP BY month
    )
    SELECT
        mv.month,
        mv.vertical,
        mv.total_spend,
        CASE
            WHEN cc.max_vertical_share > 0.35 THEN 1
            ELSE 0
        END                                 AS concentration_flag
    FROM monthly_vertical mv
    JOIN concentration_check cc ON mv.month = cc.month
    ORDER BY mv.month, mv.vertical
    """
    conn = get_database_connection()
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


@st.cache_data
def get_concentration_risk() -> pd.DataFrame:
    """
    Brands where the top 2 advertiser verticals account for more than
    60% of that brand's total annual spend.
    Returns: brand, top_vertical_1, top_vertical_2, top2_pct, brand_total.
    """
    sql = """
    WITH brand_vertical_spend AS (
        SELECT
            brand,
            vertical,
            SUM(spend_amount)               AS total_spend
        FROM advertiser_spend
        GROUP BY brand, vertical
    ),
    brand_total AS (
        SELECT
            brand,
            SUM(total_spend)                AS brand_total
        FROM brand_vertical_spend
        GROUP BY brand
    ),
    ranked AS (
        SELECT
            bvs.brand,
            bvs.vertical,
            bvs.total_spend,
            bt.brand_total,
            ROW_NUMBER() OVER (
                PARTITION BY bvs.brand
                ORDER BY bvs.total_spend DESC
            )                               AS rnk
        FROM brand_vertical_spend bvs
        JOIN brand_total bt ON bvs.brand = bt.brand
    )
    SELECT
        brand,
        MAX(brand_total)                    AS brand_total,
        SUM(total_spend)                    AS top2_spend,
        ROUND(
            100.0 * SUM(total_spend) / MAX(brand_total),
            2
        )                                   AS top2_pct,
        MAX(CASE WHEN rnk = 1 THEN vertical END) AS top_vertical_1,
        MAX(CASE WHEN rnk = 2 THEN vertical END) AS top_vertical_2
    FROM ranked
    WHERE rnk <= 2
    GROUP BY brand
    HAVING top2_pct > 60
    ORDER BY top2_pct DESC
    """
    conn = get_database_connection()
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


@st.cache_data
def get_pitch_to_pay_funnel() -> pd.DataFrame:
    """
    Funnel stages aggregated across all brands and months.
    Includes conversion_rate from the prior stage (NULL for first stage)
    and revenue_leakage as value lost entering each stage.
    Returns: stage, total_deals, total_value, total_leakage, conversion_rate.
    Stages ordered CRM Opportunity -> Reconciled.
    """
    sql = """
    WITH stage_agg AS (
        SELECT
            stage,
            SUM(deal_count)                 AS total_deals,
            ROUND(SUM(deal_value), 2)       AS total_value,
            ROUND(SUM(revenue_leakage), 2)  AS total_leakage,
            CASE stage
                WHEN 'CRM Opportunity'      THEN 1
                WHEN 'Order Created'        THEN 2
                WHEN 'Campaign Trafficked'  THEN 3
                WHEN 'Delivered'            THEN 4
                WHEN 'Billed'               THEN 5
                WHEN 'Reconciled'           THEN 6
            END                             AS stage_order
        FROM pitch_to_pay
        GROUP BY stage
    )
    SELECT
        stage,
        total_deals,
        total_value,
        total_leakage,
        ROUND(
            100.0 * total_value
            / LAG(total_value) OVER (ORDER BY stage_order),
            2
        )                                   AS conversion_rate
    FROM stage_agg
    ORDER BY stage_order
    """
    conn = get_database_connection()
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


@st.cache_data
def get_qa_summary() -> pd.DataFrame:
    """
    System health summary per source: anomaly counts, average completeness,
    average revenue variance, and data freshness.
    Returns: source, anomalies_detected, avg_completeness_pct,
             avg_variance_pct, most_recent_refresh, hours_since_last_refresh.
    """
    sql = """
    SELECT
        source,
        SUM(anomaly_flag)                   AS anomalies_detected,
        ROUND(AVG(completeness_pct), 2)     AS avg_completeness_pct,
        ROUND(AVG(variance_pct), 4)         AS avg_variance_pct,
        MAX(last_refresh)                   AS most_recent_refresh,
        ROUND(
            (JULIANDAY('now') - JULIANDAY(MAX(last_refresh))) * 24,
            1
        )                                   AS hours_since_last_refresh
    FROM data_qa_status
    GROUP BY source
    ORDER BY anomalies_detected DESC
    """
    conn = get_database_connection()
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


@st.cache_data
def get_revenue_reconciliation() -> pd.DataFrame:
    """
    Monthly cross-system revenue totals (Salesforce, AdPoint, GAM) and the
    relative reconciliation gap between the highest and lowest source.
    reconciliation_gap is expressed as a percentage of the three-way average.
    Returns: month, revenue_salesforce, revenue_adpoint, revenue_gam,
             reconciliation_gap.
    """
    sql = """
    WITH monthly_sums AS (
        SELECT
            month,
            SUM(revenue_salesforce)         AS rev_sf,
            SUM(revenue_adpoint)            AS rev_ap,
            SUM(revenue_gam)                AS rev_gam
        FROM data_qa_status
        GROUP BY month
    )
    SELECT
        month,
        ROUND(rev_sf, 2)                    AS revenue_salesforce,
        ROUND(rev_ap, 2)                    AS revenue_adpoint,
        ROUND(rev_gam, 2)                   AS revenue_gam,
        ROUND(
            100.0
            * (MAX(rev_sf, rev_ap, rev_gam) - MIN(rev_sf, rev_ap, rev_gam))
            / ((rev_sf + rev_ap + rev_gam) / 3.0),
            2
        )                                   AS reconciliation_gap
    FROM monthly_sums
    ORDER BY month
    """
    conn = get_database_connection()
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


@st.cache_data
def get_brand_summary_table() -> pd.DataFrame:
    """
    Per-brand summary with total revenue, fill rate, avg CPM, and top channel
    by revenue. Used for the Section 2 styled summary table.
    """
    sql = """
    WITH channel_ranked AS (
        SELECT
            brand,
            channel,
            SUM(revenue)                    AS ch_revenue,
            ROW_NUMBER() OVER (
                PARTITION BY brand
                ORDER BY SUM(revenue) DESC
            )                               AS rnk
        FROM brand_inventory
        GROUP BY brand, channel
    )
    SELECT
        bi.brand,
        ROUND(SUM(bi.revenue), 2)           AS total_revenue,
        ROUND(
            100.0 * CAST(SUM(bi.sold_impressions) AS FLOAT)
            / SUM(bi.available_impressions),
            2
        )                                   AS fill_rate,
        ROUND(
            SUM(bi.revenue)
            / (CAST(SUM(bi.sold_impressions) AS FLOAT) / 1000.0),
            2
        )                                   AS avg_cpm,
        cr.channel                          AS top_channel
    FROM brand_inventory bi
    JOIN (
        SELECT brand, channel
        FROM channel_ranked
        WHERE rnk = 1
    ) cr ON bi.brand = cr.brand
    GROUP BY bi.brand, cr.channel
    ORDER BY total_revenue DESC
    """
    conn = get_database_connection()
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


@st.cache_data
def get_anomaly_log() -> pd.DataFrame:
    """
    All flagged anomaly records with derived issue type and status.
    issue_type: 'High Variance' / 'Low Completeness' / 'Variance + Completeness'
    status: 'Open' for months >= 2024-09, 'Resolved' for earlier months.
    """
    sql = """
    SELECT
        source,
        brand,
        month,
        CASE
            WHEN variance_pct > 5 AND completeness_pct < 95
                THEN 'Variance + Completeness'
            WHEN variance_pct > 5
                THEN 'High Variance'
            ELSE 'Low Completeness'
        END                                 AS issue_type,
        ROUND(variance_pct, 2)              AS variance_pct,
        ROUND(completeness_pct, 2)          AS completeness_pct,
        CASE
            WHEN month >= '2024-09' THEN 'Open'
            ELSE 'Resolved'
        END                                 AS status
    FROM data_qa_status
    WHERE anomaly_flag = 1
    ORDER BY
        CASE WHEN month >= '2024-09' THEN 0 ELSE 1 END,
        variance_pct DESC
    """
    conn = get_database_connection()
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df
