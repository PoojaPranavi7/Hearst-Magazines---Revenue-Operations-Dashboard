"""
Hearst Revenue Operations Intelligence Dashboard
Single-page Streamlit app.  Run with: streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Hearst Revenue Operations",
    page_icon="📊",
    layout="wide",
)

# ── Imports ────────────────────────────────────────────────────────────────
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

from data.generate_data import get_database_connection
from sql.queries import (
    get_portfolio_kpis,
    get_brand_revenue_by_channel,
    get_monthly_revenue_trend,
    get_advertiser_spend_trends,
    get_concentration_risk,
    get_pitch_to_pay_funnel,
    get_qa_summary,
    get_revenue_reconciliation,
    get_brand_summary_table,
    get_anomaly_log,
)

# ── Global CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Page background ───────────────────────────── */
.stApp { background-color: #F8F9FC; }

/* ── Remove default Streamlit chrome ───────────── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
.block-container {
    padding-top: 1.5rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    max-width: 100%;
}

/* ── Section headers ───────────────────────────── */
.section-header {
    color: #1B3A6B;
    font-weight: 700;
    font-size: 22px;
    border-bottom: 3px solid #2E75B6;
    padding-bottom: 8px;
    margin-top: 36px;
    margin-bottom: 20px;
    font-family: system-ui, -apple-system, sans-serif;
}

/* ── Metric cards ──────────────────────────────── */
.metric-card {
    background: #ffffff;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    text-align: center;
    height: 100%;
}
.metric-label {
    color: #6B7280;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 10px;
    font-family: system-ui, -apple-system, sans-serif;
}
.metric-value {
    color: #1B3A6B;
    font-size: 26px;
    font-weight: 700;
    line-height: 1.2;
    font-family: system-ui, -apple-system, sans-serif;
}
.metric-delta {
    color: #6B7280;
    font-size: 11px;
    margin-top: 7px;
    font-family: system-ui, -apple-system, sans-serif;
}

/* ── Insight cards ─────────────────────────────── */
.insight-card {
    background: #ffffff;
    border-radius: 8px;
    padding: 22px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    height: 100%;
    font-family: system-ui, -apple-system, sans-serif;
}
.insight-icon  { font-size: 26px; margin-bottom: 8px; }
.insight-title { color: #1B3A6B; font-weight: 700; font-size: 15px; margin-bottom: 10px; }
.insight-body  { color: #4B5563; font-size: 13.5px; line-height: 1.65; }
.insight-action-label { font-weight: 600; color: #1B3A6B; }
.insight-action {
    margin-top: 12px;
    padding: 10px 12px;
    border-radius: 6px;
    font-size: 13px;
    color: #374151;
    line-height: 1.5;
    background: #F3F7FF;
}

/* ── Status cards (QA) ─────────────────────────── */
.status-card {
    background: #ffffff;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    font-family: system-ui, -apple-system, sans-serif;
}
.status-card h4 {
    color: #1B3A6B;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 14px;
    margin-top: 0;
}
.status-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 13px;
    padding: 4px 0;
    border-bottom: 1px solid #F3F4F6;
    color: #374151;
}
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-green  { background: #D1FAE5; color: #065F46; }
.badge-yellow { background: #FEF3C7; color: #92400E; }
.badge-red    { background: #FEE2E2; color: #991B1B; }

/* ── Concentration risk box ────────────────────── */
.risk-box {
    background: #FFF3CD;
    border: 1px solid #FFC107;
    border-radius: 8px;
    padding: 16px;
    margin-top: 14px;
    font-family: system-ui, -apple-system, sans-serif;
    font-size: 13px;
    color: #374151;
}
.risk-box strong { color: #92400E; }
.risk-title { font-weight: 700; color: #92400E; margin-bottom: 8px; font-size: 13px; }

/* ── Callout box (Pitch-to-Pay) ────────────────── */
.callout-box {
    background: #EBF3FB;
    border-left: 4px solid #2E75B6;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin-top: 12px;
    font-size: 14px;
    color: #1B3A6B;
    font-family: system-ui, -apple-system, sans-serif;
}

/* ── Divider ───────────────────────────────────── */
.blue-divider {
    border: none;
    border-top: 2px solid #2E75B6;
    margin: 4px 0 20px 0;
}

/* ── Footer ────────────────────────────────────── */
.footer-bar {
    border-top: 1px solid #D1D5DB;
    padding-top: 14px;
    margin-top: 48px;
    color: #9CA3AF;
    font-size: 12px;
    text-align: center;
    font-family: system-ui, -apple-system, sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ── Data load ──────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Initialising database…")
def load_db():
    return get_database_connection()

conn = load_db()

# ── Plotly defaults ────────────────────────────────────────────────────────
CHANNEL_COLORS = {
    "Direct-Sold":                "#1B3A6B",
    "Programmatic Guaranteed":    "#2E75B6",
    "Private Marketplace":        "#17B8A8",
    "Open Auction":               "#90CAF9",
}

def clean_fig(fig, show_grid=False):
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="system-ui, -apple-system, sans-serif",
        font_color="#374151",
        margin=dict(l=16, r=16, t=40, b=16),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showgrid=show_grid, gridcolor="#F3F4F6", linecolor="#E5E7EB")
    fig.update_yaxes(showgrid=show_grid, gridcolor="#F3F4F6", linecolor="#E5E7EB")
    return fig


# ══════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([2, 1])
with col_left:
    st.markdown(
        '<div style="font-family:system-ui,-apple-system,sans-serif;">'
        '<span style="color:#1B3A6B;font-size:26px;font-weight:800;">Hearst Magazines</span>'
        '<br>'
        '<span style="color:#6B7280;font-size:15px;font-weight:400;">'
        'Revenue Operations Intelligence Dashboard</span>'
        '</div>',
        unsafe_allow_html=True,
    )
with col_right:
    st.markdown(
        f'<div style="text-align:right;font-family:system-ui,-apple-system,sans-serif;'
        f'padding-top:6px;">'
        f'<span style="color:#374151;font-size:13px;">Data as of: '
        f'<strong>{date.today().strftime("%B %d, %Y")}</strong></span><br>'
        f'<span style="color:#6B7280;font-size:12px;">Portfolio: 6 Brands | FY2024</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown('<hr class="blue-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# SECTION 1 — PORTFOLIO KPIs
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Portfolio Performance — FY2024</div>',
            unsafe_allow_html=True)

kpis = get_portfolio_kpis(conn).iloc[0]

total_rev   = kpis["total_revenue"]
fill_rate   = kpis["portfolio_fill_rate"]
avg_cpm     = kpis["weighted_avg_cpm"]
sold_imps   = kpis["total_sold_impressions"]
avail_imps  = kpis["total_available_impressions"]

kpi_defs = [
    {
        "label": "Total Revenue",
        "value": f"${total_rev / 1_000_000:.1f}M",
        "delta": "Q4 peak: +24% vs Q2",
    },
    {
        "label": "Portfolio Fill Rate",
        "value": f"{fill_rate:.1f}%",
        "delta": "Direct-Sold leads at ~90%",
    },
    {
        "label": "Weighted Avg CPM",
        "value": f"${avg_cpm:.2f}",
        "delta": "Fashion brands: +20% premium",
    },
    {
        "label": "Impressions Sold",
        "value": f"{sold_imps / 1_000_000_000:.2f}B",
        "delta": "Across 4 channels",
    },
    {
        "label": "Available Inventory",
        "value": f"{avail_imps / 1_000_000_000:.2f}B",
        "delta": "FY2024 total pool",
    },
]

kpi_cols = st.columns(5)
for col, kpi in zip(kpi_cols, kpi_defs):
    with col:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">{kpi["label"]}</div>'
            f'<div class="metric-value">{kpi["value"]}</div>'
            f'<div class="metric-delta">{kpi["delta"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# Monthly revenue trend — clean navy line, no gridlines
trend_df = get_monthly_revenue_trend(conn)
fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=trend_df["month"],
    y=trend_df["total_revenue"],
    mode="lines+markers",
    line=dict(color="#1B3A6B", width=3),
    marker=dict(color="#2E75B6", size=8, line=dict(color="white", width=2)),
    fill="tozeroy",
    fillcolor="rgba(46,117,182,0.08)",
    hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
))
fig_trend.update_layout(
    title=dict(text="Monthly Revenue Trend — FY2024", font=dict(size=15, color="#1B3A6B")),
    xaxis_title=None,
    yaxis_title="Revenue ($)",
    plot_bgcolor="white",
    paper_bgcolor="white",
    font_family="system-ui, -apple-system, sans-serif",
    margin=dict(l=16, r=16, t=48, b=16),
    yaxis=dict(showgrid=False, zeroline=False),
    xaxis=dict(showgrid=False, linecolor="#E5E7EB"),
    height=320,
)
st.plotly_chart(fig_trend, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
# SECTION 2 — BRAND & INVENTORY PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Brand Performance by Channel</div>',
            unsafe_allow_html=True)

brand_channel_df = get_brand_revenue_by_channel(conn)

fig_grouped = px.bar(
    brand_channel_df,
    x="brand",
    y="total_revenue",
    color="channel",
    barmode="group",
    title="Revenue by Brand and Channel",
    labels={"total_revenue": "Revenue ($)", "brand": "Brand", "channel": "Channel"},
    color_discrete_map=CHANNEL_COLORS,
    text_auto=".3s",
)
fig_grouped = clean_fig(fig_grouped, show_grid=True)
fig_grouped.update_traces(textfont_size=10)
fig_grouped.update_layout(
    title_font=dict(size=15, color="#1B3A6B"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=400,
)
st.plotly_chart(fig_grouped, use_container_width=True)

# Summary table with conditional fill-rate formatting
summary_df = get_brand_summary_table(conn)

display_df = summary_df.rename(columns={
    "brand":         "Brand",
    "total_revenue": "Total Revenue ($)",
    "fill_rate":     "Fill Rate (%)",
    "avg_cpm":       "Avg CPM ($)",
    "top_channel":   "Top Channel",
})
display_df["Total Revenue ($)"] = display_df["Total Revenue ($)"].apply(
    lambda v: f"${v:,.0f}"
)
display_df["Avg CPM ($)"] = display_df["Avg CPM ($)"].apply(lambda v: f"${v:.2f}")


def _color_fill(val):
    try:
        v = float(val)
    except (ValueError, TypeError):
        return ""
    if v > 85:
        return "background-color: #D1FAE5; color: #065F46"
    if v >= 70:
        return "background-color: #FEF3C7; color: #92400E"
    return "background-color: #FEE2E2; color: #991B1B"


styled = display_df.style.applymap(_color_fill, subset=["Fill Rate (%)"])
st.dataframe(styled, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
# SECTION 3 — ADVERTISER SPEND TRENDS
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="section-header">'
    'Advertiser Spend Analysis — Vertical Trends &amp; Concentration Risk'
    '</div>',
    unsafe_allow_html=True,
)

spend_trends_df  = get_advertiser_spend_trends(conn)
concentration_df = get_concentration_risk(conn)

col_left, col_right = st.columns([3, 2])

with col_left:
    fig_spend_trend = px.line(
        spend_trends_df,
        x="month",
        y="total_spend",
        color="vertical",
        title="Monthly Spend by Advertiser Vertical",
        labels={"total_spend": "Spend ($)", "month": "Month", "vertical": "Vertical"},
        markers=True,
    )
    fig_spend_trend = clean_fig(fig_spend_trend, show_grid=True)
    fig_spend_trend.update_layout(
        title_font=dict(size=14, color="#1B3A6B"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=360,
    )
    st.plotly_chart(fig_spend_trend, use_container_width=True)

with col_right:
    annual_vert = (
        spend_trends_df
        .groupby("vertical", as_index=False)["total_spend"]
        .sum()
        .sort_values("total_spend", ascending=False)
    )
    fig_vert_bar = px.bar(
        annual_vert,
        x="total_spend",
        y="vertical",
        orientation="h",
        title="Annual Spend by Vertical",
        labels={"total_spend": "Spend ($)", "vertical": "Vertical"},
        color="total_spend",
        color_continuous_scale=["#90CAF9", "#1B3A6B"],
        text_auto=".3s",
    )
    fig_vert_bar = clean_fig(fig_vert_bar)
    fig_vert_bar.update_layout(
        title_font=dict(size=14, color="#1B3A6B"),
        coloraxis_showscale=False,
        height=260,
    )
    st.plotly_chart(fig_vert_bar, use_container_width=True)

    # Concentration Risk Alert box
    if not concentration_df.empty:
        risk_items_html = "".join(
            f'<div style="margin-bottom:6px;">'
            f'<strong>{row["brand"]}</strong> — '
            f'{row["top_vertical_1"]} + {row["top_vertical_2"]}: '
            f'<strong>{row["top2_pct"]:.1f}%</strong> of spend'
            f'</div>'
            for _, row in concentration_df.iterrows()
        )
        st.markdown(
            f'<div class="risk-box">'
            f'<div class="risk-title">⚠ Concentration Risk Alert</div>'
            f'{risk_items_html}'
            f'<div style="color:#92400E;font-size:12px;margin-top:8px;">'
            f'Top 2 verticals exceed 60% of brand annual spend.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.success("No concentration risk detected across the portfolio.")


# ══════════════════════════════════════════════════════════════════════════
# SECTION 4 — PITCH-TO-PAY PIPELINE
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="section-header">'
    'Pitch-to-Pay Lifecycle — Deal Progression &amp; Revenue Leakage'
    '</div>',
    unsafe_allow_html=True,
)

funnel_df = get_pitch_to_pay_funnel(conn)

# Horizontal funnel chart
fig_funnel = go.Figure(go.Funnel(
    y=funnel_df["stage"],
    x=funnel_df["total_value"],
    orientation="h",
    textposition="inside",
    textinfo="value+percent initial",
    marker=dict(
        color=["#1B3A6B", "#2355A0", "#2E75B6", "#3A8FCC", "#17B8A8", "#0D9488"],
        line=dict(width=1, color="white"),
    ),
    connector=dict(line=dict(color="#CBD5E1", dash="dot", width=1)),
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Deal Value: $%{x:,.0f}<br>"
        "<extra></extra>"
    ),
))
fig_funnel.update_layout(
    title=dict(
        text="Pitch-to-Pay Revenue Funnel — FY2024",
        font=dict(size=15, color="#1B3A6B"),
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    font_family="system-ui, -apple-system, sans-serif",
    margin=dict(l=16, r=16, t=48, b=16),
    height=360,
)
st.plotly_chart(fig_funnel, use_container_width=True)

# Revenue Leakage Analysis table
stage_order = [
    "CRM Opportunity", "Order Created", "Campaign Trafficked",
    "Delivered", "Billed", "Reconciled",
]
funnel_df = funnel_df.set_index("stage").reindex(stage_order).reset_index()

leakage_rows = []
for i in range(1, len(funnel_df)):
    prev = funnel_df.iloc[i - 1]
    curr = funnel_df.iloc[i]
    deals_lost = int(prev["total_deals"] - curr["total_deals"])
    value_lost = prev["total_value"] - curr["total_value"]
    leakage_pct = (value_lost / prev["total_value"] * 100) if prev["total_value"] else 0
    leakage_rows.append({
        "Stage Transition": f"{prev['stage']}  →  {curr['stage']}",
        "Deals Lost": deals_lost,
        "Value Lost ($M)": round(value_lost / 1_000_000, 2),
        "Leakage %": round(leakage_pct, 2),
    })

leakage_table = pd.DataFrame(leakage_rows)
max_leakage_idx = leakage_table["Value Lost ($M)"].idxmax()
worst_stage = leakage_table.loc[max_leakage_idx, "Stage Transition"].split("→")[0].strip()
total_leakage_m = leakage_table["Value Lost ($M)"].sum()


def _highlight_max_leakage(row):
    if row.name == max_leakage_idx:
        return ["background-color: #FEE2E2; color: #991B1B"] * len(row)
    return [""] * len(row)


styled_leakage = leakage_table.style.apply(_highlight_max_leakage, axis=1)
st.dataframe(styled_leakage, use_container_width=True, hide_index=True)

st.markdown(
    f'<div class="callout-box">'
    f'<strong>Total estimated revenue leakage: ${total_leakage_m:.1f}M across FY2024</strong> — '
    f'primary bottleneck at the <strong>{worst_stage}</strong> stage.'
    f'</div>',
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════
# SECTION 5 — DATA QA & PIPELINE HEALTH
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="section-header">'
    'Data Quality Monitor — Salesforce | AdPoint | GAM'
    '</div>',
    unsafe_allow_html=True,
)

qa_df   = get_qa_summary(conn)
recon_df = get_revenue_reconciliation(conn)
anom_df  = get_anomaly_log(conn)

# ── Three status cards ─────────────────────────────────────────────────────
qa_cols = st.columns(3)

for col, (_, row) in zip(qa_cols, qa_df.iterrows()):
    completeness = row["avg_completeness_pct"]
    anomalies    = int(row["anomalies_detected"])
    variance     = row["avg_variance_pct"]
    hours_stale  = row["hours_since_last_refresh"]

    # Completeness badge
    if completeness >= 95:
        comp_badge = '<span class="badge badge-green">✓ {:.1f}%</span>'.format(completeness)
    elif completeness >= 90:
        comp_badge = '<span class="badge badge-yellow">⚠ {:.1f}%</span>'.format(completeness)
    else:
        comp_badge = '<span class="badge badge-red">✗ {:.1f}%</span>'.format(completeness)

    # Anomaly badge
    if anomalies == 0:
        anom_badge = '<span class="badge badge-green">0 anomalies</span>'
    else:
        anom_badge = '<span class="badge badge-red">{} anomalies</span>'.format(anomalies)

    # Freshness badge
    if hours_stale < 24:
        fresh_badge = '<span class="badge badge-green">{:.1f}h ago</span>'.format(hours_stale)
    else:
        fresh_badge = '<span class="badge badge-red">{:.1f}h ago ⚠</span>'.format(hours_stale)

    # Overall status
    if completeness >= 95 and anomalies == 0 and hours_stale < 24:
        status_badge = '<span class="badge badge-green" style="font-size:13px;padding:4px 14px;">HEALTHY</span>'
    elif completeness < 90 or hours_stale > 48:
        status_badge = '<span class="badge badge-red" style="font-size:13px;padding:4px 14px;">CRITICAL</span>'
    else:
        status_badge = '<span class="badge badge-yellow" style="font-size:13px;padding:4px 14px;">WARNING</span>'

    with col:
        st.markdown(
            f'<div class="status-card">'
            f'<h4>{row["source"]}</h4>'
            f'<div class="status-row">'
            f'<span>Completeness</span>{comp_badge}</div>'
            f'<div class="status-row">'
            f'<span>Anomalies detected</span>{anom_badge}</div>'
            f'<div class="status-row">'
            f'<span>Avg revenue variance</span>'
            f'<span style="font-weight:600;">{variance:.3f}%</span></div>'
            f'<div class="status-row">'
            f'<span>Last refresh</span>{fresh_badge}</div>'
            f'<div style="margin-top:14px;text-align:center;">{status_badge}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Revenue Reconciliation table ───────────────────────────────────────────
st.markdown(
    '<div style="font-weight:600;color:#1B3A6B;font-size:15px;margin-bottom:8px;">'
    'Revenue Reconciliation — Cross-System Comparison</div>',
    unsafe_allow_html=True,
)

recon_display = recon_df.copy()
for col_name in ["revenue_salesforce", "revenue_adpoint", "revenue_gam"]:
    recon_display[col_name] = recon_display[col_name].apply(lambda v: f"${v:,.0f}")
recon_display = recon_display.rename(columns={
    "month":                "Month",
    "revenue_salesforce":   "Salesforce ($)",
    "revenue_adpoint":      "AdPoint ($)",
    "revenue_gam":          "GAM ($)",
    "reconciliation_gap":   "Variance (%)",
})


def _highlight_recon(row):
    try:
        gap = float(str(row["Variance (%)"]).replace("%", ""))
    except (ValueError, TypeError):
        return [""] * len(row)
    if gap > 3:
        return ["background-color: #FEE2E2; color: #991B1B"] * len(row)
    return [""] * len(row)


st.dataframe(
    recon_display.style.apply(_highlight_recon, axis=1),
    use_container_width=True,
    hide_index=True,
)
st.markdown(
    '<div style="font-size:12px;color:#6B7280;margin-top:4px;">'
    '⚠ Reconciliation gaps &gt;3% trigger Finance review workflow.</div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Anomaly log ────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="font-weight:600;color:#1B3A6B;font-size:15px;margin-bottom:8px;">'
    f'Anomaly Log ({len(anom_df)} records)</div>',
    unsafe_allow_html=True,
)


def _highlight_anomaly_row(row):
    if row["status"] == "Open":
        return ["background-color: #FFF5F5; color: #374151"] * len(row)
    return [""] * len(row)


anom_display = anom_df.rename(columns={
    "source":           "Source",
    "brand":            "Brand",
    "month":            "Month",
    "issue_type":       "Issue Type",
    "variance_pct":     "Variance (%)",
    "completeness_pct": "Completeness (%)",
    "status":           "Status",
})
st.dataframe(
    anom_display.style.apply(_highlight_anomaly_row, axis=1),
    use_container_width=True,
    hide_index=True,
)


# ══════════════════════════════════════════════════════════════════════════
# SECTION 6 — KEY INSIGHTS
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="section-header">Key Insights &amp; Recommended Actions</div>',
    unsafe_allow_html=True,
)

INSIGHTS = [
    {
        "icon": "📈",
        "border_color": "#28A745",
        "action_bg": "#F0FFF4",
        "title": "Fashion Inventory Yield Gap",
        "body": (
            "Harper's BAZAAR and ELLE are generating programmatic CPMs 18–22% above "
            "the portfolio average on fashion and beauty placements, but floor prices "
            "on these placements are set at the portfolio median. This represents an "
            "untapped yield opportunity on Hearst's highest-value inventory."
        ),
        "action": (
            "Test a 15% floor price increase on fashion and beauty placements across ELLE "
            "and Harper's BAZAAR. Based on current impression volumes, this could generate "
            "an estimated $1.2M–$1.8M in incremental annual revenue without reducing fill "
            "rates materially."
        ),
    },
    {
        "icon": "⚠️",
        "border_color": "#FD7E14",
        "action_bg": "#FFF8F0",
        "title": "Advertiser Concentration Risk — Cosmopolitan & ELLE",
        "body": (
            "Beauty and Fashion verticals account for over 68% of combined revenue on "
            "Cosmopolitan and ELLE. This concentration creates revenue vulnerability if "
            "either vertical reduces spend — a pattern seen in Q2 when beauty budgets "
            "contracted seasonally."
        ),
        "action": (
            "Prioritize Sales outreach to Finance, Technology, and Retail advertisers for "
            "Cosmopolitan and ELLE inventory packages. Diversifying to 4+ verticals above "
            "15% share each would reduce concentration risk materially."
        ),
    },
    {
        "icon": "💡",
        "border_color": "#28A745",
        "action_bg": "#F0FFF4",
        "title": "Pitch-to-Pay Bottleneck Costing $2.1M Annually",
        "body": (
            "The largest revenue leakage point in the deal lifecycle is at the "
            "Billed-to-Reconciled stage, where billing discrepancies between AdPoint and "
            "GAM delivery actuals are causing delayed or lost revenue recognition. This is "
            "a data and process issue, not a sales issue."
        ),
        "action": (
            "Implement automated three-way reconciliation between Salesforce, AdPoint, and "
            "GAM at deal close. Automated reconciliation would flag discrepancies within 2 "
            "hours rather than at month-end, recovering an estimated $2.1M in delayed "
            "revenue annually."
        ),
    },
]

insight_cols = st.columns(3)
for col, ins in zip(insight_cols, INSIGHTS):
    with col:
        st.markdown(
            f'<div class="insight-card" style="border-left:4px solid {ins["border_color"]};">'
            f'<div class="insight-icon">{ins["icon"]}</div>'
            f'<div class="insight-title">{ins["title"]}</div>'
            f'<div class="insight-body">{ins["body"]}</div>'
            f'<div class="insight-action" style="background:{ins["action_bg"]};">'
            f'<span class="insight-action-label">Recommended Action: </span>'
            f'{ins["action"]}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="footer-bar">'
    'Built by Pooja Pranavi Nalamothu &nbsp;|&nbsp; Revenue Operations Portfolio Project'
    ' &nbsp;|&nbsp; '
    'Data: Synthetic dataset grounded in IAB benchmark CPMs and Hearst public media kit'
    ' audience figures'
    ' &nbsp;|&nbsp; '
    'Built with Python, SQL, Streamlit, Plotly'
    '</div>',
    unsafe_allow_html=True,
)
