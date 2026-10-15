from app.tools.registry import registry
from app.tools.core_tools import register_core_tools
from app.tools.excel_tool import ExcelAnalysisTool
from app.tools.pdf_tool import PDFDocumentTool
from app.tools.browser_tool import BrowserAutomationTool
from app.tools.windows_tool import WindowsAutomationTool

def init_all_tools():
    register_core_tools()
    registry.register(ExcelAnalysisTool())
    registry.register(PDFDocumentTool())
    registry.register(BrowserAutomationTool())
    registry.register(WindowsAutomationTool())

# Auto-initialize
init_all_tools()
