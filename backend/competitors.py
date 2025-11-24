from typing import List, Dict, Any
import streamlit as st
import asyncio

from backend.llm import call_openai_json_async, AgentLogger
from backend.cache import get_cached_competitors, cache_competitors


# ---------------------------------------------------------
# Helper: Build a stable cache key
# ---------------------------------------------------------
def _competitor_cache_key(product_name: str, company_name: str, description: str) -> str:
    """
    Stable cache key — ensures cache hits even if LLM descriptions vary.
    """
    return f"{product_name.strip().lower()}|{company_name.strip().lower()}|{description.strip().lower()}"


# ---------------------------------------------------------
# Streamlit cache for LLM competitor discovery
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def _cached_llm_competitor_call(messages_tuple: tuple) -> Dict[str, Any]:
    """
    Streamlit-managed cache layer.
    We wrap the async call in a sync function because Streamlit cache must be sync.
    """
    # Convert back to message list
    messages = [{"role": r, "content": c} for r, c in messages_tuple]

    # IMPORTANT: call asynchronous LLM using asyncio.run inside sync context
    result = asyncio.run(call_openai_json_async(messages, model="gpt-4o-mini"))
    return result


# ---------------------------------------------------------
# MAIN — ASYNC COMPETITOR DISCOVERY
# ---------------------------------------------------------
async def discover_competitors(
    product_name: str,
    company_name: str = "",
    description: str = "",
    logger: AgentLogger = None,
    use_cache: bool = True
) -> List[Dict[str, Any]]:

    # ----------------------------
    # 1. Check local file/dict cache
    # ----------------------------
    cache_key = _competitor_cache_key(product_name, company_name, description)

    if use_cache:
        cached = get_cached_competitors(product_name, company_name, description)
        if cached:
            if logger:
                logger.log_thought(f"[CACHE HIT] Competitors for '{product_name}' loaded instantly.")
                logger.log_observation(f"Loaded {len(cached)} competitors from cache.")
            return cached

    # ----------------------------
    # 2. Build the LLM prompt
    # ----------------------------
    if logger:
        logger.log_thought(f"Discovering competitors for: {product_name}")
        logger.log_action("Querying OpenAI (gpt-4o-mini) for competitor discovery...")

    prompt = f"""
You are a market research expert. Identify the top 5–10 direct competitors.

Product Name: {product_name}
Company Name: {company_name}
Description: {description}

Return ONLY JSON in this format:
{{
    "competitors": [
        {{
            "company_name": "...",
            "product_name": "...",
            "description": "...",
            "website": "",
            "market_position": "Market Leader / Challenger / Niche Player"
        }}
    ]
}}
    """

    messages = [
        {"role": "system", "content": "You are a senior competitive intelligence analyst."},
        {"role": "user", "content": prompt}
    ]

    # Convert list → tuple for Streamlit caching
    messages_tuple = tuple((m["role"], m["content"]) for m in messages)

    # ----------------------------
    # 3. CALL LLM (cached via Streamlit)
    # ----------------------------
    try:
        result_json_str = _cached_llm_competitor_call(messages_tuple)
        competitors = result_json_str.get("competitors", [])

    except Exception as e:
        if logger:
            logger.log_observation(f"ERROR during competitor discovery: {str(e)}")
        raise Exception(f"Failed to discover competitors: {str(e)}")

    # ----------------------------
    # 4. Store in your custom cache for persistence
    # ----------------------------
    if use_cache:
        cache_competitors(product_name, company_name, description, competitors)

    # ----------------------------
    # 5. Logging
    # ----------------------------
    if logger:
        logger.log_observation(f"Identified {len(competitors)} competitors.")
        for c in competitors:
            logger.log_observation(
                f" - {c.get('company_name')} ({c.get('product_name')})"
            )

    return competitors
