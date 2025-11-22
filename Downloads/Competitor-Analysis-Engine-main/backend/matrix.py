from typing import List, Dict, Any
import pandas as pd
from backend.llm import call_openai_json, AgentLogger


def build_comparison_matrix(
    product_name: str,
    features: List[Dict[str, Any]],
    product_features: Dict[str, List[str]],
    logger: AgentLogger = None
) -> pd.DataFrame:
    if logger:
        logger.log_thought("Building feature comparison matrix")
        logger.log_action("Creating structured matrix with all products and features")
    
    feature_names = [f["feature_name"] for f in features]
    product_names = list(product_features.keys())
    
    matrix_data = []
    for feature_name in feature_names:
        row = {"Feature": feature_name}
        for product in product_names:
            has_feature = feature_name in product_features.get(product, [])
            row[product] = "✓" if has_feature else "✗"
        matrix_data.append(row)
    
    df = pd.DataFrame(matrix_data)
    
    if logger:
        logger.log_observation(f"Matrix created with {len(feature_names)} features and {len(product_names)} products")
    
    return df


def analyze_differentiators(
    product_name: str,
    competitors: List[Dict[str, Any]],
    features: List[Dict[str, Any]],
    product_features: Dict[str, List[str]],
    logger: AgentLogger = None
) -> Dict[str, Any]:
    if logger:
        logger.log_thought("Analyzing competitive differentiators and unique selling points")
        logger.log_action("Identifying unique features and competitive advantages")
    
    competitor_names = [c.get("product_name", "Unknown") for c in competitors]
    
    feature_list = "\n".join([
        f"- {f['feature_name']}: {f.get('description', '')}"
        for f in features
    ])
    
    product_feature_summary = "\n".join([
        f"{prod}: {', '.join(feats)}"
        for prod, feats in product_features.items()
    ])
    
    prompt = f"""Analyze the competitive landscape and provide strategic insights.

Main Product: {product_name}
Competitors: {', '.join(competitor_names)}

Features Analysis:
{product_feature_summary}

Provide:
1. unique_to_product: List of features that ONLY {product_name} has
2. unique_to_competitors: Features that competitors have but {product_name} doesn't
3. common_features: Features that all or most products share
4. differentiators: Top 3-5 key differentiators for {product_name}
5. recommendations: Strategic recommendations for {product_name}
6. missing_capabilities: Top 5 important capabilities that {product_name} is missing

Return as JSON:
{{
    "unique_to_product": ["feature1", "feature2", ...],
    "unique_to_competitors": ["feature1", "feature2", ...],
    "common_features": ["feature1", "feature2", ...],
    "differentiators": [
        {{"title": "...", "description": "..."}}
    ],
    "recommendations": [
        {{"title": "...", "description": "..."}}
    ],
    "missing_capabilities": [
        {{"capability": "...", "importance": "High/Medium/Low", "rationale": "..."}}
    ]
}}"""
    
    try:
        messages = [
            {"role": "system", "content": "You are a strategic business analyst specializing in competitive positioning and product strategy."},
            {"role": "user", "content": prompt}
        ]
        
        result = call_openai_json(messages)
        
        if logger:
            logger.log_observation(f"Identified {len(result.get('differentiators', []))} key differentiators")
            logger.log_observation(f"Generated {len(result.get('recommendations', []))} strategic recommendations")
        
        return result
        
    except Exception as e:
        if logger:
            logger.log_observation(f"Error during differentiator analysis: {str(e)}")
        raise Exception(f"Failed to analyze differentiators: {str(e)}")
