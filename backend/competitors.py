from typing import List, Dict, Any
import streamlit as st
from backend.llm import AgentLogger
from backend.cache import get_cached_competitors, cache_competitors


@st.cache_data(show_spinner=False)
def cached_llm_competitor_discovery(messages_tuple):
    """
    Streamlit-safe cached wrapper around OpenAI JSON call.
    messages_tuple: tuple of (role, content) pairs (Streamlit requires hashable inputs).
    """
    from backend.llm import call_openai_json  # imported here to avoid Streamlit hashing issues
    messages = [{"role": role, "content": content} for role, content in messages_tuple]
    return call_openai_json(messages)



# ---------------------------------------------------------
# MAIN FUNCTION — COMPETITOR DISCOVERY
# ---------------------------------------------------------

def discover_competitors(
    product_name: str,
    company_name: str = "",
    description: str = "",
    logger: AgentLogger = None,
    use_cache: bool = True
) -> List[Dict[str, Any]]:

    # -----------------------------------------------------
    # 1. Check your custom stored cache first
    # -----------------------------------------------------
    if use_cache:
        cached_result = get_cached_competitors(product_name, company_name, description)
        if cached_result:
            if logger:
                logger.log_thought(f"Found cached competitor data for: {product_name}")
                logger.log_observation(
                    f"Using cached results ({len(cached_result)} competitors) - saved API call!"
                )
            return cached_result

    # -----------------------------------------------------
    # 2. Log start
    # -----------------------------------------------------
    if logger:
        logger.log_thought(f"Starting competitor discovery for product: {product_name}")
        logger.log_action("Querying OpenAI to identify top competitors in the market")

    # -----------------------------------------------------
    # 3. Build LLM prompt
    # -----------------------------------------------------
    prompt = f"""You are a market research expert. Identify the top 5-10 direct competitors for the following product.

Product Name: {product_name}
{f'Company Name: {company_name}' if company_name else ''}
{f'Description: {description}' if description else ''}

For each competitor, provide:
1. company_name: The name of the competing company
2. product_name: The name of their competing product
3. description: A brief description of what they offer
4. website: Their website URL (if known, otherwise empty string)
5. market_position: Their position in the market (e.g., "Market Leader", "Challenger", "Niche Player")

Return your response as JSON in this exact format:
{{
    "competitors": [
        {{
            "company_name": "...",
            "product_name": "...",
            "description": "...",
            "website": "...",
            "market_position": "..."
        }}
    ]
}}"""

    try:
        # Build OpenAI messages
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert market research analyst with deep knowledge "
                    "of competitive landscapes across industries."
                )
            },
            {"role": "user", "content": prompt}
        ]

        # -----------------------------------------------------
        # 4. Convert messages → tuple for Streamlit caching
        # -----------------------------------------------------
        messages_tuple = tuple((m["role"], m["content"]) for m in messages)

        # -----------------------------------------------------
        # 5. Call cached LLM instead of direct OpenAI API
        # -----------------------------------------------------
        result = cached_llm_competitor_discovery(messages_tuple)

        competitors = result.get("competitors", [])

        # -----------------------------------------------------
        # 6. Cache the results in your custom cache system
        # -----------------------------------------------------
        if use_cache:
            cache_competitors(product_name, company_name, description, competitors)

        # -----------------------------------------------------
        # 7. Logging
        # -----------------------------------------------------
        if logger:
            logger.log_observation(
                f"Successfully identified {len(competitors)} competitors (cached for future use)"
            )
            for comp in competitors:
                logger.log_observation(
                    f"  - {comp.get('company_name', 'Unknown')}: {comp.get('product_name', 'Unknown')}"
                )

        return competitors

    except Exception as e:
        if logger:
            logger.log_observation(f"Error during competitor discovery: {str(e)}")

        raise Exception(f"Failed to discover competitors: {str(e)}")
