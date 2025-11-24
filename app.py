import streamlit as st
import asyncio
import pandas as pd

from backend.llm import AgentLogger
from backend.competitors import discover_competitors
from backend.features import extract_features
from backend.matrix import build_comparison_matrix, analyze_differentiators
from backend.report import generate_excel_report, generate_powerpoint_report, generate_pdf_report


# -------------------------------------------------------
# ASYNC RUNNER (Very important for Streamlit)
# This allows running async code inside Streamlit safely.
# -------------------------------------------------------
def run_async(coro):
    """Run async code inside Streamlit without crash."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        return asyncio.run(coro)
    else:
        return loop.run_until_complete(coro)


# -------------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------------
st.set_page_config(page_title="AI Competitor Analysis", layout="wide")

st.title("AI Competitor Analysis Engine")
st.write("Upload product details and generate competitor insights in minutes — now optimized!")


# -------------------------------------------------------
# INPUT FIELDS
# -------------------------------------------------------
product_name = st.text_input("Product Name")
company_name = st.text_input("Company Name (Optional)")
description = st.text_area("Product Description")

start_btn = st.button("Run Analysis", type="primary")


# -------------------------------------------------------
# MAIN ANALYSIS LOGIC (ASYNC)
# -------------------------------------------------------
if start_btn:

    if not product_name:
        st.error("Please enter a product name.")
        st.stop()

    # Enable progress logs
    logger = AgentLogger()

    with st.spinner("Running intelligent competitor analysis..."):
        
        # ------------------------------
        # 1. ASYNC COMPETITOR DISCOVERY
        # ------------------------------
        competitors = run_async(
            discover_competitors(
                product_name=product_name,
                company_name=company_name,
                description=description,
                logger=logger
            )
        )

        # ------------------------------
        # 2. ASYNC FEATURE EXTRACTION
        # ------------------------------
        feature_data = run_async(
            extract_features(
                product_name=product_name,
                competitors=competitors,
                description=description,
                logger=logger
            )
        )

        # ------------------------------
        # 3. MATRIX + DIFFERENTIATORS
        #    (Cached → VERY FAST)
        # ------------------------------
        features = feature_data["features"]
        product_features = feature_data["product_features"]

        matrix_df = build_comparison_matrix(features, product_features)
        analysis = analyze_differentiators(product_name, features, product_features)

    # -------------------------------------------------------
    # DISPLAY RESULTS
    # -------------------------------------------------------
    st.subheader("🧩 Competitors Identified")
    st.write(pd.DataFrame(competitors))

    st.subheader("🔑 Extracted Key Features")
    st.write(pd.DataFrame(features))

    st.subheader("📊 Comparison Matrix")
    st.dataframe(matrix_df)

    st.subheader("🎯 Differentiator Analysis")
    st.write(analysis)

    # -------------------------------------------------------
    # EXPORT OPTIONS
    # -------------------------------------------------------
    st.subheader("📥 Download Reports")

    excel_bytes = generate_excel_report(product_name, matrix_df)
    ppt_bytes = generate_powerpoint_report(product_name, matrix_df)
    pdf_bytes = generate_pdf_report(product_name, matrix_df)

    st.download_button(
        label="Download Excel Report",
        data=excel_bytes,
        file_name=f"{product_name}_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.download_button(
        label="Download PowerPoint Report",
        data=ppt_bytes,
        file_name=f"{product_name}_analysis.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )

    st.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name=f"{product_name}_analysis.pdf",
        mime="application/pdf",
    )


# -------------------------------------------------------
# DEBUG LOGS DISPLAY (OPTIONAL)
# -------------------------------------------------------
with st.expander("🔍 Debug Logs"):
    st.text("\n".join(logger.logs))
