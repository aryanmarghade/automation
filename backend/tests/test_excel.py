import pytest
from pathlib import Path
import pandas as pd
from app.tools.excel_tool import ExcelAnalysisTool
from app.core.config import settings

@pytest.mark.asyncio
async def test_excel_analysis_and_anomaly_detection():
    # Create a test CSV in workspace
    test_csv = settings.WORKSPACE_DIR / "test_sales.csv"
    df = pd.DataFrame({
        "Category": ["Electronics", "Clothing", "Home", "Electronics", "Clothing", "Toys"],
        "Revenue": [1200, 450, 300, 15000, 500, 150], # 15000 is an outlier
        "Units": [10, 15, 5, 12, 18, 4]
    })
    df.to_csv(test_csv, index=False)

    tool = ExcelAnalysisTool()

    # 1. Test inspect
    inspect_res = await tool.execute({"file_path": "test_sales.csv", "operation": "inspect"})
    assert inspect_res["rows"] == 6
    assert "Category" in inspect_res["columns"]

    # 2. Test summary stats
    stats_res = await tool.execute({"file_path": "test_sales.csv", "operation": "summary_stats"})
    assert stats_res["total_rows"] == 6

    # 3. Test SQL query with DuckDB
    sql_res = await tool.execute({
        "file_path": "test_sales.csv",
        "operation": "query_sql",
        "sql_query": "SELECT Category, SUM(Revenue) as TotalRev FROM df GROUP BY Category ORDER BY TotalRev DESC"
    })
    assert sql_res["result_rows"] > 0
    assert sql_res["data"][0]["Category"] == "Electronics"

    # 4. Test Chart Generation
    chart_res = await tool.execute({
        "file_path": "test_sales.csv",
        "operation": "generate_chart",
        "chart_type": "bar",
        "x_col": "Category",
        "y_col": "Revenue",
        "chart_title": "Category Revenue Analysis"
    })
    assert chart_res["is_success"] is True
    assert Path(chart_res["chart_path"]).exists()
