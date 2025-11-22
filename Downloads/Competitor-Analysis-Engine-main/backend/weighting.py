from typing import List, Dict, Any
import pandas as pd


def calculate_weighted_scores(
    product_features: Dict[str, List[str]],
    features: List[Dict[str, Any]],
    feature_weights: Dict[str, float]
) -> Dict[str, float]:
    scores = {}
    
    total_weight = sum(feature_weights.values())
    if total_weight == 0:
        total_weight = 1
    
    for product, feature_list in product_features.items():
        score = 0
        for feature_name in feature_list:
            weight = feature_weights.get(feature_name, 1.0)
            score += weight
        
        normalized_score = (score / total_weight) * 100 if total_weight > 0 else 0
        scores[product] = round(normalized_score, 2)
    
    return scores


def get_default_weights(features: List[Dict[str, Any]]) -> Dict[str, float]:
    category_base_weights = {
        "Core Functionality": 1.5,
        "Integration": 1.2,
        "Security": 1.3,
        "Performance": 1.2,
        "Pricing": 1.1,
        "Support": 1.0,
        "UI/UX": 1.0,
        "Analytics": 1.0,
        "General": 1.0
    }
    
    weights = {}
    for feature in features:
        category = feature.get('category', 'General')
        base_weight = category_base_weights.get(category, 1.0)
        weights[feature['feature_name']] = base_weight
    
    return weights


def create_weighted_comparison_matrix(
    matrix_df: pd.DataFrame,
    feature_weights: Dict[str, float]
) -> pd.DataFrame:
    weighted_df = matrix_df.copy()
    weighted_df['Weight'] = weighted_df['Feature'].map(feature_weights).fillna(1.0)
    
    products = [col for col in weighted_df.columns if col not in ['Feature', 'Weight']]
    
    for product in products:
        weighted_df[f'{product}_Score'] = weighted_df.apply(
            lambda row: row['Weight'] if row[product] == "✓" else 0,
            axis=1
        )
    
    return weighted_df


def rank_products_by_score(
    weighted_scores: Dict[str, float],
    product_name: str
) -> List[Dict[str, Any]]:
    sorted_products = sorted(weighted_scores.items(), key=lambda x: x[1], reverse=True)
    
    rankings = []
    for rank, (product, score) in enumerate(sorted_products, 1):
        rankings.append({
            "rank": rank,
            "product": product,
            "score": score,
            "is_main_product": product == product_name
        })
    
    return rankings
