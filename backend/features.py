from typing import List, Dict, Any
from backend.llm import call_openai_json, AgentLogger
from backend.cache import get_cached_features, cache_features


def extract_features(
    product_name: str,
    competitors: List[Dict[str, Any]],
    description: str = "",
    logger: AgentLogger = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    if use_cache:
        cached_result = get_cached_features(product_name)
        if cached_result:
            if logger:
                logger.log_thought(f"Found cached feature data for: {product_name}")
                logger.log_observation(f"Using cached results ({len(cached_result['features'])} features) - saved API call!")
            return cached_result
    
    if logger:
        logger.log_thought("Extracting features from all products and competitors")
        logger.log_action(f"Analyzing features for {product_name} and {len(competitors)} competitors")
    
    competitor_list = "\n".join([
        f"- {c.get('company_name', 'Unknown')}: {c.get('product_name', 'Unknown')} - {c.get('description', '')}"
        for c in competitors
    ])
    
    prompt = f"""You are a product analyst expert. Analyze the following product and its competitors, then extract a comprehensive list of key features.

Main Product: {product_name}
{f'Description: {description}' if description else ''}

Competitors:
{competitor_list}

Your task:
1. Identify 7 key features that are important for comparison across all these products
2. For each feature, determine which products have it

Return your response as JSON in this exact format:
{{
    "features": [
        {{
            "feature_name": "...",
            "description": "Brief description of the feature",
            "category": "e.g., Core Functionality, Integration, Pricing, Support, etc."
        }}
    ],
    "product_features": {{
        "{product_name}": ["feature_name_1", "feature_name_2", ...],
        "Competitor Product 1": ["feature_name_1", ...],
        ...
    }}
}}

Make sure to use the exact product names as they appear in the competitor list.
"""
    
    try:
        messages = [
            {"role": "system", "content": "You are an expert product analyst with deep knowledge of product features and competitive analysis."},
            {"role": "user", "content": prompt}
        ]
        
        result = call_openai_json(messages)
        
        features = result.get("features", [])
        product_features = result.get("product_features", {})
        
        feature_data = {
            "features": features,
            "product_features": product_features
        }
        
        if use_cache:
            cache_features(product_name, features, product_features)
        
        if logger:
            logger.log_observation(f"Successfully extracted {len(features)} key features (cached for future use)")
            logger.log_observation(f"Analyzed feature coverage for {len(product_features)} products")
        
        return feature_data
        
    except Exception as e:
        if logger:
            logger.log_observation(f"Error during feature extraction: {str(e)}")
        raise Exception(f"Failed to extract features: {str(e)}")
