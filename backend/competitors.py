from typing import List, Dict, Any
from backend.llm import call_openai_json, AgentLogger
from backend.cache import get_cached_competitors, cache_competitors


def discover_competitors(
    product_name: str,
    company_name: str = "",
    description: str = "",
    logger: AgentLogger = None,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    if use_cache:
        cached_result = get_cached_competitors(product_name, company_name, description)
        if cached_result:
            if logger:
                logger.log_thought(f"Found cached competitor data for: {product_name}")
                logger.log_observation(f"Using cached results ({len(cached_result)} competitors) - saved API call!")
            return cached_result
    
    if logger:
        logger.log_thought(f"Starting competitor discovery for product: {product_name}")
        logger.log_action("Querying OpenAI to identify top competitors in the market")
    
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
        messages = [
            {"role": "system", "content": "You are an expert market research analyst with deep knowledge of competitive landscapes across industries."},
            {"role": "user", "content": prompt}
        ]
        
        result = call_openai_json(messages)
        
        competitors = result.get("competitors", [])
        
        if use_cache:
            cache_competitors(product_name, company_name, description, competitors)
        
        if logger:
            logger.log_observation(f"Successfully identified {len(competitors)} competitors (cached for future use)")
            for comp in competitors:
                logger.log_observation(f"  - {comp.get('company_name', 'Unknown')}: {comp.get('product_name', 'Unknown')}")
        
        return competitors
        
    except Exception as e:
        if logger:
            logger.log_observation(f"Error during competitor discovery: {str(e)}")
        raise Exception(f"Failed to discover competitors: {str(e)}")
