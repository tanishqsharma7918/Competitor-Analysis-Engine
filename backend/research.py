"""
Research Agent Module - Web Search Integration for Competitor Analysis
Prevents LLM hallucinations by grounding prompts in live market data.
"""

from typing import List, Dict, Any
from ddgs import DDGS
from backend.llm import AgentLogger


def perform_research(
    product_name: str,
    company_name: str = "",
    description: str = "",
    logger: AgentLogger = None
) -> str:
    """
    Research Agent: Performs live web search to gather market intelligence.
    NEW: Fall-back logic for better results.
    
    Logic:
    1. Search for "{Product} {Company} competitors"
    2. If results are short (<200 words) or have <3 company names:
       - Perform SECOND search for market category
       - Example: "Top Healthcare Dark Web Monitoring companies"
    3. Combine both search results
    
    Args:
        product_name: Main product to analyze
        company_name: Optional company context
        description: Optional product description
        logger: AgentLogger instance for logging
    
    Returns:
        Formatted research summary from web search results (primary + fallback)
    """
    
    if logger:
        logger.log_thought("🔍 Starting live web research with fall-back logic...")
    
    # ============================================================
    # PRIMARY SEARCH: "{Product} {Company} competitors"
    # ============================================================
    if company_name:
        primary_query = f"{product_name} {company_name} competitors alternatives"
    else:
        primary_query = f"{product_name} competitors alternatives"
    
    if logger:
        logger.log_action(f"Primary search: '{primary_query}'")
    
    primary_results = []
    try:
        with DDGS() as ddgs:
            primary_results = list(ddgs.text(primary_query, max_results=15))
    except Exception as e:
        if logger:
            logger.log_observation(f"⚠ Primary search error: {str(e)}")
    
    # Format primary results
    primary_summary = ""
    primary_word_count = 0
    company_name_count = 0
    
    if primary_results and isinstance(primary_results, list):
        for i, result in enumerate(primary_results[:15], 1):
            if not isinstance(result, dict):
                continue
            
            title = result.get('title', 'Untitled')
            snippet = result.get('body', 'No description')
            url = result.get('href', '')
            
            primary_summary += f"{i}. {title}\n"
            primary_summary += f"   {snippet}\n"
            primary_summary += f"   Source: {url}\n\n"
            
            # Count words and potential company names (capitalized words)
            primary_word_count += len(snippet.split())
            company_name_count += sum(1 for word in snippet.split() if word and word[0].isupper())
    
    if logger:
        logger.log_observation(f"✓ Primary search: {len(primary_results)} sources, ~{primary_word_count} words, ~{company_name_count} capitalized terms")
    
    # ============================================================
    # FALL-BACK LOGIC: Check if results are sufficient
    # ============================================================
    needs_fallback = False
    
    if primary_word_count < 200:
        needs_fallback = True
        if logger:
            logger.log_thought(f"⚠ Primary results too short ({primary_word_count} words < 200). Triggering fall-back search...")
    elif company_name_count < 3:
        needs_fallback = True
        if logger:
            logger.log_thought(f"⚠ Few company names detected ({company_name_count} < 3). Triggering fall-back search...")
    
    fallback_summary = ""
    
    if needs_fallback:
        # ============================================================
        # FALL-BACK SEARCH: Market category search
        # ============================================================
        # Extract market category from description or product name
        if description:
            # Use description to build category query
            fallback_query = f"top {description} companies alternatives"
        else:
            # Use product name
            fallback_query = f"top {product_name} companies market leaders"
        
        if logger:
            logger.log_action(f"Fall-back search: '{fallback_query}'")
        
        try:
            with DDGS() as ddgs:
                fallback_results = list(ddgs.text(fallback_query, max_results=15))
            
            if fallback_results and isinstance(fallback_results, list):
                fallback_summary = "\n=== ADDITIONAL MARKET CATEGORY SEARCH ===\n\n"
                
                for i, result in enumerate(fallback_results[:15], 1):
                    if not isinstance(result, dict):
                        continue
                    
                    title = result.get('title', 'Untitled')
                    snippet = result.get('body', 'No description')
                    url = result.get('href', '')
                    
                    fallback_summary += f"{i}. {title}\n"
                    fallback_summary += f"   {snippet}\n"
                    fallback_summary += f"   Source: {url}\n\n"
                
                if logger:
                    logger.log_observation(f"✓ Fall-back search: {len(fallback_results)} additional sources retrieved")
        
        except Exception as e:
            if logger:
                logger.log_observation(f"⚠ Fall-back search error: {str(e)}")
    
    # ============================================================
    # COMBINE RESULTS
    # ============================================================
    if not primary_summary and not fallback_summary:
        if logger:
            logger.log_observation("⚠ No search results from either search - falling back to LLM knowledge")
        return ""
    
    combined_summary = "=== LIVE MARKET RESEARCH DATA ===\n\n"
    
    if primary_summary:
        combined_summary += "--- PRIMARY SEARCH RESULTS ---\n"
        combined_summary += primary_summary
    
    if fallback_summary:
        combined_summary += fallback_summary
    
    combined_summary += "=== END OF RESEARCH DATA ===\n"
    
    total_sources = len(primary_results) + (len(fallback_results) if needs_fallback and 'fallback_results' in locals() else 0)
    
    if logger:
        logger.log_observation(f"✅ Total research sources: {total_sources} (Primary: {len(primary_results)}, Fall-back: {len(fallback_results) if needs_fallback and 'fallback_results' in locals() else 0})")
    
    return combined_summary


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
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=5))
        
        if not results:
            return f"No {category} category data found."
        
        research_summary = f"=== {category.upper()} CATEGORY RESEARCH ===\n\n"
        
        for i, result in enumerate(results, 1):
            if not isinstance(result, dict):
                continue
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
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=3))
        
        if not results:
            if logger:
                logger.log_observation(f"✗ No web evidence for {company_name}")
            return {
                "exists": False,
                "evidence": "No search results found",
                "confidence": "low"
            }
        
        # Check if results mention the company/product
        evidence_text = " ".join([r.get('body', '') for r in results[:3] if isinstance(r, dict)])
        
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
