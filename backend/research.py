"""
Research Agent Module - Web Search Integration for Competitor Analysis
Prevents LLM hallucinations by grounding prompts in live market data.
"""

from typing import List, Dict, Any
from duckduckgo_search import DDGS
from backend.llm import AgentLogger


def perform_research(
    product_name: str,
    company_name: str = "",
    description: str = "",
    logger: AgentLogger = None
) -> str:
    """
    Research Agent: Performs live web search to gather market intelligence.
    
    Args:
        product_name: Main product to analyze
        company_name: Optional company context
        description: Optional product description
        logger: AgentLogger instance for logging
    
    Returns:
        Formatted research summary from web search results
    """
    
    if logger:
        logger.log_thought("🔍 Starting live web research to prevent hallucinations...")
    
    # Build search query
    if company_name:
        search_query = f"{product_name} by {company_name} competitors alternatives"
    else:
        search_query = f"{product_name} competitors alternatives"
    
    if logger:
        logger.log_action(f"Searching: '{search_query}'")
    
    try:
        # Perform web search
        ddgs = DDGS()
        results = ddgs.text(search_query, max_results=10)
        
        if not results or not isinstance(results, list):
            if logger:
                logger.log_observation("⚠ No search results found - falling back to LLM knowledge")
            return ""  # Return empty string to proceed with LLM knowledge only
        
        # Format research summary
        research_summary = "=== LIVE MARKET RESEARCH DATA ===\n\n"
        
        for i, result in enumerate(results[:10], 1):
            if not isinstance(result, dict):
                continue
            
            title = result.get('title', 'Untitled')
            snippet = result.get('body', 'No description')
            url = result.get('href', '')
            
            research_summary += f"{i}. {title}\n"
            research_summary += f"   {snippet}\n"
            research_summary += f"   Source: {url}\n\n"
        
        research_summary += "=== END OF RESEARCH DATA ===\n"
        
        if logger:
            logger.log_observation(f"✓ Retrieved {len(results)} live market sources")
        
        return research_summary
    
    except Exception as e:
        error_msg = f"⚠ Research error: {str(e)}"
        if logger:
            logger.log_observation(error_msg)
        
        # Return empty string to gracefully fallback to LLM knowledge
        return ""


def perform_category_research(
    product_name: str,
    category: str,
    logger: AgentLogger = None
) -> str:
    """
    Specialized research for specific product categories.
    
    Args:
        product_name: Product to research
        category: Category context (e.g., "CRM", "Project Management")
        logger: AgentLogger instance
    
    Returns:
        Category-specific research summary
    """
    
    if logger:
        logger.log_thought(f"🔍 Researching {category} category for {product_name}...")
    
    search_query = f"{product_name} {category} competitors market analysis"
    
    try:
        ddgs = DDGS()
        results = ddgs.text(search_query, max_results=5)
        
        if not results:
            return f"No {category} category data found."
        
        research_summary = f"=== {category.upper()} CATEGORY RESEARCH ===\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'Untitled')
            snippet = result.get('body', 'No description')
            research_summary += f"{i}. {title}\n   {snippet}\n\n"
        
        if logger:
            logger.log_observation(f"✓ Category research complete: {len(results)} sources")
        
        return research_summary
    
    except Exception as e:
        if logger:
            logger.log_observation(f"⚠ Category research error: {str(e)}")
        return f"Category research unavailable: {str(e)}"


def verify_competitor_exists(
    company_name: str,
    product_name: str,
    logger: AgentLogger = None
) -> Dict[str, Any]:
    """
    Research-based verification: Check if a competitor actually exists.
    
    Args:
        company_name: Company to verify
        product_name: Product to verify
        logger: AgentLogger instance
    
    Returns:
        Dict with verification status and evidence
    """
    
    if logger:
        logger.log_thought(f"🔎 Verifying: {company_name} - {product_name}")
    
    search_query = f"{company_name} {product_name} official website"
    
    try:
        ddgs = DDGS()
        results = ddgs.text(search_query, max_results=3)
        
        if not results:
            if logger:
                logger.log_observation(f"✗ No web evidence for {company_name}")
            return {
                "exists": False,
                "evidence": "No search results found",
                "confidence": "low"
            }
        
        # Check if results mention the company/product
        evidence_text = " ".join([r.get('body', '') for r in results[:3]])
        
        if company_name.lower() in evidence_text.lower():
            if logger:
                logger.log_observation(f"✓ Verified: {company_name} exists")
            return {
                "exists": True,
                "evidence": results[0].get('body', ''),
                "source": results[0].get('href', ''),
                "confidence": "high"
            }
        else:
            if logger:
                logger.log_observation(f"⚠ Weak evidence for {company_name}")
            return {
                "exists": False,
                "evidence": "Search results don't match",
                "confidence": "medium"
            }
    
    except Exception as e:
        if logger:
            logger.log_observation(f"⚠ Verification error: {str(e)}")
        return {
            "exists": None,
            "evidence": f"Error: {str(e)}",
            "confidence": "unknown"
        }
