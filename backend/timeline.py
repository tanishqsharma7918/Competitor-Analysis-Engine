from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from backend.database import get_all_analyses, get_analysis_by_id


def get_product_analysis_history(product_name: str) -> List[Dict[str, Any]]:
    all_analyses = get_all_analyses()
    
    product_analyses = [
        a for a in all_analyses 
        if a['product_name'].lower() == product_name.lower()
    ]
    
    return sorted(product_analyses, key=lambda x: x['created_at'])


def compare_two_analyses(analysis_id_1: int, analysis_id_2: int) -> Dict[str, Any]:
    analysis_1 = get_analysis_by_id(analysis_id_1)
    analysis_2 = get_analysis_by_id(analysis_id_2)
    
    if not analysis_1 or not analysis_2:
        return {"error": "One or both analyses not found"}
    
    competitors_1 = {c['product_name'] for c in analysis_1['competitors']}
    competitors_2 = {c['product_name'] for c in analysis_2['competitors']}
    
    new_competitors = competitors_2 - competitors_1
    removed_competitors = competitors_1 - competitors_2
    common_competitors = competitors_1 & competitors_2
    
    features_1 = {f['feature_name'] for f in analysis_1['features']}
    features_2 = {f['feature_name'] for f in analysis_2['features']}
    
    new_features = features_2 - features_1
    removed_features = features_1 - features_2
    common_features = features_1 & features_2
    
    feature_changes = {}
    for product in common_competitors:
        features_old = set(analysis_1['product_features'].get(product, []))
        features_new = set(analysis_2['product_features'].get(product, []))
        
        added = features_new - features_old
        removed = features_old - features_new
        
        if added or removed:
            feature_changes[product] = {
                "added_features": list(added),
                "removed_features": list(removed)
            }
    
    return {
        "analysis_1": {
            "id": analysis_1['id'],
            "date": analysis_1['created_at'].strftime('%Y-%m-%d %H:%M'),
            "product_name": analysis_1['product_name']
        },
        "analysis_2": {
            "id": analysis_2['id'],
            "date": analysis_2['created_at'].strftime('%Y-%m-%d %H:%M'),
            "product_name": analysis_2['product_name']
        },
        "competitor_changes": {
            "new": list(new_competitors),
            "removed": list(removed_competitors),
            "unchanged": list(common_competitors)
        },
        "feature_changes": {
            "new": list(new_features),
            "removed": list(removed_features),
            "unchanged": list(common_features)
        },
        "product_feature_changes": feature_changes,
        "summary": {
            "competitors_added": len(new_competitors),
            "competitors_removed": len(removed_competitors),
            "features_added": len(new_features),
            "features_removed": len(removed_features),
            "products_with_changes": len(feature_changes)
        }
    }


def get_trend_analysis(product_name: str) -> Dict[str, Any]:
    history = get_product_analysis_history(product_name)
    
    if len(history) < 2:
        return {
            "error": "Need at least 2 analyses to show trends",
            "history_count": len(history)
        }
    
    trend_data = {
        "dates": [],
        "competitor_counts": [],
        "feature_counts": [],
        "analyses": []
    }
    
    for analysis_summary in history:
        full_analysis = get_analysis_by_id(analysis_summary['id'])
        if full_analysis:
            trend_data["dates"].append(full_analysis['created_at'].strftime('%Y-%m-%d'))
            trend_data["competitor_counts"].append(len(full_analysis['competitors']))
            trend_data["feature_counts"].append(len(full_analysis['features']))
            trend_data["analyses"].append({
                "id": full_analysis['id'],
                "date": full_analysis['created_at'].strftime('%Y-%m-%d %H:%M')
            })
    
    return trend_data
