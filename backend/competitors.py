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
    Safe cached wrapper using GPT-4o for maximum accuracy.
    """
    from backend.llm import call_openai_json

    messages = [{"role": r, "content": c} for (r, c) in messages_tuple]
    raw = call_openai_json(messages, model="gpt-4o")

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            raise ValueError(f"OpenAI returned invalid JSON:\n\n{raw}")

    return raw


# ---------------------------------------------------------
# STEP 1: Multi-Step Competitor Discovery (GPT-4o) — RESEARCH-FIRST
# ---------------------------------------------------------
async def _discover_competitors_multi_step(
    product_name: str,
    company_name: str,
    description: str,
    research_context: str = "",
    logger: AgentLogger = None
) -> List[Dict[str, Any]]:
    """
    RESEARCH-FIRST: Uses GPT-4o's deep reasoning with live market data to discover competitors in 4 steps:
    1. Well-known competitors
    2. Niche and small competitors
    3. Emerging startups
    4. Open-source + budget options
    """
    
    if logger:
        logger.log_thought("🔍 Step 1/4: Discovering well-known competitors...")
    
    prompt_step1 = f"""
You are a Market Research & Competitor Analysis Expert.

REAL-TIME CONTEXT FROM WEB SEARCH:
---
{research_context}
---

TASK:
Analyze the product '{product_name}' by '{company_name}' (Description: {description}) based ONLY on the context above.

1. **Identify the Precise Niche:** Define the specific market category (e.g., if it's 'Medical Device Security', do NOT just say 'Healthcare').

2. **Select 3-5 Direct Competitors:**
   - Look for companies that solve the *exact same problem* for the *exact same customer*.
   - **Guardrail:** If the product is a technical B2B tool (like 'External Threat Intel'), DO NOT suggest generic consumer apps or internal compliance checklists.
   - **Guardrail:** If the product is 'Internal' (installable), do not suggest 'External' (SaaS scanning) tools unless they are the primary alternative.

3. **Explain Your Reasoning:** For each competitor, explain *why* it is a functional alternative based on the search data.

**STEP 1: Identify 3-5 WELL-KNOWN, MARKET-LEADING competitors.**

For each competitor, provide:
- company_name
- product_name
- description (1 sentence)
- target_audience (who uses this product)
- pricing_tier (Enterprise / Mid-Market / SMB / Free)
- product_category (e.g., Project Management, CRM, Collaboration)
- key_strengths (comma-separated, 2-3 strengths)
- key_weaknesses (comma-separated, 2-3 weaknesses)
- website (full URL)
- market_position (Market Leader / Challenger / Niche Player)

Return ONLY JSON:
{{
    "competitors": [
        {{
            "company_name": "...",
            "product_name": "...",
            "description": "...",
            "target_audience": "...",
            "pricing_tier": "...",
            "product_category": "...",
            "key_strengths": "...",
            "key_weaknesses": "...",
            "website": "...",
            "market_position": "..."
        }}
    ]
}}
"""

    messages1 = [
        {"role": "system", "content": "You are a Market Research & Competitor Analysis Expert. CRITICAL RULES: 1) Base ALL analysis ONLY on provided research data. 2) Identify the PRECISE niche, not generic categories. 3) Select competitors solving the EXACT same problem for the EXACT same customer. 4) DO NOT mix Internal vs External tools. 5) DO NOT mix B2B technical tools with consumer apps. 6) Explain WHY each competitor is a functional alternative."},
        {"role": "user", "content": prompt_step1}
    ]
    
    result1 = await asyncio.to_thread(call_openai_json, messages1, "gpt-4o")
    step1_competitors = result1.get("competitors", [])
    
    if logger:
        logger.log_observation(f"✓ Found {len(step1_competitors)} well-known competitors")
    
    # STEP 2: Niche and small competitors
    if logger:
        logger.log_thought("🔍 Step 2/4: Discovering niche and small competitors...")
    
    prompt_step2 = f"""
REAL-TIME CONTEXT FROM WEB SEARCH:
---
{research_context}
---

Product: {product_name}
Category: {description}

Already found: {[c.get('company_name', 'Unknown') for c in step1_competitors]}

**STEP 2: Identify 2-3 NICHE or SMALLER competitors**

RULES:
1. Focus on the PRECISE niche (not generic category)
2. Select competitors solving the EXACT same problem
3. If product is 'Internal', do NOT suggest 'External' tools
4. If product is B2B technical, do NOT suggest consumer apps
5. Base suggestions ONLY on research data above
6. Explain WHY each is a functional alternative

Return same JSON format as before.
"""

    messages2 = [
        {"role": "system", "content": "You are a Market Research Expert focusing on niche players. CRITICAL: Identify PRECISE niche, not generic categories. Select competitors solving EXACT same problem. DO NOT mix Internal/External or B2B/consumer tools. Base ALL suggestions on research data only."},
        {"role": "user", "content": prompt_step2}
    ]
    
    result2 = await asyncio.to_thread(call_openai_json, messages2, "gpt-4o")
    step2_competitors = result2.get("competitors", [])
    
    if logger:
        logger.log_observation(f"✓ Found {len(step2_competitors)} niche competitors")
    
    # STEP 3: Emerging startups
    if logger:
        logger.log_thought("🔍 Step 3/4: Discovering emerging startups...")
    
    prompt_step3 = f"""
REAL-TIME CONTEXT FROM WEB SEARCH:
---
{research_context}
---

Product: {product_name}

Already found: {[c.get('company_name', 'Unknown') for c in step1_competitors + step2_competitors]}

**STEP 3: Identify 2-3 EMERGING STARTUPS or NEW ENTRANTS**

RULES:
1. Focus on the PRECISE niche (not generic category)
2. Select startups solving the EXACT same problem
3. Maintain Internal vs External distinction
4. Maintain B2B technical vs consumer distinction
5. Base suggestions ONLY on research data above
6. Explain WHY each is a functional alternative

Return same JSON format.
"""

    messages3 = [
        {"role": "system", "content": "You are a Market Research Expert tracking emerging startups. CRITICAL: Identify PRECISE niche. Select startups solving EXACT same problem. Maintain Internal/External and B2B/consumer distinctions. Base ALL suggestions on research data only."},
        {"role": "user", "content": prompt_step3}
    ]
    
    result3 = await asyncio.to_thread(call_openai_json, messages3, "gpt-4o")
    step3_competitors = result3.get("competitors", [])
    
    if logger:
        logger.log_observation(f"✓ Found {len(step3_competitors)} emerging startups")
    
    # STEP 4: Open-source and budget options
    if logger:
        logger.log_thought("🔍 Step 4/4: Discovering open-source and budget alternatives...")
    
    prompt_step4 = f"""
REAL-TIME CONTEXT FROM WEB SEARCH:
---
{research_context}
---

Product: {product_name}

Already found: {[c.get('company_name', 'Unknown') for c in step1_competitors + step2_competitors + step3_competitors]}

**STEP 4: Identify 2-3 OPEN-SOURCE or LOW-COST ALTERNATIVES**

RULES:
1. Focus on the PRECISE niche (not generic category)
2. Select alternatives solving the EXACT same problem
3. Maintain Internal vs External distinction
4. Maintain B2B technical vs consumer distinction
5. Base suggestions ONLY on research data above
6. Explain WHY each is a functional alternative

Return same JSON format.
"""

    messages4 = [
        {"role": "system", "content": "You are a Market Research Expert analyzing open-source alternatives. CRITICAL: Identify PRECISE niche. Select alternatives solving EXACT same problem. Maintain Internal/External and B2B/consumer distinctions. Base ALL suggestions on research data only."},
        {"role": "user", "content": prompt_step4}
    ]
    
    result4 = await asyncio.to_thread(call_openai_json, messages4, "gpt-4o")
    step4_competitors = result4.get("competitors", [])
    
    if logger:
        logger.log_observation(f"✓ Found {len(step4_competitors)} open-source/budget options")
    
    # Merge all lists
    all_competitors = step1_competitors + step2_competitors + step3_competitors + step4_competitors
    
    # Remove duplicates by company_name
    seen = set()
    unique_competitors = []
    for comp in all_competitors:
        company = comp.get("company_name", "").lower().strip()
        if company and company not in seen:
            seen.add(company)
            unique_competitors.append(comp)
    
    if logger:
        logger.log_observation(f"📊 Total unique competitors: {len(unique_competitors)}")
    
    return unique_competitors


# ---------------------------------------------------------
# STEP 2: Verification Step (GPT-4o)
# ---------------------------------------------------------
async def _verify_competitors(
    competitors: List[Dict[str, Any]],
    logger: AgentLogger = None
) -> List[Dict[str, Any]]:
    """
    Uses GPT-4o to verify each competitor is REAL and update incorrect information.
    """
    
    if logger:
        logger.log_thought("🔎 Verifying competitors with GPT-4o...")
    
    verified_competitors = []
    
    for comp in competitors:
        company_name = comp.get("company_name", "")
        product_name = comp.get("product_name", "")
        website = comp.get("website", "")
        
        verification_prompt = f"""
You are a fact-checking expert. Verify if this competitor is REAL and correct any errors.

Company: {company_name}
Product: {product_name}
Website: {website}

Tasks:
1. Verify if this company and product actually exist
2. Correct the website URL if wrong
3. Verify the product description is accurate
4. Return "exists: yes" or "exists: no"

Return ONLY JSON:
{{
    "exists": "yes/no",
    "company_name": "...",
    "product_name": "...",
    "website": "...",
    "verification_note": "..."
}}
"""

        messages = [
            {"role": "system", "content": "You are a factual verification specialist with access to company databases. Do not guess. Only verify based on known facts."},
            {"role": "user", "content": verification_prompt}
        ]
        
        try:
            result = await asyncio.to_thread(call_openai_json, messages, "gpt-4o")
            
            if result.get("exists", "").lower() == "yes":
                # Update competitor with verified information
                comp["company_name"] = result.get("company_name", comp["company_name"])
                comp["product_name"] = result.get("product_name", comp["product_name"])
                comp["website"] = result.get("website", comp["website"])
                verified_competitors.append(comp)
                
                if logger:
                    logger.log_observation(f"✓ Verified: {comp['company_name']}")
            else:
                if logger:
                    logger.log_observation(f"✗ Removed: {company_name} (does not exist)")
        
        except Exception as e:
            # If verification fails, keep the competitor
            verified_competitors.append(comp)
            if logger:
                logger.log_observation(f"⚠ Verification error for {company_name}: {str(e)}")
    
    return verified_competitors


# ---------------------------------------------------------
# MAIN — ASYNC COMPETITOR DISCOVERY (RESEARCH-FIRST)
# ---------------------------------------------------------
async def discover_competitors(
    product_name: str,
    company_name: str = "",
    description: str = "",
    research_context: str = "",
    logger: AgentLogger = None,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    """
    RESEARCH-FIRST competitor discovery using GPT-4o with:
    - Live web search context injection
    - Multi-step discovery (4 stages)
    - Verification of all competitors
    - Enhanced competitor details
    - Low hallucination, high accuracy
    """

    # 1. Check cache
    if use_cache:
        cached = get_cached_competitors(product_name, company_name, description)
        if cached:
            if logger:
                logger.log_thought(f"[CACHE HIT] Competitors for '{product_name}' loaded instantly.")
                logger.log_observation(f"Loaded {len(cached)} competitors from cache.")
            return cached

    # 2. Multi-step discovery WITH RESEARCH CONTEXT
    if logger:
        logger.log_action("🚀 Starting RESEARCH-FIRST GPT-4o powered competitor discovery...")
    
    competitors = await _discover_competitors_multi_step(
        product_name, company_name, description, research_context, logger
    )
    
    # 3. Verify competitors
    if logger:
        logger.log_action("🔍 Verifying competitor authenticity...")
    
    verified_competitors = await _verify_competitors(competitors, logger)
    
    # 4. Cache results
    if use_cache:
        cache_competitors(product_name, company_name, description, verified_competitors)
    
    # 5. Final logging
    if logger:
        logger.log_observation(f"✅ Final verified competitor count: {len(verified_competitors)}")
        for c in verified_competitors:
            logger.log_observation(f"  • {c.get('company_name')} - {c.get('product_name')} ({c.get('market_position')})")
    
    return verified_competitors
