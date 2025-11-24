from typing import Dict, List, Any
import pandas as pd
import streamlit as st

from backend.llm import call_openai_json  # sync version used here on purpose


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
# CACHING DIFFERENTIATOR ANALYSIS
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def _cached_differentiator_llm(messages_tuple: tuple) -> Dict[str, Any]:
    messages = [{"role": r, "content": c} for r, c in messages_tuple]
    return call_openai_json(messages, model="gpt-4o")


def analyze_differentiators(
    product_name: str,
    features: List[Dict[str, Any]],
    product_features: Dict[str, List[str]]
) -> Dict[str, Any]:

    # Prepare LLM prompt
    prompt = f"""
You are a competitive strategy expert.

Given these features and coverage, analyze:
1. Which features differentiate {product_name} from its competitors.
2. Which features competitors offer that {product_name} does not.
3. Recommend strategic improvements.

Return ONLY JSON in EXACTLY this format:
{{
    "differentiators": [
        {{
            "title": "...",
            "description": "..."
        }}
    ],
    "gaps": [
        {{
            "title": "...",
            "description": "..."
        }}
    ],
    "recommendations": [
        {{
            "title": "...",
            "description": "..."
        }}
    ]
}}
"""

    messages = [
        {"role": "system", "content": "You are an expert in product differentiation."},
        {"role": "user", "content": prompt},
    ]

    messages_tuple = tuple((m["role"], m["content"]) for m in messages)

    result_json = _cached_differentiator_llm(messages_tuple)

    return {
        "differentiators": result_json.get("differentiators", []),
        "gaps": result_json.get("gaps", []),
        "recommendations": result_json.get("recommendations", []),
    }
