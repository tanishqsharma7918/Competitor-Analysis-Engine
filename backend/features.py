from typing import List, Dict, Any
import streamlit as st
import asyncio

from backend.llm import call_openai_json_async, AgentLogger
from backend.cache import get_cached_features, cache_features


# ---------------------------------------------------------
# Stable Cache Key Helper
# ---------------------------------------------------------
def _feature_cache_key(product_name: str, description: str, competitor_names: List[str]) -> str:
    """
    Stable cache key that does NOT depend on LLM-generated competitor descriptions.
    """
    competitors_joined = "|".join(sorted([c.lower().strip() for c in competitor_names]))
    return f"{product_name.strip().lower()}|{description.strip().lower()}|{competitors_joined}"


# ---------------------------------------------------------
# Streamlit Cache Wrapper (sync wrapper for async LLM call)
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def _cached_llm_feature_call(messages_tuple: tuple) -> Dict[str, Any]:
    """
    Streamlit requires cache functions to be sync.
    So we run the async LLM call inside asyncio.run().
    """
    messages = [{"role": r, "content": c} for r, c in messages_tuple]
    result = asyncio.run(call_openai_json_async(messages, model="gpt-4o-mini"))
    return result


# ---------------------------------------------------------
# ASYNC FEATURE EXTRACTION
# ---------------------------------------------------------
async def extract_features(
    product_name: str,
    competitors: List[Dict[str, Any]],
    description: str = "",
    logger: AgentLogger = None,
    use_cache: bool = True
) -> Dict[str, Any]:

    # ------------------------------------------
    # 1. Build stable cache key
    # ------------------------------------------
    competitor_names = [c.get("product_name", "") for c in competitors]
    cache_key = _feature_cache_key(product_name, description, competitor_names)

    # ------------------------------------------
    # 2. Check local (persistent) cache
    # ------------------------------------------
    if use_cache:
        cached = get_cached_features(product_name)
        if cached:
            if logger:
                logger.log_thought(f"[CACHE HIT] Features for '{product_name}' loaded instantly.")
                logger.log_observation(f"{len(cached['features'])} features pulled from cache.")
            return cached

    # ------------------------------------------
    # 3. Prepare LLM prompt
    # ------------------------------------------
    if logger:
        logger.log_thought("Extracting features via LLM...")
        logger.log_action(f"Analyzing product: {product_name} and {len(competitors)} competitors.")

    competitor_list = "\n".join(
        [
            f"- {c.get('company_name', 'Unknown')}: {c.get('product_name', 'Unknown')} - {c.get('description', '')}"
            for c in competitors
        ]
    )

    prompt = f"""
You are a senior product analyst. Read the following:

Main Product: {product_name}
Description: {description}

Competitors:
{competitor_list}

Your tasks:
1. Identify EXACTLY 7 key features important for comparison across all these products.
2. Each feature must include:
   - feature_name
   - description
   - category (e.g., Core Functionality, Integrations, Pricing, Support, UX, etc.)
3. For each product, list which features they have.

Return ONLY JSON in this exact format:
{{
    "features": [
        {{
            "feature_name": "...",
            "description": "...",
            "category": "..."
        }}
    ],
    "product_features": {{
        "{product_name}": ["feature1", "feature2", ...],
        "competitor product": ["feature1", ...],
        ...
    }}
}}
    """

    messages = [
        {"role": "system", "content": "You are an expert product feature analyst."},
        {"role": "user", "content": prompt}
    ]

    messages_tuple = tuple((m["role"], m["content"]) for m in messages)

    # ------------------------------------------
    # 4. Call the cached LLM wrapper
    # ------------------------------------------
    try:
        json_str = _cached_llm_feature_call(messages_tuple)
        features = json_str.get("features", [])
        product_features = json_str.get("product_features", {})

    except Exception as e:
        if logger:
            logger.log_observation(f"ERROR during feature extraction: {str(e)}")
        raise Exception(f"Feature extraction failed: {str(e)}")

    feature_data = {
        "features": features,
        "product_features": product_features,
    }

    # ------------------------------------------
    # 5. Save to local persistent cache
    # ------------------------------------------
    if use_cache:
        cache_features(product_name, features, product_features)

    # ------------------------------------------
    # 6. Logging
    # ------------------------------------------
    if logger:
        logger.log_observation(f"{len(features)} features extracted.")
        logger.log_observation(f"Feature coverage computed for {len(product_features)} products.")

    return feature_data
