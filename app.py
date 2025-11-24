import streamlit as st
import os
import pandas as pd
import asyncio
import nest_asyncio

nest_asyncio.apply()

# Backend imports (ASYNC + optimized backend)
from backend.llm import AgentLogger
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
    page_title="AI Competitor Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS styling (UNCHANGED)
with open(os.path.join("static", "style.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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
# SIDEBAR (UNCHANGED)
# -------------------------------------------------------
with st.sidebar:
    st.markdown("## 📝 About")
    st.info("This app analyzes competitors using AI and generates insights, charts, and reports.")


# -------------------------------------------------------
# HEADER UI (UNCHANGED)
# -------------------------------------------------------
st.markdown("<div class='main-header'>", unsafe_allow_html=True)
st.title("🎯 AI-Powered Competitor Analysis")
st.markdown("Discover competitors, compare features, and gain strategic insights powered by AI")
st.markdown("</div>", unsafe_allow_html=True)


# -------------------------------------------------------
# PRODUCT INPUT SECTION (UNCHANGED UI)
# -------------------------------------------------------
with st.container():
    st.markdown("### 📝 Product Information")

    col1, col2 = st.columns(2)

    with col1:
        product_name = st.text_input(
            "Product Name *",
            placeholder="e.g., Slack, Notion, Salesforce",
            help="Enter the name of your product or the product you want to analyze"
        )

    with col2:
        company_name = st.text_input(
            "Company Name (Optional)",
            placeholder="e.g., Acme Corporation",
            help="Enter your company name if applicable"
        )

    product_description = st.text_area(
        "Product Description (Optional)",
        placeholder="Briefly describe what your product does, its key value proposition, and target market...",
        help="Providing more context helps generate more accurate competitor analysis",
        height=100
    )

    st.markdown("---")

    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        analyze_button = st.button("🚀 Analyze Competitors", type="primary", use_container_width=True)

    with col_btn2:
        if st.session_state.analysis_complete:
            clear_button = st.button("🔄 Clear Results", use_container_width=True)
            if clear_button:
                st.session_state.analysis_complete = False
                st.session_state.results = {}
                st.session_state.logger = None
                st.rerun()


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

    with st.spinner("🔍 Analyzing competitors and extracting insights..."):

        try:
            # -------------------------------------------------------
            # ASYNC COMPETITOR DISCOVERY
            # -------------------------------------------------------
            competitors = run_async(
                discover_competitors(
                    product_name_clean,
                    company_name_clean,
                    description_clean,
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
            st.error(f"❌ An error occurred during analysis: {str(e)}")
            st.session_state.logger.log_observation(f"Fatal error: {str(e)}")
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
# DISPLAY ANALYSIS RESULTS (UNCHANGED UI)
# -------------------------------------------------------
if st.session_state.analysis_complete and st.session_state.results:

    results = st.session_state.results

    st.markdown("---")
    st.markdown("## 📊 Analysis Results")

    # ----------------------------
    # COMPETITORS
    # ----------------------------
    st.markdown("### 🏢 Competitors Identified")
    st.markdown(f"Found **{len(results['competitors'])}** direct competitors for **{results['product_name']}**")

    for i, comp in enumerate(results['competitors'], 1):
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{i}. {comp.get('company_name', 'Unknown')}** - {comp.get('product_name', 'Unknown')}")
                st.caption(comp.get('description', 'No description available'))
            with col2:
                st.markdown(f"_{comp.get('market_position', 'Unknown')}_")
                if comp.get('website'):
                    st.markdown(f"[🔗 Website]({comp.get('website')})")

    # ----------------------------
    # FEATURES
    # ----------------------------
    st.markdown("---")
    st.markdown("### 📋 Feature List")

    features_by_category = {}
    for feature in results['features']:
        cat = feature.get('category', 'General')
        features_by_category.setdefault(cat, []).append(feature)

    for category, features in features_by_category.items():
        with st.expander(f"**{category}** ({len(features)} features)", expanded=True):
            for feature in features:
                st.markdown(f"- **{feature['feature_name']}**: {feature['description']}")

    # ----------------------------
    # VISUAL ANALYTICS (UNCHANGED)
    # ----------------------------
    st.markdown("---")
    st.markdown("### 📈 Visual Analytics")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Feature Coverage Heatmap",
        "🎯 Radar Chart",
        "📍 Market Positioning",
        "🥧 Category Breakdown"
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

    # ----------------------------
    # FEATURE MATRIX (UNCHANGED)
    # ----------------------------
    st.markdown("---")
    st.markdown("### 🎯 Feature Comparison Matrix")

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
    # DIFFERENTIATORS (RESTORED ORIGINAL FORMAT)
    # ----------------------------
    st.markdown("---")
    st.markdown("### 💎 Key Differentiators")

    diffs = results['analysis'].get("differentiators", [])
    if diffs:
        for i, d in enumerate(diffs, 1):
            st.markdown(f"""
            <div class='differentiator-card'>
                <strong>{i}. {d.get('title')}</strong><br>
                {d.get('description')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No differentiators identified.")

    # ----------------------------
    # RECOMMENDATIONS
    # ----------------------------
    st.markdown("---")
    st.markdown("### 💡 Strategic Recommendations")

    recs = results['analysis'].get("recommendations", [])
    if recs:
        for i, r in enumerate(recs, 1):
            st.markdown(f"""
            <div class='recommendation-card'>
                <strong>{i}. {r.get('title')}</strong><br>
                {r.get('description')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recommendations available.")

    # ----------------------------
    # MISSING CAPABILITIES
    # ----------------------------
    st.markdown("---")
    st.markdown("### ⚠️ Missing Capabilities")

    missing = results['analysis'].get("missing_capabilities", [])
    if missing:
        for i, m in enumerate(missing, 1):
            importance = m.get("importance", "Unknown")
            color = {
                "High": "#ff4444",
                "Medium": "#ff9944",
                "Low": "#44aa44"
            }.get(importance, "#666")

            st.markdown(f"""
            <div class='missing-capability-card'>
                <strong>{i}. {m.get('capability')}</strong>
                <span style='color:{color}; font-weight:bold;'>({importance})</span><br>
                {m.get('rationale')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No major missing capabilities identified!")

    # ----------------------------
    # DOWNLOAD REPORTS
    # ----------------------------
    st.markdown("---")
    st.markdown("### 📥 Download Reports")

    col1, col2 = st.columns(2)

    # Excel
    with col1:
        try:
            excel_data = generate_excel_report(
                results['product_name'],
                results['matrix_df']
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
                results['matrix_df']
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
# FOOTER (UNCHANGED)
# -------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#666; font-size:0.9rem; padding:2rem 0;'>
    <p>Powered by OpenAI • Built with Streamlit</p>
    <p>Designed by Tanishq Sharma</p>
</div>
""", unsafe_allow_html=True)
