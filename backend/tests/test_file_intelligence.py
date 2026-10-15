import pytest
from pathlib import Path
import pandas as pd
import pypdf
from pypdf import PdfWriter
from app.tools.pdf_tool import PDFDocumentTool
from app.tools.excel_tool import ExcelAnalysisTool
from app.core.config import settings

def create_sample_pdf(filepath: Path):
    writer = PdfWriter()
    page1 = writer.add_blank_page(width=300, height=300)
    # Write some basic PDF stream content
    with open(filepath, "wb") as f:
        writer.write(f)

@pytest.mark.asyncio
async def test_pdf_inspection_and_error_handling():
    tool = PDFDocumentTool()

    # 1. Nonexistent file
    res = await tool.execute({"file_path": "non_existent_file.pdf", "operation": "inspect"})
    assert res["is_success"] is False
    assert "File not found" in res["error"]

    # 2. Empty file
    empty_pdf = settings.WORKSPACE_DIR / "empty_test.pdf"
    empty_pdf.touch()
    res_empty = await tool.execute({"file_path": "empty_test.pdf", "operation": "inspect"})
    assert res_empty["is_success"] is False
    assert "empty" in res_empty["error"]

    # 3. Create real valid PDF fixture
    valid_pdf = settings.WORKSPACE_DIR / "sample_contract.pdf"
    create_sample_pdf(valid_pdf)
    res_valid = await tool.execute({"file_path": "sample_contract.pdf", "operation": "inspect"})
    assert res_valid["is_success"] is True
    assert res_valid["total_pages"] == 1

@pytest.mark.asyncio
async def test_excel_analysis_and_duckdb_sql():
    tool = ExcelAnalysisTool()

    # 1. Nonexistent file
    res = await tool.execute({"file_path": "missing.xlsx", "operation": "inspect"})
    assert res["is_success"] is False

    # 2. Real CSV fixture
    csv_file = settings.WORKSPACE_DIR / "test_records.csv"
    df = pd.DataFrame({
        "Department": ["Sales", "Engineering", "Marketing", "Sales", "Engineering"],
        "Budget": [50000, 120000, 45000, 52000, 130000],
        "Headcount": [5, 12, 4, 6, 14]
    })
    df.to_csv(csv_file, index=False)

    # 3. SQL aggregation query
    sql_res = await tool.execute({
        "file_path": "test_records.csv",
        "operation": "query_sql",
        "sql_query": "SELECT Department, AVG(Budget) as AvgBudget, SUM(Headcount) as TotalHC FROM df GROUP BY Department ORDER BY AvgBudget DESC"
    })
    assert sql_res["is_success"] is True
    assert sql_res["result_rows"] == 3
    assert sql_res["data"][0]["Department"] == "Engineering"

    # 4. Summary Export to Excel
    export_res = await tool.execute({
        "file_path": "test_records.csv",
        "operation": "export_summary"
    })
    assert export_res["is_success"] is True
    assert Path(export_res["exported_path"]).exists()
