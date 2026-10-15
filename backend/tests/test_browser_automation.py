import pytest
from pathlib import Path
from app.tools.browser_tool import BrowserAutomationTool
from app.core.config import settings

@pytest.mark.asyncio
async def test_playwright_local_html_navigation():
    # 1. Create a local test HTML page in workspace
    test_html = settings.WORKSPACE_DIR / "test_form.html"
    test_html.write_text("""
    <!DOCTYPE html>
    <html>
    <head><title>NexusFlow Test Page</title></head>
    <body>
        <h1>Welcome to NexusFlow Local Automation</h1>
        <p>This is a deterministic local test page for Playwright verification.</p>
        <form id="sample-form">
            <input type="text" id="username" name="user" placeholder="Enter username" />
            <button type="button" id="submit-btn" onclick="document.getElementById('status').innerText = 'Submitted Successfully';">Submit</button>
        </form>
        <div id="status">Ready</div>
    </body>
    </html>
    """, encoding="utf-8")

    tool = BrowserAutomationTool()
    posix_path = test_html.as_posix()
    file_url = f"file:///{posix_path}"

    # 2. Test navigate and extract
    nav_res = await tool.execute({
        "action": "navigate_and_extract",
        "url": file_url
    })
    assert nav_res["is_success"] is True
    assert "NexusFlow Test Page" in nav_res["title"]
    assert "Welcome to NexusFlow" in nav_res["text_preview"]

    # 3. Test click and fill with screenshot capture
    fill_res = await tool.execute({
        "action": "click_and_fill",
        "url": file_url,
        "selector": "input#username",
        "fill_text": "AutomationAgentAdmin"
    })
    assert fill_res["is_success"] is True
    assert "screenshot_path" in fill_res
    assert Path(fill_res["screenshot_path"]).exists()

@pytest.mark.asyncio
async def test_web_research_and_citations():
    tool = BrowserAutomationTool()
    res = await tool.execute({
        "action": "research_topic",
        "query": "Artificial Intelligence agent workflows"
    })
    assert res["is_success"] is True
    assert res["facts_distinguished_from_inferences"] is True
    assert len(res["sources_consulted"]) > 0

@pytest.mark.asyncio
async def test_browser_url_validation_and_ssrf():
    tool = BrowserAutomationTool()
    
    # 1. Invalid protocol
    res = await tool.execute({
        "action": "navigate_and_extract",
        "url": "ftp://malicious.example.com/payload"
    })
    assert res["is_success"] is False
    assert "Invalid URL protocol" in res["error"]

    # 2. Cloud metadata SSRF blocking
    ssrf_res = await tool.execute({
        "action": "navigate_and_extract",
        "url": "http://169.254.169.254/latest/meta-data/"
    })
    assert ssrf_res["is_success"] is False
    assert "restricted metadata service" in ssrf_res["error"]

    # 3. Arbitrary file scheme traversal outside workspace
    file_escape_res = await tool.execute({
        "action": "navigate_and_extract",
        "url": "file:///C:/Windows/System32/drivers/etc/hosts"
    })
    assert file_escape_res["is_success"] is False
    assert "outside workspace sandbox" in file_escape_res["error"]
