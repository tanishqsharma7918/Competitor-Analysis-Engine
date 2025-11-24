import streamlit as st
import pandas as pd
from typing import Dict, Any, List
import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment


@st.cache_data(show_spinner=False)
def generate_excel_report(
    product_name: str,
    matrix_df: pd.DataFrame,
    competitors: List[Dict[str, Any]],
    features: List[Dict[str, Any]],
    product_features: Dict[str, List[str]],
    analysis: Dict[str, Any]
) -> bytes:
    """
    FULL detailed Excel export with 5 worksheets:
    Overview, Competitors, Features, Matrix, Analysis
    """

    wb = Workbook()

    # ---------------------------------------------------
    # 1️⃣ Sheet: Overview
    # ---------------------------------------------------
    ws = wb.active
    ws.title = "Overview"

    ws["A1"] = f"Competitor Analysis Report — {product_name}"
    ws["A1"].font = Font(size=16, bold=True)

    ws.append(["Product Name", product_name])
    ws.append(["Total Competitors", len(competitors)])
    ws.append(["Total Features", len(features)])

    ws.append([])

    # Differentiators summary
    ws.append(["Key Differentiators"])
    diffs = analysis.get("differentiators", [])
    for d in diffs:
        ws.append([f"- {d.get('title')}: {d.get('description')}"])

    ws.append([])

    # Recommendations summary
    ws.append(["Recommendations"])
    recs = analysis.get("recommendations", [])
    for r in recs:
        ws.append([f"- {r.get('title')}: {r.get('description')}"])

    # ---------------------------------------------------
    # 2️⃣ Competitors Sheet
    # ---------------------------------------------------
    ws2 = wb.create_sheet("Competitors")
    ws2.append(["Company Name", "Product", "Description", "Website", "Market Position"])

    for c in competitors:
        ws2.append([
            c.get("company_name", ""),
            c.get("product_name", ""),
            c.get("description", ""),
            c.get("website", ""),
            c.get("market_position", "")
        ])

    # ---------------------------------------------------
    # 3️⃣ Features Sheet
    # ---------------------------------------------------
    ws3 = wb.create_sheet("Features")
    ws3.append(["Feature Name", "Category", "Description"])

    for f in features:
        ws3.append([
            f.get("feature_name", ""),
            f.get("category", ""),
            f.get("description", "")
        ])

    # ---------------------------------------------------
    # 4️⃣ Matrix Sheet
    # ---------------------------------------------------
    ws4 = wb.create_sheet("Feature Matrix")
    ws4.append(["Product"] + list(matrix_df.columns))

    for product, row in matrix_df.iterrows():
        ws4.append([product] + list(row.values))

    # ---------------------------------------------------
    # 5️⃣ Analysis Sheet
    # ---------------------------------------------------
    ws5 = wb.create_sheet("Analysis")
    ws5.append(["Differentiators"])
    for d in analysis.get("differentiators", []):
        ws5.append([d.get("title"), d.get("description")])

    ws5.append([])
    ws5.append(["Gaps"])
    for g in analysis.get("gaps", []):
        ws5.append([g.get("title"), g.get("description")])

    ws5.append([])
    ws5.append(["Recommendations"])
    for r in analysis.get("recommendations", []):
        ws5.append([r.get("title"), r.get("description")])

    # ---------------------------------------------------
    # Return Excel bytes
    # ---------------------------------------------------
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
