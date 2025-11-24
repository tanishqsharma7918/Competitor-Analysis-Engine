from typing import Dict, List, Any
import pandas as pd
import streamlit as st

from backend.llm import call_openai_json  # sync version used here on purpose


# ---------------------------------------------------------
# Streamlit cache for matrix building
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def _cached_matrix_build(features: List[Dict[str, Any]], product_features: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Caches the entire DataFrame build. This avoids recomputing the matrix
    even if the app reruns 10 times.
    """
    return _build_matrix(features, product_features)


# ---------------------------------------------------------
# INTERNAL — NON-CACHED RAW MATRIX BUILDER
# ---------------------------------------------------------
def _build_matrix(features: List[Dict[str, Any]], product_features: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Build the comparison matrix WITHOUT any caching.
    This function is wrapped by the Streamlit cache above.
    """

    # Extract feature names
    feature_names = [f.get("feature_name", "") for f in features]

    # Sort products alphabetically for stable output
    product_names = sorted(product_features.keys())

    # Create matrix dict
    matrix_data = {
        feature_name: [
            1 if feature_name in product_features.get(product, []) else 0
            for product in product_names
        ]
        for feature_name in feature_names
    }

    # Build DataFrame
    df = pd.DataFrame(matrix_data, index=product_names)

    return df


# ---------------------------------------------------------
# PUBLIC FUNCTION — CALLED BY app.py
# ---------------------------------------------------------
def build_comparison_matrix(features: List[Dict[str, Any]], product_features: Dict[str, List[str]]) -> pd.DataFrame:
    """Build and return cached comparison matrix DataFrame."""
    return _cached_matrix_build(features, product_features)


# ---------------------------------------------------------
# CACHING DIFFERENTIATOR ANALYSIS
# ---------------------------------------------------------

@st.cache_data(show_spinner=False)
def _cached_differentiator_llm(messages_tuple: tuple) -> Dict[str, Any]:
    """
    Streamlit cache wrapper for differentiator analysis.
    Uses gpt-4o (stronger model) for best insight quality.
    """
    messages = [{"role": r, "content": c} for r, c in messages_tuple]
    result = call_openai_json(messages, model="gpt-4o")  # STRONG model for insights
    return result


def analyze_differentiators(
    product_name: str,
    features: List[Dict[str, Any]],
    product_features: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Uses LLM to analyze differentiation strategy.
    This used to take 30–90 seconds — now cached to ~0.1 sec.
    """

    # Prepare LLM prompt
    prompt = f"""
You are a competitive strategy expert.

Given these features and coverage, analyze:
1. Which features differentiate {product_name} from its competitors.
2. Which features competitors offer that {product_name} does not.
3. Recommend strategic improvements.

Return ONLY JSON in this format:
{{
    "differentiators": ["..."],
    "gaps": ["..."],
    "recommendations": ["..."]
}}
"""

    messages = [
        {"role": "system", "content": "You are an expert in product differentiation."},
        {"role": "user", "content": prompt},
    ]

    messages_tuple = tuple((m["role"], m["content"]) for m in messages)

    # Cached LLM call
    result_json = _cached_differentiator_llm(messages_tuple)

    # Parse fields safely
    return {
        "differentiators": result_json.get("differentiators", []),
        "gaps": result_json.get("gaps", []),
        "recommendations": result_json.get("recommendations", []),
    }
