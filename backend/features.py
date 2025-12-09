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
    Streamlit cache wrapper using GPT-4o for enhanced feature extraction.
    """
    messages = [{"role": r, "content": c} for r, c in messages_tuple]
    result = asyncio.run(call_openai_json_async(messages, model="gpt-4o"))
    return result


# ---------------------------------------------------------
# ASYNC FEATURE EXTRACTION (UPGRADED TO GPT-4o)
# ---------------------------------------------------------
async def extract_features(
    product_name: str,
    competitors: List[Dict[str, Any]],
    description: str = "",
    logger: AgentLogger = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Enhanced feature extraction using GPT-4o with:
    - Deeper feature analysis
    - Importance scoring
    - Competitive relevance scoring
    - Category classification
    """

    # 1. Build stable cache key
    competitor_names = [c.get("product_name", "") for c in competitors]
    cache_key = _feature_cache_key(product_name, description, competitor_names)

    # 2. Check cache
    if use_cache:
        cached = get_cached_features(product_name)
        if cached:
            if logger:
                logger.log_thought(f"[CACHE HIT] Features for '{product_name}' loaded instantly.")
                logger.log_observation(f"{len(cached['features'])} features pulled from cache.")
            return cached

    # 3. Prepare enhanced LLM prompt
    if logger:
        logger.log_thought("🔬 Extracting features with GPT-4o deep reasoning...")
        logger.log_action(f"Analyzing {product_name} and {len(competitors)} competitors.")

    competitor_list = "\n".join([
        f"- {c.get('company_name', 'Unknown')}: {c.get('product_name', 'Unknown')}\n"
        f"  Description: {c.get('description', '')}\n"
        f"  Category: {c.get('product_category', '')}\n"
        f"  Strengths: {c.get('key_strengths', '')}\n"
        f"  Target: {c.get('target_audience', '')}"
        for c in competitors
    ])

    prompt = f"""
You are a senior product analyst with deep expertise in competitive feature analysis.

Main Product: {product_name}
Description: {description}

Competitors:
{competitor_list}

**Tasks:**

1. Identify EXACTLY 10 key features that are critical for comparison across all these products.

2. For each feature, provide:
   - feature_name (clear, specific name)
   - description (detailed 2-sentence explanation)
   - category (choose from: Core Functionality, Integrations, Analytics, Collaboration, Security, Pricing, Support, UX/Design, Mobile, API/Developer)
   - importance_score (1-5, where 5 = critical for market success)
   - competitive_relevance_score (1-5, where 5 = key differentiator in this market)

3. For each product (main + competitors), list which features they have.

**Important:** Use deep reasoning to identify features that:
- Are genuinely important for users
- Differentiate competitors from each other
- Reflect real market dynamics
- Are verifiable and not hallucinated

Return ONLY JSON in this EXACT format:
{{
    "features": [
        {{
            "feature_name": "...",
            "description": "...",
            "category": "...",
            "importance_score": 4,
            "competitive_relevance_score": 5
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
        {"role": "system", "content": "You are an expert product feature analyst with deep market knowledge and factual accuracy."},
        {"role": "user", "content": prompt}
    ]

    messages_tuple = tuple((m["role"], m["content"]) for m in messages)

    # 4. Call GPT-4o
    try:
        json_result = _cached_llm_feature_call(messages_tuple)
        features = json_result.get("features", [])
        product_features = json_result.get("product_features", {})

        # Validate importance and relevance scores
        for feature in features:
            if "importance_score" not in feature:
                feature["importance_score"] = 3
            if "competitive_relevance_score" not in feature:
                feature["competitive_relevance_score"] = 3

    except Exception as e:
        if logger:
            logger.log_observation(f"ERROR during feature extraction: {str(e)}")
        raise Exception(f"Feature extraction failed: {str(e)}")

    feature_data = {
        "features": features,
        "product_features": product_features,
    }

    # 5. Cache results
    if use_cache:
        cache_features(product_name, features, product_features)

    # 6. Enhanced logging
    if logger:
        logger.log_observation(f"✅ Extracted {len(features)} high-quality features")
        
        # Log top features by importance
        sorted_features = sorted(features, key=lambda x: x.get("importance_score", 0), reverse=True)
        logger.log_observation("🔝 Top 3 critical features:")
        for feat in sorted_features[:3]:
            logger.log_observation(
                f"  • {feat['feature_name']} "
                f"(Importance: {feat.get('importance_score', 0)}/5, "
                f"Competitive Relevance: {feat.get('competitive_relevance_score', 0)}/5)"
            )
        
        logger.log_observation(f"📊 Feature coverage computed for {len(product_features)} products")

    return feature_data
