# app.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import base64

# ------------------ CONFIG ------------------
st.set_page_config(page_title="DataLens - Auto Insights Generator", layout="wide")

st.title("📊 DataLens → Auto Insights & Report Generator")

# ------------------ ABOUT / HEADER SECTION ------------------
st.markdown(
    """
    <div style='text-align: center; margin-top: 10px;'>
    """,
    unsafe_allow_html=True
)

st.header("**From data to decisions—instantly.**")

st.markdown(
    """
    __This webapp has been created in Python by [Yawar Ali](https://github.com/datacanvas7/).__
    
    __DataLens - Auto Insights Generator__ is a Streamlit-based application for automated insights generator for your datasets.

    It helps users instantly generate insights, detect data quality issues, and visualize patterns without writing code.

    *Libraries used: `Streamlit`, `Pandas`, `NumPy`, `Matplotlib`, `Seaborn`*
    """,
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)

# ------------------ SIDEBAR ------------------
st.sidebar.header("⚙️ Settings")
show_heatmap = st.sidebar.checkbox("Show Correlation Heatmap", True)
show_distributions = st.sidebar.checkbox("Show Distributions", False)

# ------------------ FILE UPLOAD ------------------
uploaded_file = st.file_uploader("Upload Your Excel file", type=["csv", "xlsx"])

df = None

if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1]

    if file_type == "csv":
        df = pd.read_csv(uploaded_file)

    elif file_type == "xlsx":
        excel_file = pd.ExcelFile(uploaded_file)
        sheet = st.selectbox("📑 Select Sheet", excel_file.sheet_names)
        df = pd.read_excel(excel_file, sheet_name=sheet)

# ------------------ MAIN ------------------
if df is not None:

    # -------- PREVIEW --------
    st.markdown("### 🔍 Dataset Preview")
    st.dataframe(df.head(), use_container_width=True)

    # -------- BASIC INFO --------
    st.markdown("### 📌 Basic Info")
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", df.shape[0])
    col2.metric("Columns", df.shape[1])
    col3.metric("Missing Values", int(df.isnull().sum().sum()))

    # -------- DATA TYPES --------
    st.markdown("### 📂 Data Types")
    st.dataframe(df.dtypes.astype(str))

    # -------- MISSING --------
    st.markdown("### ⚠️ Missing Values")
    missing = df.isnull().sum()
    missing = missing[missing > 0]

    if not missing.empty:
        st.dataframe(missing)
    else:
        st.success("No missing values 🎉")

    # -------- NUMERIC --------
    numeric_df = df.select_dtypes(include=np.number)

    st.markdown("### 📈 Statistical Summary")
    if not numeric_df.empty:
        st.dataframe(numeric_df.describe())
    else:
        st.warning("No numeric columns found.")

    # -------- HEATMAP --------
    if show_heatmap and not numeric_df.empty:
        st.markdown("### 🔥 Correlation Heatmap")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)

    # -------- DISTRIBUTIONS --------
    if show_distributions and not numeric_df.empty:
        st.markdown("### 📊 Distributions")
        for col in numeric_df.columns:
            fig, ax = plt.subplots()
            sns.histplot(numeric_df[col], kde=True, ax=ax)
            ax.set_title(col)
            st.pyplot(fig)

    # ------------------ INSIGHTS ------------------
    st.markdown("### 🧠 Auto Insights")
    insights = []

    # Missing
    if df.isnull().sum().sum() > 0:
        insights.append("Dataset contains missing values.")

    # Correlation
    if not numeric_df.empty:
        corr = numeric_df.corr().abs()
        if (corr.values.sum() - len(corr)) > 0:
            if (corr > 0.8).sum().sum() > len(corr):
                insights.append("High correlation detected (>0.8).")

    # Skewness
    if not numeric_df.empty:
        skewed = numeric_df.skew()
        skew_cols = skewed[abs(skewed) > 1].index.tolist()
        if skew_cols:
            insights.append(f"Skewed columns: {', '.join(skew_cols)}")

    # Duplicates
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        insights.append(f"{duplicate_count} duplicate rows detected.")

    # Constant Columns
    constant_cols = [col for col in df.columns if df[col].nunique() <= 1]
    if constant_cols:
        insights.append(f"Constant columns: {', '.join(constant_cols)}")

    # Outliers (IQR method)
    outlier_cols = []
    if not numeric_df.empty:
        for col in numeric_df.columns:
            Q1 = numeric_df[col].quantile(0.25)
            Q3 = numeric_df[col].quantile(0.75)
            IQR = Q3 - Q1

            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            if ((numeric_df[col] < lower) | (numeric_df[col] > upper)).sum() > 0:
                outlier_cols.append(col)

    if outlier_cols:
        insights.append(f"Outliers detected in: {', '.join(outlier_cols)}")

    # Display insights
    if insights:
        for i in insights:
            st.write(f"• {i}")
    else:
        st.success("No major issues detected.")

    # -------- EXTRA VIEWS --------
    if duplicate_count > 0:
        st.markdown("### 🔁 Duplicate Rows")
        st.dataframe(df[df.duplicated()])

    if constant_cols:
        st.markdown("### 📉 Constant Columns")
        st.write(constant_cols)

    # ------------------ REPORT ------------------
    def generate_report():
        return f"""
        <h1>📊 Data Report</h1>

        <h2>Basic Info</h2>
        <p>Rows: {df.shape[0]}<br>Columns: {df.shape[1]}</p>

        <h2>Missing Values</h2>
        {df.isnull().sum().to_frame().to_html()}

        <h2>Summary</h2>
        {df.describe().to_html() if not numeric_df.empty else "<p>No numeric data</p>"}

        <h2>Insights</h2>
        <ul>
        {''.join([f"<li>{i}</li>" for i in insights])}
        </ul>
        """

    st.markdown("### 📄 Report")

    if st.button("📥 Generate Report"):
        html_report = generate_report()
        b64 = base64.b64encode(html_report.encode()).decode()

        href = f'<a href="data:text/html;base64,{b64}" download="report.html">Download Report</a>'
        st.markdown(href, unsafe_allow_html=True)