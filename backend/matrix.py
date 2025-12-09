from typing import Dict, List, Any
import pandas as pd
import streamlit as st
import json

from backend.llm import call_openai_json


# ---------------------------------------------------------
# Streamlit cache for matrix building
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def _cached_matrix_build(features: List[Dict[str, Any]], product_features: Dict[str, List[str]]) -> pd.DataFrame:
    return _build_matrix(features, product_features)


# ---------------------------------------------------------
# INTERNAL — NON-CACHED RAW MATRIX BUILDER
# ---------------------------------------------------------
def _build_matrix(features: List[Dict[str, Any]], product_features: Dict[str, List[str]]) -> pd.DataFrame:

    feature_names = [f.get("feature_name", "") for f in features]
    product_names = sorted(product_features.keys())

    matrix_data = {
        feature_name: [
            1 if feature_name in product_features.get(product, []) else 0
            for product in product_names
        ]
        for feature_name in feature_names
    }

    df = pd.DataFrame(matrix_data, index=product_names)
    return df


# ---------------------------------------------------------
# PUBLIC FUNCTION — CALLED BY app.py
# ---------------------------------------------------------
def build_comparison_matrix(features: List[Dict[str, Any]], product_features: Dict[str, List[str]]) -> pd.DataFrame:
    return _cached_matrix_build(features, product_features)


# ---------------------------------------------------------
# CACHING DIFFERENTIATOR ANALYSIS (UPGRADED TO GPT-4o)
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def _cached_differentiator_llm(messages_tuple: tuple) -> Dict[str, Any]:
    messages = [{"role": r, "content": c} for r, c in messages_tuple]
    return call_openai_json(messages, model="gpt-4o")


# ---------------------------------------------------------
# COMPETITOR RANKING WITH DEEP REASONING (NEW)
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def _cached_competitor_ranking(messages_tuple: tuple) -> Dict[str, Any]:
    messages = [{"role": r, "content": c} for r, c in messages_tuple]
    return call_openai_json(messages, model="gpt-4o")


def rank_competitors(
    product_name: str,
    competitors: List[Dict[str, Any]],
    features: List[Dict[str, Any]],
    product_features: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Uses GPT-4o deep reasoning to rank competitors by:
    - Similarity to main product
    - Market overlap
    - Feature parity
    - ICP (Ideal Customer Profile) match
    """
    
    prompt = f"""
You are a competitive intelligence expert specializing in market positioning analysis.

Main Product: {product_name}

Competitors:
{json.dumps([{
    'company': c.get('company_name'),
    'product': c.get('product_name'),
    'target_audience': c.get('target_audience'),
    'pricing_tier': c.get('pricing_tier'),
    'market_position': c.get('market_position'),
    'strengths': c.get('key_strengths'),
    'weaknesses': c.get('key_weaknesses')
} for c in competitors], indent=2)}

Features and Coverage:
{json.dumps({
    'all_features': [f['feature_name'] for f in features],
    'product_features': product_features
}, indent=2)}

**Task:**

Rank all competitors by their THREAT LEVEL to {product_name}, considering:
1. Product similarity (features, functionality)
2. Market overlap (target audience, pricing tier)
3. Feature parity (how many features they share)
4. ICP match (how similar their ideal customer is)

For each competitor, provide:
- company_name
- product_name
- rank (1 = highest threat, N = lowest)
- similarity_score (0-100)
- market_overlap_score (0-100)
- feature_parity_score (0-100)
- icp_match_score (0-100)
- overall_threat_score (0-100, weighted average)
- reasoning (2-3 sentence explanation of ranking)

Return ONLY JSON:
{{
    "ranked_competitors": [
        {{
            "company_name": "...",
            "product_name": "...",
            "rank": 1,
            "similarity_score": 85,
            "market_overlap_score": 90,
            "feature_parity_score": 75,
            "icp_match_score": 80,
            "overall_threat_score": 83,
            "reasoning": "..."
        }}
    ]
}}
"""

    messages = [
        {"role": "system", "content": "You are a strategic competitive analyst with deep market insight."},
        {"role": "user", "content": prompt}
    ]

    messages_tuple = tuple((m["role"], m["content"]) for m in messages)
    
    try:
        result = _cached_competitor_ranking(messages_tuple)
        return result
    except Exception as e:
        return {"ranked_competitors": []}


# ---------------------------------------------------------
# ANALYZE DIFFERENTIATORS (UPGRADED TO GPT-4o)
# ---------------------------------------------------------
def analyze_differentiators(
    product_name: str,
    features: List[Dict[str, Any]],
    product_features: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Enhanced differentiator analysis using GPT-4o deep reasoning.
    """

    # 1. Calculate missing capabilities
    all_feature_names = [f["feature_name"] for f in features]
    your_features = set(product_features.get(product_name, []))
    all_features_set = set(all_feature_names)
    missing = sorted(list(all_features_set - your_features))

    # Get feature details for missing items
    feature_details = {f["feature_name"]: f for f in features}

    # 2. Enhanced LLM prompt with deep reasoning
    prompt = f"""
You are a world-class competitive strategy consultant with expertise in product differentiation.

**Context:**

Main Product: {product_name}

All Features in Market:
{json.dumps([{
    'name': f['feature_name'],
    'category': f.get('category', ''),
    'importance': f.get('importance_score', 0),
    'competitive_relevance': f.get('competitive_relevance_score', 0)
} for f in features], indent=2)}

Features {product_name} Currently Has:
{sorted(list(your_features))}

Features {product_name} is Missing:
{missing}

**Tasks:**

1. **Key Differentiators:** Identify 3-5 unique strengths of {product_name} that competitors lack or do poorly.

2. **Missing Capabilities Analysis:** For each missing feature:
   - Explain WHY it matters
   - Rate importance: High / Medium / Low
   - Provide strategic rationale
   - Consider: importance_score, competitive_relevance_score, and market demand

3. **Strategic Recommendations:** Provide 4-6 actionable recommendations:
   - Prioritize what to build next
   - Identify quick wins
   - Highlight long-term investments
   - Suggest positioning strategies

**Use deep reasoning:** Consider market dynamics, user needs, competitive pressure, and strategic value.

Return ONLY JSON in EXACTLY this format:
{{
    "differentiators": [
        {{
            "title": "...",
            "description": "...",
            "competitive_advantage": "..."
        }}
    ],
    "missing_capabilities": [
        {{
            "capability": "...",
            "importance": "High/Medium/Low",
            "rationale": "...",
            "strategic_value": "...",
            "estimated_impact": "High/Medium/Low"
        }}
    ],
    "recommendations": [
        {{
            "title": "...",
            "description": "...",
            "priority": "High/Medium/Low",
            "timeframe": "Short-term (0-3 months) / Mid-term (3-6 months) / Long-term (6+ months)",
            "expected_outcome": "..."
        }}
    ]
}}
"""

    messages = [
        {"role": "system", "content": "You are an expert in product differentiation and competitive strategy with deep market insight."},
        {"role": "user", "content": prompt},
    ]

    messages_tuple = tuple((m["role"], m["content"]) for m in messages)

    llm_json = _cached_differentiator_llm(messages_tuple)

    # 3. Format output for UI compatibility
    differentiators = []
    for diff in llm_json.get("differentiators", []):
        differentiators.append({
            "title": diff.get("title", ""),
            "description": diff.get("description", "")
        })

    missing_capabilities = []
    for cap in llm_json.get("missing_capabilities", []):
        missing_capabilities.append({
            "capability": cap.get("capability", ""),
            "importance": cap.get("importance", "Medium"),
            "rationale": cap.get("rationale", "")
        })

    recommendations = []
    for rec in llm_json.get("recommendations", []):
        recommendations.append({
            "title": rec.get("title", ""),
            "description": rec.get("description", "")
        })

    return {
        "differentiators": differentiators,
        "missing_capabilities": missing_capabilities,
        "recommendations": recommendations
    }
