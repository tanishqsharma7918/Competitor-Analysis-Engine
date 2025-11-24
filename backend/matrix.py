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

    # ----------------------------------------------
    # 1. REAL missing capability calculation
    # ----------------------------------------------
    all_feature_names = [f["feature_name"] for f in features]

    your_features = set(product_features.get(product_name, []))
    all_features_set = set(all_feature_names)

    missing = sorted(list(all_features_set - your_features))

    missing_capability_objects = [
        {
            "title": feat,
            "description": f"{product_name} does not currently offer '{feat}', which competitors use to deliver value.",
            "importance": "Medium"  # placeholder (LLM upgrades below)
        }
        for feat in missing
    ]

    # ----------------------------------------------
    # 2. Ask LLM to evaluate differentiators & importance
    # ----------------------------------------------
    prompt = f"""
You are a competitive strategy expert.

Here is the feature set:
{all_feature_names}

Here are the features offered by {product_name}:
{list(your_features)}

Here are the features {product_name} is missing:
{missing}

Analyze:

1. Key differentiators of {product_name}.
2. Why the missing features matter.
3. Rate each missing feature with importance: High / Medium / Low.
4. Provide final strategic recommendations.

Return ONLY JSON in EXACTLY this format:

{{
    "differentiators": [
        {{
            "title": "...",
            "description": "..."
        }}
    ],
    "missing_capabilities": [
        {{
            "title": "...",
            "description": "...",
            "importance": "High / Medium / Low"
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

    llm_json = _cached_differentiator_llm(messages_tuple)

    # ----------------------------------------------
    # 3. Combine LLM output + real missing list
    # ----------------------------------------------
    llm_missing = llm_json.get("missing_capabilities", [])

    # Upgrade importance if LLM didn’t rate it
    final_missing = []
    for item in missing_capability_objects:
        llm_item = next((m for m in llm_missing if m["title"] == item["title"]), None)
        if llm_item:
            final_missing.append(llm_item)
        else:
            final_missing.append(item)

    return {
        "differentiators": llm_json.get("differentiators", []),
        "missing_capabilities": final_missing,
        "recommendations": llm_json.get("recommendations", [])
    }
