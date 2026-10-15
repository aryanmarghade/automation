import pytest
from app.tools.browser_tool import BrowserAutomationTool
from app.tools.windows_tool import WindowsAutomationTool

@pytest.mark.asyncio
async def test_browser_search_and_extract():
    tool = BrowserAutomationTool()
    # Test verified research search
    search_res = await tool.execute({
        "action": "search_web",
        "query": "FastAPI python web framework"
    })
    assert search_res["results_count"] > 0
    assert "query" in search_res

@pytest.mark.asyncio
async def test_windows_automation_and_info():
    tool = WindowsAutomationTool()
    info = await tool.execute({"action": "get_system_info"})
    assert "os" in info
    assert "ram_total_gb" in info
    assert info["cpu_count"] > 0

    # Test permission barrier on unapproved app launch
    blocked = await tool.execute({"action": "launch_app", "app_name": "malicious_script.exe"})
    assert blocked["is_success"] is False
    assert "not in the approved whitelist" in blocked["error"]
