import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Any
import numpy as np


def create_feature_coverage_heatmap(matrix_df: pd.DataFrame) -> go.Figure:
    products = [col for col in matrix_df.columns if col != 'Feature']
    features = matrix_df['Feature'].tolist()
    
    z_data = []
    for _, row in matrix_df.iterrows():
        row_data = []
        for product in products:
            value = row[product]
            row_data.append(1 if value == "✓" else 0)
        z_data.append(row_data)
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=products,
        y=features,
        colorscale=[[0, '#FFC7CE'], [1, '#C6EFCE']],
        showscale=False,
        text=[[row[product] for product in products] for _, row in matrix_df.iterrows()],
        texttemplate='%{text}',
        textfont={"size": 14, "color": "black"},
        hovertemplate='<b>%{y}</b><br>%{x}: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Feature Coverage Heatmap",
        xaxis_title="Products",
        yaxis_title="Features",
        height=max(400, len(features) * 25),
        font=dict(size=12),
        margin=dict(l=200, r=20, t=60, b=100),
        xaxis={'side': 'bottom'}
    )
    
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_feature_radar_chart(
    product_name: str,
    competitors: List[Dict[str, Any]],
    product_features: Dict[str, List[str]],
    features: List[Dict[str, Any]]
) -> go.Figure:
    categories = list(set([f.get('category', 'General') for f in features]))
    
    data_traces = []
    
    for product, feature_list in list(product_features.items())[:6]:
        category_counts = {cat: 0 for cat in categories}
        total_per_category = {cat: 0 for cat in categories}
        
        for feat in features:
            cat = feat.get('category', 'General')
            total_per_category[cat] += 1
            if feat['feature_name'] in feature_list:
                category_counts[cat] += 1
        
        percentages = [
            (category_counts[cat] / total_per_category[cat] * 100) if total_per_category[cat] > 0 else 0
            for cat in categories
        ]
        
        is_main_product = product == product_name
        
        data_traces.append(go.Scatterpolar(
            r=percentages,
            theta=categories,
            fill='toself',
            name=product,
            line=dict(width=3 if is_main_product else 2),
            opacity=0.8 if is_main_product else 0.5
        ))
    
    fig = go.Figure(data=data_traces)
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="Feature Coverage by Category (%)",
        showlegend=True,
        height=500,
        font=dict(size=12)
    )
    
    return fig


def create_market_positioning_chart(
    product_name: str,
    competitors: List[Dict[str, Any]],
    product_features: Dict[str, List[str]]
) -> go.Figure:
    market_position_scores = {
        "Market Leader": 5,
        "Challenger": 4,
        "Established Player": 3,
        "Niche Player": 2,
        "Emerging": 1
    }
    
    data = []
    for product, features in product_features.items():
        matching_comp = next((c for c in competitors if c['product_name'] == product), None)
        
        if matching_comp:
            position = matching_comp.get('market_position', 'Niche Player')
        else:
            position = 'Established Player'
        
        data.append({
            'product': product,
            'feature_count': len(features),
            'market_score': market_position_scores.get(position, 3),
            'is_main': product == product_name,
            'position': position
        })
    
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    
    for is_main in [False, True]:
        subset = df[df['is_main'] == is_main]
        fig.add_trace(go.Scatter(
            x=subset['feature_count'],
            y=subset['market_score'],
            mode='markers+text',
            name='Your Product' if is_main else 'Competitors',
            text=subset['product'],
            textposition='top center',
            marker=dict(
                size=20 if is_main else 15,
                color='#366092' if is_main else '#FF6B6B',
                line=dict(width=2, color='white')
            ),
            hovertemplate='<b>%{text}</b><br>Features: %{x}<br>Position: %{customdata}<extra></extra>',
            customdata=subset['position']
        ))
    
    fig.update_layout(
        title="Market Positioning: Feature Count vs Market Position",
        xaxis_title="Number of Features",
        yaxis_title="Market Position Score",
        yaxis=dict(
            tickvals=[1, 2, 3, 4, 5],
            ticktext=['Emerging', 'Niche Player', 'Established', 'Challenger', 'Market Leader']
        ),
        height=500,
        showlegend=True,
        font=dict(size=12),
        hovermode='closest'
    )
    
    return fig


def create_feature_category_breakdown(features: List[Dict[str, Any]]) -> go.Figure:
    categories = {}
    for feat in features:
        cat = feat.get('category', 'General')
        categories[cat] = categories.get(cat, 0) + 1
    
    fig = go.Figure(data=[go.Pie(
        labels=list(categories.keys()),
        values=list(categories.values()),
        hole=0.4,
        marker=dict(colors=px.colors.qualitative.Set3),
        textinfo='label+percent',
        textfont=dict(size=12)
    )])
    
    fig.update_layout(
        title="Feature Distribution by Category",
        height=400,
        showlegend=True,
        font=dict(size=12)
    )
    
    return fig


def create_competitor_feature_comparison_bar(
    product_features: Dict[str, List[str]]
) -> go.Figure:
    products = list(product_features.keys())
    feature_counts = [len(features) for features in product_features.values()]
    
    fig = go.Figure(data=[
        go.Bar(
            x=products,
            y=feature_counts,
            text=feature_counts,
            textposition='outside',
            marker=dict(
                color=feature_counts,
                colorscale='Blues',
                showscale=False
            )
        )
    ])
    
    fig.update_layout(
        title="Total Features per Product",
        xaxis_title="Products",
        yaxis_title="Number of Features",
        height=400,
        font=dict(size=12),
        xaxis_tickangle=-45
    )
    
    return fig
