from pathlib import Path

import pandas as pd

from src.graph.state import GraphState
from data_frame import global_df


def profiler_node(state: GraphState):
    """
    Generates a lightweight profiling report without external profiling libraries.
    """

    print("🔍 Generating dataset profile...")

    try:
        df = global_df

        if df is None or df.empty:
            return {
                "execution_output": "Dataset is empty.",
                "final_report": "No data available for profiling.",
            }

        numeric_df = df.select_dtypes(include="number")

        # Basic Information
        rows, cols = df.shape
        memory_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
        duplicates = int(df.duplicated().sum())

        # Missing Values
        missing = df.isnull().sum()
        missing_percent = ((missing / rows) * 100).round(2)

        # Column Summary
        column_summary = pd.DataFrame({
            "Data Type": df.dtypes.astype(str),
            "Missing": missing,
            "Missing %": missing_percent,
            "Unique Values": df.nunique(),
        })

        # Numeric Statistics
        numeric_summary = (
            df.describe(include="number")
            if not numeric_df.empty
            else pd.DataFrame()
        )

        # Categorical Statistics
        categorical_summary = (
            df.describe(include=["object", "category"])
            if len(df.select_dtypes(include=["object", "category"]).columns) > 0
            else pd.DataFrame()
        )

        # Correlation
        correlation = (
            numeric_df.corr().round(2)
            if numeric_df.shape[1] > 1
            else pd.DataFrame()
        )

        # Save HTML Report
        html = f"""
        <html>
        <head>
            <title>DataScribe Dataset Profile</title>
            <style>
                body {{
                    font-family: Arial;
                    margin: 40px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 30px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                h2 {{
                    margin-top: 40px;
                }}
            </style>
        </head>
        <body>

        <h1>DataScribe Dataset Profile</h1>

        <h2>Dataset Overview</h2>

        <ul>
            <li><b>Rows:</b> {rows}</li>
            <li><b>Columns:</b> {cols}</li>
            <li><b>Memory Usage:</b> {memory_mb:.2f} MB</li>
            <li><b>Duplicate Rows:</b> {duplicates}</li>
        </ul>

        <h2>Column Summary</h2>

        {column_summary.to_html()}

        <h2>Numeric Statistics</h2>

        {numeric_summary.to_html() if not numeric_summary.empty else "<p>No numeric columns.</p>"}

        <h2>Categorical Statistics</h2>

        {categorical_summary.to_html() if not categorical_summary.empty else "<p>No categorical columns.</p>"}

        <h2>Correlation Matrix</h2>

        {correlation.to_html() if not correlation.empty else "<p>Not enough numeric columns.</p>"}

        </body>
        </html>
        """

        report_path = Path("data_profile_report.html")
        report_path.write_text(html, encoding="utf-8")

        output = "Dataset profiling completed successfully."

        report = f"""
# Dataset Profile Summary

- **Rows:** {rows}
- **Columns:** {cols}
- **Memory Usage:** {memory_mb:.2f} MB
- **Duplicate Rows:** {duplicates}
- **Columns with Missing Values:** {(missing > 0).sum()}

A detailed HTML report has been generated:

`data_profile_report.html`

The report contains:
- Dataset overview
- Column information
- Missing value analysis
- Numeric statistics
- Categorical statistics
- Correlation matrix
"""

        return {
            "execution_output": output,
            "final_report": report,
        }

    except Exception as e:
        return {
            "execution_output": str(e),
            "final_report": f"Profiling failed:\n\n{e}",
        }