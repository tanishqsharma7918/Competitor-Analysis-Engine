import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Any
import numpy as np


# ============================================================
# HEATMAP (fixed version for your matrix format)
# ============================================================
def create_feature_coverage_heatmap(matrix_df: pd.DataFrame) -> go.Figure:
    """
    matrix_df:
        index = products
        columns = features
        values = 1/0
    """

    df = matrix_df.copy()

    products = df.index.tolist()
    features = df.columns.tolist()

    # Convert 1/0 values into ✓/✗ for hover/text
    text_data = df.replace({1: "✓", 0: "✗"}).values.tolist()

    fig = go.Figure(
        data=go.Heatmap(
            z=df.values,
            x=features,
            y=products,
            colorscale=[[0, '#FFC7CE'], [1, '#C6EFCE']],
            showscale=False,
            text=text_data,
            texttemplate='%{text}',
            hovertemplate='<b>%{y}</b><br>%{x}: %{text}<extra></extra>'
        )
    )

    fig.update_layout(
        title="Feature Coverage Heatmap",
        xaxis_title="Features",
        yaxis_title="Products",
        height=max(450, len(products) * 35),
        font=dict(size=12),
        margin=dict(l=80, r=20, t=60, b=120),
    )
    fig.update_xaxes(tickangle=-45)
    return fig


# ============================================================
# RADAR CHART (optimized)
# ============================================================
def create_feature_radar_chart(
    product_name: str,
    competitors: List[Dict[str, Any]],
    product_features: Dict[str, List[str]],
    features: List[Dict[str, Any]]
) -> go.Figure:

    categories = sorted(list(set([f.get('category', 'General') for f in features])))

    fig = go.Figure()

    # Maximum 6 products for readability
    for product, feature_list in list(product_features.items())[:6]:

        counts = {cat: 0 for cat in categories}
        totals = {cat: 0 for cat in categories}

        for feat in features:
            cat = feat.get('category', 'General')
            totals[cat] += 1
            if feat['feature_name'] in feature_list:
                counts[cat] += 1

        percentages = [
            (counts[c] / totals[c] * 100) if totals[c] > 0 else 0
            for c in categories
        ]

        is_main = (product == product_name)

        fig.add_trace(go.Scatterpolar(
            r=percentages,
            theta=categories,
            fill='toself',
            name=product,
            line=dict(width=3 if is_main else 1.7),
            opacity=0.85 if is_main else 0.55
        ))

    fig.update_layout(
        title="Feature Coverage by Category (%)",
        polar=dict(radialaxis=dict(range=[0, 100], visible=True)),
        height=500,
        showlegend=True,
    )

    return fig


# ============================================================
# Market positioning chart (unchanged, already correct)
# ============================================================
def create_market_positioning_chart(
    product_name: str,
    competitors: List[Dict[str, Any]],
    product_features: Dict[str, List[str]]
) -> go.Figure:

    scores = {
        "Market Leader": 5,
        "Challenger": 4,
        "Established Player": 3,
        "Niche Player": 2,
        "Emerging": 1
    }

    rows = []
    for product, feats in product_features.items():
        comp = next((c for c in competitors if c['product_name'] == product), None)
        position = comp.get('market_position', 'Established Player') if comp else 'Established Player'
        rows.append({
            "product": product,
            "feature_count": len(feats),
            "market_score": scores.get(position, 3),
            "position": position,
            "is_main": product == product_name
        })

    df = pd.DataFrame(rows)

    fig = go.Figure()

    # competitors
    subset = df[df["is_main"] == False]
    fig.add_trace(go.Scatter(
        x=subset["feature_count"],
        y=subset["market_score"],
        mode="markers+text",
        name="Competitors",
        text=subset["product"],
        textposition="top center",
        marker=dict(size=15, color="#FF6B6B", line=dict(width=1)),
        customdata=subset["position"],
        hovertemplate="<b>%{text}</b><br>Features: %{x}<br>Position: %{customdata}<extra></extra>"
    ))

    # main product
    subset = df[df["is_main"] == True]
    fig.add_trace(go.Scatter(
        x=subset["feature_count"],
        y=subset["market_score"],
        mode="markers+text",
        name="Your Product",
        text=subset["product"],
        textposition="top center",
        marker=dict(size=22, color="#366092", line=dict(width=2, color="white")),
        customdata=subset["position"],
        hovertemplate="<b>%{text}</b><br>Features: %{x}<br>Position: %{customdata}<extra></extra>"
    ))

    fig.update_layout(
        title="Market Positioning",
        xaxis_title="Number of Features",
        yaxis_title="Market Position Score",
        height=450,
        hovermode="closest",
        yaxis=dict(
            tickvals=[1, 2, 3, 4, 5],
            ticktext=["Emerging", "Niche", "Established", "Challenger", "Market Leader"]
        )
    )

    return fig


# ============================================================
# Pie chart
# ============================================================
def create_feature_category_breakdown(features: List[Dict[str, Any]]) -> go.Figure:
    cats = {}
    for feat in features:
        cat = feat.get("category", "General")
        cats[cat] = cats.get(cat, 0) + 1

    fig = go.Figure(go.Pie(
        labels=list(cats.keys()),
        values=list(cats.values()),
        hole=0.45,
        textinfo="label+percent",
    ))

    fig.update_layout(
        title="Feature Distribution by Category",
        height=420
    )

    return fig


# ============================================================
# Bar chart
# ============================================================
def create_competitor_feature_comparison_bar(product_features: Dict[str, List[str]]) -> go.Figure:
    products = list(product_features.keys())
    counts = [len(v) for v in product_features.values()]

    fig = go.Figure(go.Bar(
        x=products,
        y=counts,
        text=counts,
        textposition="outside",
        marker=dict(color=counts, colorscale="Blues", showscale=False)
    ))

    fig.update_layout(
        title="Total Features per Product",
        xaxis_title="Products",
        yaxis_title="Feature Count",
        xaxis_tickangle=-35,
        height=420
    )

    return fig
