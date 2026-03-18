"""
Hearst Revenue Operations Dashboard — entry point.
Run with: streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Hearst Revenue Operations",
    page_icon="📊",
    layout="wide",
)

from data.generate_data import get_database_connection  # noqa: E402

@st.cache_resource(show_spinner="Loading data…")
def load_db():
    return get_database_connection()


conn = load_db()

st.title("Hearst Magazines — Revenue Operations Dashboard")
st.caption("Synthetic data | Jan 2024 – Dec 2024 | numpy.random.seed(42)")

import pandas as pd  # noqa: E402
from sql import queries  # noqa: E402

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

brands = ["All"] + sorted(
    pd.read_sql("SELECT DISTINCT brand FROM brand_inventory ORDER BY brand", conn)[
        "brand"
    ].tolist()
)
selected_brand = st.sidebar.selectbox("Brand", brands)

months = pd.read_sql(
    "SELECT DISTINCT month FROM brand_inventory ORDER BY month", conn
)["month"].tolist()
selected_months = st.sidebar.select_slider(
    "Month range",
    options=months,
    value=(months[0], months[-1]),
)
month_filter = f"month BETWEEN '{selected_months[0]}' AND '{selected_months[1]}'"
brand_filter = "" if selected_brand == "All" else f"AND brand = '{selected_brand}'"


# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📦 Inventory & Revenue", "💰 Advertiser Spend", "🔄 Pitch-to-Pay", "🔍 Data QA"]
)


# ============================================================
# TAB 1: Inventory & Revenue
# ============================================================
with tab1:
    st.subheader("Portfolio Revenue Overview")

    inv_summary = pd.read_sql(
        f"""
        SELECT brand,
               ROUND(SUM(revenue), 0)            AS total_revenue,
               ROUND(AVG(fill_rate)*100, 2)       AS avg_fill_rate_pct,
               ROUND(AVG(cpm), 2)                 AS avg_cpm,
               SUM(sold_impressions)              AS sold_impressions
        FROM brand_inventory
        WHERE {month_filter} {brand_filter}
        GROUP BY brand
        ORDER BY total_revenue DESC
        """,
        conn,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${inv_summary['total_revenue'].sum():,.0f}")
    col2.metric("Avg Fill Rate", f"{inv_summary['avg_fill_rate_pct'].mean():.1f}%")
    col3.metric("Avg CPM", f"${inv_summary['avg_cpm'].mean():.2f}")

    import plotly.express as px  # noqa: E402

    fig_rev = px.bar(
        inv_summary,
        x="brand",
        y="total_revenue",
        color="brand",
        title="Total Revenue by Brand",
        labels={"total_revenue": "Revenue ($)", "brand": "Brand"},
        text_auto=".3s",
    )
    st.plotly_chart(fig_rev, use_container_width=True)

    # Monthly trend
    trend = pd.read_sql(
        f"""
        SELECT month, {'' if selected_brand == 'All' else 'brand,'}
               ROUND(SUM(revenue), 0) AS revenue,
               ROUND(AVG(fill_rate)*100, 2) AS fill_rate_pct
        FROM brand_inventory
        WHERE {month_filter} {brand_filter}
        GROUP BY month {'' if selected_brand == 'All' else ', brand'}
        ORDER BY month
        """,
        conn,
    )

    fig_trend = px.line(
        trend,
        x="month",
        y="revenue",
        color="brand" if "brand" in trend.columns else None,
        title="Monthly Revenue Trend",
        markers=True,
        labels={"revenue": "Revenue ($)", "month": "Month"},
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # Channel breakdown
    channel_data = pd.read_sql(
        f"""
        SELECT channel,
               ROUND(SUM(revenue), 0)      AS total_revenue,
               ROUND(AVG(fill_rate)*100, 2) AS avg_fill_rate_pct,
               ROUND(AVG(cpm), 2)           AS avg_cpm
        FROM brand_inventory
        WHERE {month_filter} {brand_filter}
        GROUP BY channel
        ORDER BY total_revenue DESC
        """,
        conn,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        fig_pie = px.pie(
            channel_data,
            names="channel",
            values="total_revenue",
            title="Revenue Mix by Channel",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        fig_cpm = px.bar(
            channel_data,
            x="channel",
            y="avg_cpm",
            color="channel",
            title="Average CPM by Channel",
            text_auto=".2f",
            labels={"avg_cpm": "CPM ($)", "channel": "Channel"},
        )
        st.plotly_chart(fig_cpm, use_container_width=True)

    st.dataframe(
        inv_summary.rename(
            columns={
                "total_revenue": "Revenue ($)",
                "avg_fill_rate_pct": "Fill Rate (%)",
                "avg_cpm": "CPM ($)",
                "sold_impressions": "Sold Impressions",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAB 2: Advertiser Spend
# ============================================================
with tab2:
    st.subheader("Advertiser Spend by Vertical")

    spend_data = pd.read_sql(
        f"""
        SELECT brand, vertical,
               ROUND(SUM(spend_amount), 0) AS total_spend
        FROM advertiser_spend
        WHERE {month_filter} {brand_filter}
        GROUP BY brand, vertical
        ORDER BY total_spend DESC
        """,
        conn,
    )

    col1, col2 = st.columns(2)

    with col1:
        fig_spend_brand = px.bar(
            spend_data.groupby("brand")["total_spend"].sum().reset_index(),
            x="brand",
            y="total_spend",
            color="brand",
            title="Total Spend by Brand",
            text_auto=".3s",
            labels={"total_spend": "Spend ($)", "brand": "Brand"},
        )
        st.plotly_chart(fig_spend_brand, use_container_width=True)

    with col2:
        fig_spend_vert = px.pie(
            spend_data.groupby("vertical")["total_spend"].sum().reset_index(),
            names="vertical",
            values="total_spend",
            title="Spend Share by Vertical",
        )
        st.plotly_chart(fig_spend_vert, use_container_width=True)

    fig_heatmap = px.density_heatmap(
        spend_data,
        x="vertical",
        y="brand",
        z="total_spend",
        title="Spend Heatmap: Brand × Vertical",
        color_continuous_scale="Blues",
        labels={"total_spend": "Spend ($)"},
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    monthly_spend = pd.read_sql(
        f"""
        SELECT month, vertical,
               ROUND(SUM(spend_amount), 0) AS total_spend
        FROM advertiser_spend
        WHERE {month_filter} {brand_filter}
        GROUP BY month, vertical
        ORDER BY month
        """,
        conn,
    )
    fig_spend_trend = px.area(
        monthly_spend,
        x="month",
        y="total_spend",
        color="vertical",
        title="Monthly Spend Trend by Vertical",
        labels={"total_spend": "Spend ($)", "month": "Month"},
    )
    st.plotly_chart(fig_spend_trend, use_container_width=True)


# ============================================================
# TAB 3: Pitch-to-Pay
# ============================================================
with tab3:
    st.subheader("Pipeline Funnel & Revenue Leakage")

    funnel_data = pd.read_sql(
        f"""
        SELECT stage,
               SUM(deal_count)              AS total_deals,
               ROUND(SUM(deal_value), 0)    AS total_value,
               ROUND(SUM(revenue_leakage), 0) AS total_leakage
        FROM pitch_to_pay
        WHERE {month_filter} {brand_filter}
        GROUP BY stage
        ORDER BY
            CASE stage
                WHEN 'CRM Opportunity'      THEN 1
                WHEN 'Order Created'        THEN 2
                WHEN 'Campaign Trafficked'  THEN 3
                WHEN 'Delivered'            THEN 4
                WHEN 'Billed'               THEN 5
                WHEN 'Reconciled'           THEN 6
            END
        """,
        conn,
    )

    fig_funnel = px.funnel(
        funnel_data,
        x="total_value",
        y="stage",
        title="Pitch-to-Pay Revenue Funnel",
        labels={"total_value": "Deal Value ($)", "stage": "Stage"},
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        leakage_brand = pd.read_sql(
            f"""
            SELECT brand,
                   ROUND(SUM(revenue_leakage), 0) AS total_leakage
            FROM pitch_to_pay
            WHERE {month_filter} {brand_filter}
            GROUP BY brand
            ORDER BY total_leakage DESC
            """,
            conn,
        )
        fig_leakage = px.bar(
            leakage_brand,
            x="brand",
            y="total_leakage",
            color="brand",
            title="Revenue Leakage by Brand",
            text_auto=".3s",
            labels={"total_leakage": "Leakage ($)", "brand": "Brand"},
        )
        st.plotly_chart(fig_leakage, use_container_width=True)

    with col2:
        stage_leakage = funnel_data[funnel_data["total_leakage"] > 0]
        fig_stage_leak = px.bar(
            stage_leakage,
            x="stage",
            y="total_leakage",
            color="stage",
            title="Leakage by Pipeline Stage",
            text_auto=".3s",
            labels={"total_leakage": "Leakage ($)", "stage": "Stage"},
        )
        st.plotly_chart(fig_stage_leak, use_container_width=True)

    total_crm = funnel_data[funnel_data["stage"] == "CRM Opportunity"]["total_value"].values
    total_rec = funnel_data[funnel_data["stage"] == "Reconciled"]["total_value"].values
    if len(total_crm) and len(total_rec):
        conversion = total_rec[0] / total_crm[0] * 100
        total_leak = funnel_data["total_leakage"].sum()
        c1, c2 = st.columns(2)
        c1.metric("End-to-End Conversion", f"{conversion:.1f}%")
        c2.metric("Total Revenue Leakage", f"${total_leak:,.0f}")

    st.dataframe(
        funnel_data.rename(
            columns={
                "total_deals": "Deals",
                "total_value": "Value ($)",
                "total_leakage": "Leakage ($)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAB 4: Data QA
# ============================================================
with tab4:
    st.subheader("Data Quality & System Health")

    health = pd.read_sql(
        """
        SELECT
            source,
            COUNT(*)                                        AS total_records,
            ROUND(AVG(completeness_pct), 2)                 AS avg_completeness_pct,
            ROUND(AVG(variance_pct), 4)                     AS avg_variance_pct,
            SUM(anomaly_flag)                               AS total_anomalies,
            SUM(
                CASE
                    WHEN (JULIANDAY('now') - JULIANDAY(last_refresh)) * 24 > 24
                    THEN 1 ELSE 0
                END
            )                                               AS stale_feeds
        FROM data_qa_status
        GROUP BY source
        ORDER BY total_anomalies DESC
        """,
        conn,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Anomalies", int(health["total_anomalies"].sum()))
    col2.metric("Avg Completeness", f"{health['avg_completeness_pct'].mean():.1f}%")
    col3.metric("Stale Feeds", int(health["stale_feeds"].sum()))

    st.dataframe(
        health.rename(
            columns={
                "avg_completeness_pct": "Completeness (%)",
                "avg_variance_pct": "Avg Variance (%)",
                "total_anomalies": "Anomalies",
                "stale_feeds": "Stale Feeds",
                "total_records": "Records",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    anomalies = pd.read_sql(
        f"""
        SELECT source, brand, month,
               completeness_pct,
               variance_pct,
               anomaly_flag,
               last_refresh
        FROM data_qa_status
        WHERE anomaly_flag = 1 {brand_filter.replace('AND ', 'AND ', 1)}
        ORDER BY variance_pct DESC
        LIMIT 50
        """,
        conn,
    )

    st.subheader(f"Flagged Anomalies ({len(anomalies)} shown)")

    if not anomalies.empty:
        fig_anom = px.scatter(
            anomalies,
            x="month",
            y="variance_pct",
            color="source",
            symbol="brand",
            size="variance_pct",
            title="Anomaly Scatter: Variance % by Month & Source",
            labels={"variance_pct": "Variance (%)", "month": "Month"},
        )
        st.plotly_chart(fig_anom, use_container_width=True)

        st.dataframe(
            anomalies.rename(
                columns={
                    "completeness_pct": "Completeness (%)",
                    "variance_pct": "Variance (%)",
                    "anomaly_flag": "Anomaly",
                    "last_refresh": "Last Refresh",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No anomalies in the selected filters.")

    stale = pd.read_sql(
        """
        SELECT source, brand, month, last_refresh,
               ROUND((JULIANDAY('now') - JULIANDAY(last_refresh)) * 24, 1) AS hours_stale
        FROM data_qa_status
        WHERE (JULIANDAY('now') - JULIANDAY(last_refresh)) * 24 > 24
        ORDER BY hours_stale DESC
        """,
        conn,
    )

    st.subheader("Stale Data Feeds (> 24 h)")
    if not stale.empty:
        st.dataframe(stale, use_container_width=True, hide_index=True)
    else:
        st.success("All feeds are fresh.")
