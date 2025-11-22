import streamlit as st
import os
import pandas as pd
from backend.llm import AgentLogger
from backend.competitors import discover_competitors
from backend.features import extract_features
from backend.report import generate_excel_report
from backend.matrix import build_comparison_matrix, analyze_differentiators
from backend.pptx_export import generate_powerpoint_report
from backend.visualizations import (
    create_feature_coverage_heatmap,
    create_feature_radar_chart,
    create_market_positioning_chart,
    create_feature_category_breakdown,
    create_competitor_feature_comparison_bar
)
from utils.helpers import validate_product_name, sanitize_input, format_log_entry, generate_filename


st.set_page_config(
    page_title="AI Competitor Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)


with open(os.path.join("static", "style.css")) as f:

    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'logger' not in st.session_state:
    st.session_state.logger = None
if 'loaded_analysis_id' not in st.session_state:
    st.session_state.loaded_analysis_id = None

with st.sidebar:
    st.markdown("## 📝 About")
    st.info("This app analyzes competitors using AI and generates insights, charts, and reports.")

st.markdown("<div class='main-header'>", unsafe_allow_html=True)
st.title("🎯 AI-Powered Competitor Analysis")
st.markdown("Discover competitors, compare features, and gain strategic insights powered by AI")
st.markdown("</div>", unsafe_allow_html=True)

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
    
    col_btn1, col_btn2 = st.columns([1, 1,])
    
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

if analyze_button:
    if not validate_product_name(product_name):
        st.error("⚠️ Please enter a product name to continue.")
    elif "OPENAI_API_KEY" not in st.secrets:
        st.error("⚠️ OPENAI_API_KEY is missing. Add it in Streamlit Cloud → Settings → Secrets.")

    else:
        st.session_state.analysis_complete = False
        st.session_state.logger = AgentLogger()
        
        product_name_clean = sanitize_input(product_name)
        company_name_clean = sanitize_input(company_name)
        description_clean = sanitize_input(product_description)
        
        with st.spinner("🔍 Analyzing competitors and extracting insights..."):
            try:
                competitors = discover_competitors(
                    product_name_clean,
                    company_name_clean,
                    description_clean,
                    st.session_state.logger
                )
                
                feature_data = extract_features(
                    product_name_clean,
                    competitors,
                    description_clean,
                    st.session_state.logger
                )
                
                matrix_df = build_comparison_matrix(
                    product_name_clean,
                    feature_data["features"],
                    feature_data["product_features"],
                    st.session_state.logger
                )
                
                analysis = analyze_differentiators(
                    product_name_clean,
                    competitors,
                    feature_data["features"],
                    feature_data["product_features"],
                    st.session_state.logger
                )
                
                st.session_state.results = {
                    "product_name": product_name_clean,
                    "competitors": competitors,
                    "features": feature_data["features"],
                    "product_features": feature_data["product_features"],
                    "matrix_df": matrix_df,
                    "analysis": analysis
                }
                
                st.success("✅ Analysis complete!")
                st.session_state.analysis_complete = True
                
            except Exception as e:
                st.error(f"❌ An error occurred during analysis: {str(e)}")
                if st.session_state.logger:
                    st.session_state.logger.log_observation(f"Fatal error: {str(e)}")

if st.session_state.logger and st.session_state.logger.get_logs():
    with st.expander("🤖 Agent Process Log (Thought → Action → Observation)", expanded=False):
        st.markdown("<div class='agent-log'>", unsafe_allow_html=True)
        for log in st.session_state.logger.get_logs():
            formatted_log = format_log_entry(log)
            st.markdown(formatted_log)
        st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.analysis_complete and st.session_state.results:
    results = st.session_state.results
    
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")
    
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
    
    st.markdown("---")
    st.markdown("### 📋 Feature List")
    
    features_by_category = {}
    for feature in results['features']:
        category = feature.get('category', 'General')
        if category not in features_by_category:
            features_by_category[category] = []
        features_by_category[category].append(feature)
    
    for category, features in features_by_category.items():
        with st.expander(f"**{category}** ({len(features)} features)", expanded=True):
            for feature in features:
                st.markdown(f"- **{feature.get('feature_name', '')}**: {feature.get('description', '')}")
    
    st.markdown("---")
    st.markdown("### 📈 Visual Analytics")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Feature Coverage Heatmap", "🎯 Radar Chart", "📍 Market Positioning", "🥧 Category Breakdown"])
    
    with tab1:
        try:
            fig_heatmap = create_feature_coverage_heatmap(results['matrix_df'])
            st.plotly_chart(fig_heatmap, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating heatmap: {str(e)}")
    
    with tab2:
        try:
            fig_radar = create_feature_radar_chart(
                results['product_name'],
                results['competitors'],
                results['product_features'],
                results['features']
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating radar chart: {str(e)}")
    
    with tab3:
        try:
            fig_positioning = create_market_positioning_chart(
                results['product_name'],
                results['competitors'],
                results['product_features']
            )
            st.plotly_chart(fig_positioning, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating positioning chart: {str(e)}")
    
    with tab4:
        col_a, col_b = st.columns(2)
        with col_a:
            try:
                fig_category = create_feature_category_breakdown(results['features'])
                st.plotly_chart(fig_category, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating category breakdown: {str(e)}")
        with col_b:
            try:
                fig_bar = create_competitor_feature_comparison_bar(results['product_features'])
                st.plotly_chart(fig_bar, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating comparison bar: {str(e)}")
    
    st.markdown("---")
    st.markdown("### 🎯 Feature Comparison Matrix")
    
    def highlight_cells(val):
        if val == "✓":
            return 'background-color: #C6EFCE; color: #006100; font-weight: bold;'
        elif val == "✗":
            return 'background-color: #FFC7CE; color: #9C0006; font-weight: bold;'
        return ''
    
    styled_df = results['matrix_df'].style.applymap(highlight_cells)
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    st.markdown("---")
    st.markdown("### 💎 Key Differentiators")
    
    differentiators = results['analysis'].get('differentiators', [])
    if differentiators:
        for i, diff in enumerate(differentiators, 1):
            st.markdown(f"""
            <div class='differentiator-card'>
                <strong>{i}. {diff.get('title', '')}</strong><br>
                {diff.get('description', '')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No specific differentiators identified.")
    
    st.markdown("---")
    st.markdown("### 💡 Strategic Recommendations")
    
    recommendations = results['analysis'].get('recommendations', [])
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"""
            <div class='recommendation-card'>
                <strong>{i}. {rec.get('title', '')}</strong><br>
                {rec.get('description', '')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recommendations available.")
    
    st.markdown("---")
    st.markdown("### ⚠️ Missing Capabilities")
    
    missing = results['analysis'].get('missing_capabilities', [])[:5]
    if missing:
        for i, miss in enumerate(missing, 1):
            importance = miss.get('importance', 'Unknown')
            importance_color = {
                'High': '#ff4444',
                'Medium': '#ff9944',
                'Low': '#44aa44'
            }.get(importance, '#666666')
            
            st.markdown(f"""
            <div class='missing-capability-card'>
                <strong>{i}. {miss.get('capability', '')}</strong> 
                <span style='color: {importance_color}; font-weight: bold;'>({importance} Importance)</span><br>
                {miss.get('rationale', '')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No critical missing capabilities identified!")
    
    st.markdown("---")
    st.markdown("### 📥 Download Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            excel_data = generate_excel_report(
                results['product_name'],
                results['competitors'],
                results['matrix_df'],
                results['analysis'],
                results['features']
            )
            
            excel_filename = generate_filename(results['product_name'], 'xlsx')
            
            st.download_button(
                label="📊 Excel",
                data=excel_data,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generating Excel: {str(e)}")
    

    
    with col3:
        try:
            pptx_data = generate_powerpoint_report(
                results['product_name'],
                results['competitors'],
                results['matrix_df'],
                results['analysis'],
                results['features']
            )
            
            pptx_filename = generate_filename(results['product_name'], 'pptx')
            
            st.download_button(
                label="📽️ PowerPoint",
                data=pptx_data,
                file_name=pptx_filename,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generating PowerPoint: {str(e)}")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem; padding: 2rem 0;'>
    <p>Powered by OpenAI GPT-5 • Built with Streamlit</p>
    <p>Designed by Tanishq Sharma</p>
</div>
""", unsafe_allow_html=True)
