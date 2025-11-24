from typing import List, Dict, Any
import streamlit as st
import asyncio
import json

from backend.llm import call_openai_json, call_openai_json_async, AgentLogger
from backend.cache import get_cached_competitors, cache_competitors


# ---------------------------------------------------------
# Helper: stable cache key
# ---------------------------------------------------------
def _competitor_cache_key(product_name: str, company_name: str, description: str) -> str:
    return f"{product_name.strip().lower()}|{company_name.strip().lower()}|{description.strip().lower()}"


# ---------------------------------------------------------
# FIXED — Streamlit-safe cached LLM wrapper
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def _cached_llm_competitor_call(messages_tuple: tuple) -> Dict[str, Any]:
    """
    Safe cached wrapper. MUST be synchronous.
    Uses thread offloading instead of asyncio.run to avoid Streamlit crashes.
    Also guarantees parsed JSON dict.
    """
    from backend.llm import call_openai_json  # sync version

    # Rebuild messages
    messages = [{"role": r, "content": c} for (r, c) in messages_tuple]

    # Call sync JSON function inside the cache
    raw = call_openai_json(messages, model="gpt-4o-mini")

    # Ensure JSON is parsed, even if cached as string
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            raise ValueError(f"OpenAI returned invalid JSON:\n\n{raw}")

    return raw  # already a dict


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

    # 1. Internal persistent cache
    if use_cache:
        cached = get_cached_competitors(product_name, company_name, description)
        if cached:
            if logger:
                logger.log_thought(f"[CACHE HIT] Competitors for '{product_name}' loaded instantly.")
                logger.log_observation(f"Loaded {len(cached)} competitors from cache.")
            return cached

    # 2. Build LLM prompt
    if logger:
        logger.log_thought(f"Discovering competitors for: {product_name}")
        logger.log_action("Querying OpenAI (gpt-4o-mini)...")

    prompt = f"""
You are a market research expert. Identify the top 5–10 direct competitors.

Product Name: {product_name}
Company Name: {company_name}
Description: {description}

Return ONLY JSON in this exact structure:
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

    messages_tuple = tuple((m["role"], m["content"]) for m in messages)

    # 3. SAFE LLM CALL (cached)
    try:
        result_dict = _cached_llm_competitor_call(messages_tuple)
        competitors = result_dict.get("competitors", [])

    except Exception as e:
        if logger:
            logger.log_observation(f"ERROR during competitor discovery: {str(e)}")
        raise Exception(f"Failed to discover competitors: {str(e)}")

    # 4. Persist to your custom cache
    if use_cache:
        cache_competitors(product_name, company_name, description, competitors)

    # 5. Logging
    if logger:
        logger.log_observation(f"Identified {len(competitors)} competitors.")
        for c in competitors:
            logger.log_observation(f" - {c.get('company_name')} ({c.get('product_name')})")

    return competitors
