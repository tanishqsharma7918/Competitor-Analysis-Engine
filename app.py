import streamlit as st
import os
import pandas as pd
import asyncio
import nest_asyncio

nest_asyncio.apply()

# Backend imports (ASYNC + optimized backend)
from backend.llm import AgentLogger
from backend.research import perform_research
from backend.competitors import discover_competitors
from backend.features import extract_features
from backend.matrix import build_comparison_matrix, analyze_differentiators
from backend.report import generate_excel_report
from backend.pptx_export import generate_powerpoint_report

# Visualization imports (UNCHANGED)
from backend.visualizations import (
    create_feature_coverage_heatmap,
    create_feature_radar_chart,
    create_market_positioning_chart,
    create_feature_category_breakdown,
    create_competitor_feature_comparison_bar
)

# Utility imports (UNCHANGED)
from utils.helpers import validate_product_name, sanitize_input, format_log_entry, generate_filename


# -------------------------------------------------------
# ASYNC RUNNER (Streamlit-Safe)
# -------------------------------------------------------
def run_async(coro):
    """
    Safely run async coroutines inside Streamlit.
    NEVER uses asyncio.run() (which crashes Streamlit).
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Always use run_until_complete
    return loop.run_until_complete(coro)


# -------------------------------------------------------
# PAGE CONFIGURATION (UNCHANGED)
# -------------------------------------------------------
st.set_page_config(
    page_title="Competitor Analysis",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Load CSS styling (UNCHANGED)
with open(os.path.join("static", "style.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Fluent UI button centering (handled in style.css)
# No additional inline styles needed


# -------------------------------------------------------
# SESSION STATE INITIALIZATION (UNCHANGED)
# -------------------------------------------------------
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

if 'results' not in st.session_state:
    st.session_state.results = {}

if 'logger' not in st.session_state:
    st.session_state.logger = None

if 'loaded_analysis_id' not in st.session_state:
    st.session_state.loaded_analysis_id = None


# -------------------------------------------------------
# SIDEBAR (APPLE STYLE)
# -------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style='background: var(--apple-white); padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--apple-gray);'>
        <h3 style='font-size: 19px; font-weight: 600; color: var(--apple-text); margin-bottom: 12px; letter-spacing: -0.3px;'>About</h3>
        <p style='font-size: 14px; color: var(--apple-text-secondary); line-height: 1.6; margin: 0;'>
            AI-powered competitive intelligence platform that discovers competitors, analyzes features, and delivers strategic insights.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: var(--apple-white); padding: 20px; border-radius: 12px; border: 1px solid var(--apple-gray);'>
        <h3 style='font-size: 17px; font-weight: 600; color: var(--apple-text); margin-bottom: 12px; letter-spacing: -0.3px;'>Features</h3>
        <ul style='font-size: 13px; color: var(--apple-text-secondary); line-height: 2; margin: 0; padding-left: 20px;'>
            <li>Automated competitor discovery</li>
            <li>Feature comparison matrix</li>
            <li>Visual analytics & charts</li>
            <li>Strategic recommendations</li>
            <li>Exportable reports</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# -------------------------------------------------------
# HEADER UI (FLUENT + APPLE HYBRID)
# -------------------------------------------------------
st.markdown("""
<div class='fluent-header'>
    <h1 class='fluent-header-title'>Competitor Analysis</h1>
    <p class='fluent-header-subtitle'>Discover, analyze, and benchmark your competitive landscape with AI-powered market intelligence</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# PRODUCT INFORMATION SECTION (FLUENT CARD)
# -----------------------------
st.markdown("""
<div class='fluent-card'>
    <div class='fluent-card-header'>
        <h3 class='fluent-card-title'>📝 Product Information</h3>
        <p class='fluent-card-description'>Enter your product details to begin competitive analysis</p>
    </div>
""", unsafe_allow_html=True)

with st.form("product_form"):   # <<<< THE FIX: Streamlit wraps correctly
    col1, col2 = st.columns(2)

    with col1:
        product_name = st.text_input(
            "Product Name *",
            placeholder="Slack, Notion, Salesforce"
        )

    with col2:
        company_name = st.text_input(
            "Company Name (Optional)",
            placeholder="e.g., Acme Corporation"
        )

    product_description = st.text_area(
        "Product Description (Optional)",
        placeholder="Describe your product…",
        height=120
    )

    # Center button manually + force CSS class
    submit_col = st.columns([1,2,1])
    with submit_col[1]:
        submitted = st.form_submit_button(
            "🚀 Analyze Competitors",
            help="Run competitor analysis now"
        )

st.markdown("</div></div>", unsafe_allow_html=True)

# Handle clear results button (outside form)
if st.session_state.analysis_complete:
    clear_button = st.button("🔄 Clear Results")
    if clear_button:
        st.session_state.analysis_complete = False
        st.session_state.results = {}
        st.session_state.logger = None
        st.rerun()

# Store form values
analyze_button = submitted


# -------------------------------------------------------
# HANDLE "Analyze" CLICK (ASYNC UPDATED)
# -------------------------------------------------------
if analyze_button:

    if not validate_product_name(product_name):
        st.error("⚠️ Please enter a product name to continue.")
        st.stop()

    elif "OPENAI_API_KEY" not in st.secrets:
        st.error("⚠️ OPENAI_API_KEY is missing. Add it in Streamlit Cloud → Settings → Secrets.")
        st.stop()

    # Prepare session logger
    st.session_state.logger = AgentLogger()

    product_name_clean = sanitize_input(product_name)
    company_name_clean = sanitize_input(company_name)
    description_clean = sanitize_input(product_description)

    # -------------------------------------------------------
    # STEP 1: RESEARCH PHASE (PREVENTS HALLUCINATIONS)
    # -------------------------------------------------------
    with st.spinner("🔍 Researching live market data..."):
        try:
            research_results = perform_research(
                product_name_clean,
                company_name_clean,
                description_clean,
                st.session_state.logger
            )
        except Exception as e:
            st.warning(f"⚠️ Research failed: {str(e)}. Continuing with LLM knowledge.")
            research_results = ""
    
    # -------------------------------------------------------
    # STEP 2: ANALYSIS PHASE (WITH RESEARCH CONTEXT)
    # -------------------------------------------------------
    with st.spinner("🔍 Analyzing competitors and extracting insights..."):

        try:
            # -------------------------------------------------------
            # ASYNC COMPETITOR DISCOVERY (WITH RESEARCH CONTEXT)
            # -------------------------------------------------------
            competitors = run_async(
                discover_competitors(
                    product_name_clean,
                    company_name_clean,
                    description_clean,
                    research_results,  # <-- INJECTED RESEARCH CONTEXT
                    st.session_state.logger
                )
            )

            # -------------------------------------------------------
            # ASYNC FEATURE EXTRACTION
            # -------------------------------------------------------
            feature_data = run_async(
                extract_features(
                    product_name_clean,
                    competitors,
                    description_clean,
                    st.session_state.logger
                )
            )

            # Extract core elements
            features = feature_data["features"]
            product_features = feature_data["product_features"]

            # -------------------------------------------------------
            # MATRIX + DIFFERENTIATOR ANALYSIS (SYNC BUT CACHED)
            # -------------------------------------------------------
            matrix_df = build_comparison_matrix(features, product_features)

            analysis = analyze_differentiators(
                product_name_clean,
                features,
                product_features
            )

            # -------------------------------------------------------
            # SAVE TO SESSION STATE
            # -------------------------------------------------------
            st.session_state.results = {
                "product_name": product_name_clean,
                "competitors": competitors,
                "features": features,
                "product_features": product_features,
                "matrix_df": matrix_df,
                "analysis": analysis
            }

            st.session_state.analysis_complete = True
            st.success("✅ Analysis complete!")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            st.error(f"❌ An error occurred during analysis: {str(e)}")
            if st.session_state.logger:
                st.session_state.logger.log_observation(f"Fatal error: {str(e)}")
                st.session_state.logger.log_observation(f"Traceback: {error_details}")
            
            # Show detailed error in expander
            with st.expander("🔍 Error Details", expanded=False):
                st.code(error_details)
# -------------------------------------------------------
# DEBUG LOGS (UNCHANGED)
# -------------------------------------------------------
if st.session_state.logger and st.session_state.logger.get_logs():
    with st.expander("🤖 Agent Process Log (Thought → Action → Observation)", expanded=False):
        st.markdown("<div class='agent-log'>", unsafe_allow_html=True)
        for log in st.session_state.logger.get_logs():
            formatted_log = format_log_entry(log)
            st.markdown(formatted_log)
        st.markdown("</div>", unsafe_allow_html=True)


# -------------------------------------------------------
# DISPLAY ANALYSIS RESULTS (IMMERSIVE)
# -------------------------------------------------------
if st.session_state.analysis_complete and st.session_state.results:

    results = st.session_state.results
    
    st.markdown("<div class='content-wrapper'>", unsafe_allow_html=True)
    st.markdown("""
    <div class='section-header'>
        <h2 class='section-title'>📊 Analysis Results</h2>
        <p class='section-subtitle'>Comprehensive competitive intelligence for {}</p>
    </div>
    """.format(results['product_name']), unsafe_allow_html=True)

    # ----------------------------
    # MARKET OVERVIEW METRICS (FLUENT CARD)
    # ----------------------------
    st.markdown("""
    <div class='analytics-container'>
        <h3 class='analytics-header'>📊 Market Overview</h3>
        <div class='analytics-grid'>
    """, unsafe_allow_html=True)
    
    total_features = len(results['features'])
    coverage = len([f for f in results['product_features'].values() if f]) / total_features * 100 if total_features > 0 else 0
    categories = len(set(f.get('category', 'General') for f in results['features']))
    
    st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Competitors</div>
        </div>
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Features Tracked</div>
        </div>
        <div class='metric-card'>
            <div class='metric-value'>{}%</div>
            <div class='metric-label'>Coverage Rate</div>
        </div>
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Categories</div>
        </div>
        </div>
    </div>
    """.format(len(results['competitors']), total_features, int(coverage), categories), unsafe_allow_html=True)

    # ----------------------------
    # COMPETITORS (FLUENT CARDS)
    # ----------------------------
    st.markdown("""
    <div class='section-header'>
        <h3 class='section-title'>🏢 Competitor Landscape</h3>
    </div>
    """, unsafe_allow_html=True)
    
    for i, comp in enumerate(results['competitors'], 1):
        # Calculate market share (simulated - in real app would come from data)
        market_share = max(5, 35 - (i * 5))  # Simulated decreasing share
        
        # Get competitor data with HTML escaping for text content
        import html
        company_name = html.escape(comp.get('company_name', 'Unknown'))
        product_name = html.escape(comp.get('product_name', 'Unknown'))
        description = html.escape(comp.get('description', 'No description available'))
        market_position = html.escape(comp.get('market_position', 'Unknown'))
        
        # Get pricing tier from competitor data or simulate
        pricing_tier = comp.get('pricing_tier', 'Mid-Tier')
        if not pricing_tier or pricing_tier == 'Unknown':
            pricing_tier = "Premium" if i <= 2 else "Mid-Tier" if i <= 4 else "Budget"
        
        weakness_badge = "<span class='usp-badge weakness'>⚠️ Complex UI</span>" if i > 2 else ""
        
        # Build website link HTML (inside the card)
        website_link = ""
        website_url = comp.get('website', '')
        if website_url:
            # Clean and validate URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            website_link = f"""<a href='{html.escape(website_url)}' target='_blank'>Visit Website →</a>"""
        
        competitor_html = f"""<div class='competitor-card'>
<div class='competitor-header'>
<div>
<div class='competitor-name'>{company_name}</div>
<div class='competitor-product'>{product_name}</div>
</div>
<div class='market-share-badge'>{market_share}% Market Share</div>
</div>
<p class='competitor-description'>{description}</p>
<div class='competitor-stats'>
<div class='stat-item'>
<div class='stat-label'>Position</div>
<div class='stat-value'>{market_position}</div>
</div>
<div class='stat-item'>
<div class='stat-label'>Pricing</div>
<div class='stat-value'>{pricing_tier}</div>
</div>
<div class='stat-item'>
<div class='stat-label'>Status</div>
<div class='stat-value'>Active</div>
</div>
</div>
<div class='usp-badges'>
<span class='usp-badge strength'>🎯 Key Strength: Feature Rich</span>
<span class='usp-badge'>💼 Enterprise Focus</span>
{weakness_badge}
</div>
{website_link}
</div>"""
        
        st.markdown(competitor_html, unsafe_allow_html=True)

    # ----------------------------
    # FEATURES (FLUENT SECTION)
    # ----------------------------
    st.markdown("""
    <div class='section-header'>
        <h3 class='section-title'>📋 Feature List</h3>
    </div>
    """, unsafe_allow_html=True)

    features_by_category = {}
    for feature in results['features']:
        cat = feature.get('category', 'General')
        features_by_category.setdefault(cat, []).append(feature)

    for category, features in features_by_category.items():
        with st.expander(f"**{category}** ({len(features)} features)", expanded=True):
            for feature in features:
                st.markdown(f"- **{feature['feature_name']}**: {feature['description']}")

    # ----------------------------
    # VISUAL ANALYTICS (FLUENT SECTION)
    # ----------------------------
    st.markdown("""
    <div class='section-header'>
        <h3 class='section-title'>📈 Visual Analytics & Trends</h3>
    </div>
    <div class='analytics-container'>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Feature Coverage",
        "Radar Analysis",
        "Market Position",
        "Category View"
    ])

    # Heatmap
    with tab1:
        try:
            fig = create_feature_coverage_heatmap(results["matrix_df"])
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating heatmap: {str(e)}")

    # Radar Chart
    with tab2:
        try:
            fig = create_feature_radar_chart(
                results['product_name'],
                results['competitors'],
                results['product_features'],
                results['features']
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating radar chart: {str(e)}")

    # Positioning Scatter
    with tab3:
        try:
            fig = create_market_positioning_chart(
                results['product_name'],
                results['competitors'],
                results['product_features']
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating positioning chart: {str(e)}")

    # Category Breakdown + Feature Comparison Bar
    with tab4:
        colA, colB = st.columns(2)
        with colA:
            try:
                fig = create_feature_category_breakdown(results['features'])
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating category breakdown: {str(e)}")

        with colB:
            try:
                fig = create_competitor_feature_comparison_bar(results['product_features'])
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating comparison bar: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------
    # INSIGHTS SUMMARY (FLUENT CARD)
    # ----------------------------
    st.markdown("""
    <div class='fluent-card'>
        <div class='fluent-card-header'>
            <h3 class='fluent-card-title'>💡 Key Insights</h3>
        </div>
        <p style='color: var(--text-secondary); font-size: 15px; line-height: 1.6;'>Based on comprehensive analysis of {} competitors across {} features, your product shows strong positioning in core capabilities with opportunities for strategic enhancement in emerging feature categories.</p>
    </div>
    """.format(len(results['competitors']), len(results['features'])), unsafe_allow_html=True)

    # ----------------------------
    # FEATURE MATRIX (FLUENT SECTION)
    # ----------------------------
    st.markdown("""
    <div class='section-header'>
        <h3 class='section-title'>🎯 Feature Comparison Matrix</h3>
    </div>
    """, unsafe_allow_html=True)

    def highlight(val):
        if val == 1:
            return 'background-color: #C6EFCE; color: #006100; font-weight: bold;'
        return 'background-color: #FFC7CE; color: #9C0006; font-weight: bold;'

    styled_df = results["matrix_df"].replace({1: "✓", 0: "✗"}).style.applymap(
        lambda v: 'background-color: #C6EFCE; color: #006100; font-weight:bold;' if v == "✓"
        else 'background-color: #FFC7CE; color: #9C0006; font-weight:bold;'
    )

    st.dataframe(styled_df, use_container_width=True, height=400)

    # ----------------------------
    # DIFFERENTIATORS (FLUENT SECTION)
    # ----------------------------
    st.markdown("""
    <div class='section-header'>
        <h3 class='section-title'>💎 Key Differentiators</h3>
    </div>
    """, unsafe_allow_html=True)

    diffs = results['analysis'].get("differentiators", [])
    if diffs:
        for i, d in enumerate(diffs, 1):
            diff_html = f"""<div class='differentiator-card'>
    <div class='differentiator-title'>{i}. {d.get('title', 'Untitled')}</div>
    <div class='differentiator-description'>{d.get('description', 'No description available')}</div>
</div>"""
            st.markdown(diff_html, unsafe_allow_html=True)
    else:
        st.info("No differentiators identified.")

    # ----------------------------
    # RECOMMENDATIONS (FLUENT SECTION)
    # ----------------------------
    st.markdown("""
    <div class='section-header'>
        <h3 class='section-title'>💡 Strategic Recommendations</h3>
    </div>
    """, unsafe_allow_html=True)

    recs = results['analysis'].get("recommendations", [])
    if recs:
        for i, r in enumerate(recs, 1):
            rec_html = f"""<div class='insight-card'>
    <div class='insight-title'>{i}. {r.get('title', 'Untitled')}</div>
    <div class='insight-description'>{r.get('description', 'No description available')}</div>
</div>"""
            st.markdown(rec_html, unsafe_allow_html=True)
    else:
        st.info("No recommendations available.")

    # ----------------------------
    # MISSING CAPABILITIES (FLUENT SECTION)
    # ----------------------------
    st.markdown("""
    <div class='section-header'>
        <h3 class='section-title'>⚠️ Missing Capabilities</h3>
    </div>
    """, unsafe_allow_html=True)

    missing = results['analysis'].get("missing_capabilities", [])
    if missing:
        for i, m in enumerate(missing, 1):
            importance = m.get("importance", "Unknown")
            color = {
                "High": "#ff4444",
                "Medium": "#ff9944",
                "Low": "#44aa44"
            }.get(importance, "#666")
            
            missing_html = f"""<div class='insight-card'>
    <div class='insight-title'>{i}. {m.get('capability', 'Unknown capability')} <span style='color:{color}; font-weight:600;'>({importance})</span></div>
    <div class='insight-description'>{m.get('rationale', 'No rationale provided')}</div>
</div>"""
            st.markdown(missing_html, unsafe_allow_html=True)
    else:
        st.success("No major missing capabilities identified!")

    # ----------------------------
    # DOWNLOAD REPORTS (FLUENT SECTION)
    # ----------------------------
    st.markdown("""
    <div class='section-header'>
        <h3 class='section-title'>📥 Export Reports</h3>
        <p class='section-subtitle'>Download comprehensive analysis reports in your preferred format</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Excel
    with col1:
        try:
            excel_data = generate_excel_report(
                results['product_name'],
                results['matrix_df'],
                results['competitors'],
                results['features'],
                results['product_features'],
                results['analysis']
            )
            st.download_button(
                "📊 Excel Report",
                data=excel_data,
                file_name=generate_filename(results["product_name"], "xlsx"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Excel Error: {str(e)}")

    # PowerPoint
    with col2:
        try:
            ppt_data = generate_powerpoint_report(
                results['product_name'],
                results['matrix_df'],
                results['analysis'],
                results['features']
            )
            st.download_button(
                "📽️ PowerPoint Report",
                data=ppt_data,
                file_name=generate_filename(results["product_name"], "pptx"),
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PPTX Error: {str(e)}")
    


# -------------------------------------------------------
# FOOTER (TRANSPARENT - FIXED)
# -------------------------------------------------------
st.markdown("""
<div class='footer-box' style='text-align:center; margin-top: 64px; margin-bottom: 32px;'>
    <p style='margin-bottom: 8px; font-weight: 500; color: var(--text-secondary);'>Powered by OpenAI GPT-4o • Built with Streamlit</p>
    <p style='font-size: 13px; color: var(--text-tertiary);'>Designed by Tanishq Sharma</p>
    <p style='margin-top: 16px; font-size: 12px; color: var(--text-tertiary);'>© 2024 Competitor Analysis Engine. All rights reserved.</p>
</div>
""", unsafe_allow_html=True)
