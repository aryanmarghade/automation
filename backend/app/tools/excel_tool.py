import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import openpyxl
import duckdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time
from app.tools.registry import BaseTool, ToolDefinition, ToolCategory, ToolParameter, RiskLevel, registry
from app.core.config import settings

class ExcelAnalysisTool(BaseTool):
    def __init__(self):
        super().__init__(ToolDefinition(
            id="excel_tabular_analyzer",
            name="Spreadsheet & Tabular Analyzer",
            description="Analyzes Excel (.xlsx, .xls) and CSV workbooks, detects anomalies/duplicates/metrics, executes SQL queries with DuckDB, and generates charts and new formatted summaries.",
            category=ToolCategory.TABULAR,
            risk_level=RiskLevel.LOW,
            parameters=[
                ToolParameter(name="file_path", type="string", description="Workspace-relative or absolute path to the .xlsx, .xls, or .csv file", required=True),
                ToolParameter(name="operation", type="string", description="Operation: 'inspect', 'summary_stats', 'query_sql', 'detect_anomalies', 'generate_chart', 'export_summary', 'compare_sheets'", required=True, options=["inspect", "summary_stats", "query_sql", "detect_anomalies", "generate_chart", "export_summary", "compare_sheets"]),
                ToolParameter(name="sql_query", type="string", description="SQL query to run when operation is 'query_sql' (Table name is 'df')", required=False, default=""),
                ToolParameter(name="chart_type", type="string", description="Chart type when generating chart: 'bar', 'line', 'pie', 'scatter'", required=False, default="bar", options=["bar", "line", "pie", "scatter"]),
                ToolParameter(name="x_col", type="string", description="Column for X axis in chart", required=False, default=""),
                ToolParameter(name="y_col", type="string", description="Column for Y axis in chart", required=False, default=""),
                ToolParameter(name="chart_title", type="string", description="Title for generated chart image", required=False, default="Data Chart")
            ]
        ))

    def _resolve_file(self, file_path_str: str) -> Path:
        p = Path(file_path_str)
        if not p.is_absolute():
            p = settings.WORKSPACE_DIR / file_path_str
        
        # Security sandbox check
        try:
            resolved = p.resolve()
            workspace_resolved = settings.WORKSPACE_DIR.resolve()
            if not str(resolved).startswith(str(workspace_resolved)):
                raise PermissionError(f"Access denied: File '{file_path_str}' is outside the authorized workspace sandbox.")
        except Exception as e:
            if isinstance(e, PermissionError):
                raise
            pass

        if not p.exists():
            raise FileNotFoundError(f"File not found: {p.name}")
        
        # File size check (max 100 MB)
        if p.stat().st_size > 100 * 1024 * 1024:
            raise ValueError(f"File '{p.name}' exceeds the maximum allowed size limit of 100 MB")
        if p.stat().st_size == 0:
            raise ValueError(f"File '{p.name}' is empty (0 bytes)")

        return p

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        file_path_str = params.get("file_path", "")
        op = params.get("operation", "inspect")
        
        try:
            target_path = self._resolve_file(file_path_str)
        except Exception as e:
            return {"error": str(e), "is_success": False}

        try:
            is_csv = target_path.suffix.lower() in [".csv", ".tsv"]
            if is_csv:
                df = pd.read_csv(target_path, sep=None, engine="python")
                sheet_names = ["Sheet1"]
            elif target_path.suffix.lower() in [".xlsx", ".xls"]:
                xl = pd.ExcelFile(target_path)
                sheet_names = xl.sheet_names
                df = pd.read_excel(target_path, sheet_name=sheet_names[0])
            else:
                return {"error": f"Unsupported tabular file format: {target_path.suffix}", "is_success": False}

            if op == "inspect":
                return {
                    "filename": target_path.name,
                    "sheet_names": sheet_names,
                    "active_sheet": sheet_names[0],
                    "rows": len(df),
                    "columns": list(df.columns),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "sample_records": df.head(5).fillna("").to_dict(orient="records"),
                    "is_success": True
                }

            elif op == "summary_stats":
                numeric_df = df.select_dtypes(include=["number"])
                desc = numeric_df.describe().to_dict() if not numeric_df.empty else {}
                null_counts = df.isnull().sum().to_dict()
                return {
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "null_counts": null_counts,
                    "numeric_statistics": desc,
                    "is_success": True
                }

            elif op == "detect_anomalies":
                duplicates_count = int(df.duplicated().sum())
                numeric_cols = df.select_dtypes(include=["number"]).columns
                
                outliers = {}
                for col in numeric_cols:
                    col_data = df[col].dropna()
                    if len(col_data) > 3 and col_data.std() > 0:
                        z_scores = (col_data - col_data.mean()) / col_data.std()
                        outlier_indices = col_data[z_scores.abs() > 3].to_dict()
                        if outlier_indices:
                            outliers[col] = outlier_indices

                return {
                    "duplicate_rows": duplicates_count,
                    "outliers_found": outliers,
                    "missing_values_by_column": df.isnull().sum().to_dict(),
                    "is_success": True
                }

            elif op == "query_sql":
                sql = params.get("sql_query", "").strip()
                if not sql:
                    return {"error": "sql_query parameter is required for query_sql operation", "is_success": False}
                con = duckdb.connect(database=":memory:")
                con.register("df", df)
                query_res = con.execute(sql).df()
                return {
                    "query": sql,
                    "result_rows": len(query_res),
                    "columns": list(query_res.columns),
                    "data": query_res.head(50).fillna("").to_dict(orient="records"),
                    "is_success": True
                }

            elif op == "generate_chart":
                chart_type = params.get("chart_type", "bar")
                x_col = params.get("x_col")
                y_col = params.get("y_col")
                title = params.get("chart_title", "Chart")

                if not x_col or not y_col:
                    return {"error": "x_col and y_col are required to render a chart", "is_success": False}
                
                if x_col not in df.columns or y_col not in df.columns:
                    return {"error": f"Columns {x_col} or {y_col} not found in dataset columns: {list(df.columns)}", "is_success": False}

                fig, ax = plt.subplots(figsize=(10, 6))
                plot_data = df.dropna(subset=[x_col, y_col]).head(20)

                if chart_type == "bar":
                    ax.bar(plot_data[x_col].astype(str), plot_data[y_col], color="#3b82f6")
                    plt.xticks(rotation=45, ha='right')
                elif chart_type == "line":
                    ax.plot(plot_data[x_col].astype(str), plot_data[y_col], marker='o', color="#10b981")
                    plt.xticks(rotation=45, ha='right')
                elif chart_type == "scatter":
                    ax.scatter(plot_data[x_col], plot_data[y_col], color="#8b5cf6")
                
                ax.set_title(title, fontsize=14, fontweight='bold')
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                plt.tight_layout()

                output_filename = f"chart_{int(time.time())}.png"
                output_path = settings.WORKSPACE_DIR / output_filename
                fig.savefig(output_path, dpi=150)
                plt.close(fig)

                return {
                    "chart_file": output_filename,
                    "chart_path": str(output_path),
                    "chart_type": chart_type,
                    "is_success": True
                }

            elif op == "export_summary":
                out_name = f"summary_{target_path.stem}_{int(time.time())}.xlsx"
                out_path = settings.WORKSPACE_DIR / out_name
                
                with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
                    df.head(100).to_excel(writer, sheet_name="DataSample", index=False)
                    desc = df.describe(include='all')
                    desc.to_excel(writer, sheet_name="StatisticalSummary")
                
                return {
                    "exported_file": out_name,
                    "exported_path": str(out_path),
                    "is_success": True
                }

            return {"error": f"Unsupported operation: {op}", "is_success": False}

        except Exception as e:
            return {"error": f"Spreadsheet analysis failed: {str(e)}", "is_success": False}
