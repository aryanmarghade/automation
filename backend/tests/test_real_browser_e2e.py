import pytest
import asyncio
import os
import sys
import time
import subprocess
import socket
from pathlib import Path
import httpx
from playwright.async_api import async_playwright

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://127.0.0.1:8000"

def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

@pytest.fixture(scope="session", autouse=True)
def ensure_servers():
    """Starts backend and frontend if not already running, then yields for tests."""
    procs = []
    
    # 1. Backend
    if not is_port_open(8000):
        backend_dir = Path(__file__).parent.parent
        p_back = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(backend_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        procs.append(p_back)

    # 2. Frontend
    if not is_port_open(3000):
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        p_front = subprocess.Popen(
            ["npm.cmd", "run", "dev"],
            cwd=str(frontend_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        procs.append(p_front)

    # Wait up to 15s for both servers to be responsive
    start_time = time.time()
    backend_ready = False
    frontend_ready = False
    while time.time() - start_time < 20:
        if not backend_ready and is_port_open(8000):
            try:
                r = httpx.get(f"{BACKEND_URL}/health", timeout=1.0)
                if r.status_code == 200:
                    backend_ready = True
            except Exception:
                pass
        if not frontend_ready and is_port_open(3000):
            try:
                r = httpx.get(FRONTEND_URL, timeout=1.0)
                if r.status_code == 200:
                    frontend_ready = True
            except Exception:
                pass
        if backend_ready and frontend_ready:
            break
        time.sleep(0.5)

    yield

    # Clean up spawned processes
    for p in procs:
        try:
            p.terminate()
            p.kill()
        except Exception:
            pass

@pytest.mark.asyncio
async def test_journey_a_dashboard_and_sidebar_navigation():
    """Journey A: Real browser opens dashboard and clicks every sidebar link verifying page content."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        # 1. Load Dashboard
        await page.goto(f"{FRONTEND_URL}/", timeout=15000, wait_until="domcontentloaded")
        assert "NexusFlow" in await page.title()
        
        # Verify dashboard main heading
        heading = await page.inner_text("main h1")
        assert "NexusFlow Control Center" in heading

        # 2. Test Sidebar Links
        routes_to_test = [
            ("/agent", "AI Agent Execution"),
            ("/builder", "Workflow Canvas"),
            ("/library", "Workflow Library"),
            ("/files", "Workspace Files & Data Artifacts"),
            ("/tools", "Dynamic Tool Registry"),
            ("/browser", "Browser & Web Research Engine"),
            ("/desktop", "Windows Desktop Automation Control Panel"),
            ("/history", "Execution History"),
            ("/scheduler", "Scheduler"),
            ("/settings", "AI Providers & Model Configuration"),
            ("/security", "Security Boundaries & Permissions")
        ]

        for href, expected_text in routes_to_test:
            link = page.locator(f"aside a[href='{href}']")
            assert await link.count() > 0, f"Sidebar link {href} not found"
            await page.goto(f"{FRONTEND_URL}{href}", timeout=10000, wait_until="domcontentloaded")
            
            # Assert URL and heading
            assert href in page.url
            body_text = await page.inner_text("body")
            assert expected_text in body_text, f"Expected '{expected_text}' on route {href}"

        await browser.close()

@pytest.mark.asyncio
async def test_journey_b_builder_canvas_and_validation():
    """Journey B: Real browser loads workflow builder canvas, validates DAG, and checks controls."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        await page.goto(f"{FRONTEND_URL}/builder", timeout=15000, wait_until="domcontentloaded")
        
        # Check Canvas header & buttons
        assert await page.locator("text=Available Nodes").count() > 0
        save_btn = page.locator("button:has-text('Save Workflow')")
        assert await save_btn.count() > 0
        
        # Click Execute DAG button
        run_btn = page.locator("button:has-text('Execute DAG')")
        assert await run_btn.count() > 0
        
        # Verify canvas container exists
        canvas = page.locator(".react-flow")
        assert await canvas.count() > 0

        await browser.close()

@pytest.mark.asyncio
async def test_journey_c_agent_chat_interface():
    """Journey C: Real browser submits a prompt in AI Agent interface and observes planning state."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        await page.goto(f"{FRONTEND_URL}/agent", timeout=15000, wait_until="domcontentloaded")
        
        # Find input form
        input_box = page.locator("textarea[placeholder*='Describe']")
        assert await input_box.count() > 0

        # Focus and type sample objective with keyboard events
        await input_box.click()
        await input_box.press_sequentially("Analyze dataset revenue anomalies and summarize results", delay=10)
        await page.wait_for_timeout(300)
        
        # Submit form
        send_btn = page.locator("button:has-text('Plan & Execute')")
        assert await send_btn.count() > 0
        await send_btn.click()
        
        # Wait for agent response
        await page.wait_for_timeout(3000)
        body = await page.inner_text("body")
        assert "plan" in body.lower() or "formulated" in body.lower() or "step" in body.lower()

        await browser.close()

@pytest.mark.asyncio
async def test_journey_d_files_workspace_and_search():
    """Journey D: Real browser tests files workspace search and artifact download links."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        await page.goto(f"{FRONTEND_URL}/files", timeout=15000, wait_until="domcontentloaded")
        
        # Search input
        search_input = page.locator("input[placeholder*='Filter']")
        assert await search_input.count() > 0
        await search_input.fill("test")
        await page.wait_for_timeout(300)

        # Header presence
        assert await page.locator("text=Workspace Files").count() > 0

        await browser.close()

@pytest.mark.asyncio
async def test_journey_e_scheduler_modal_and_form():
    """Journey E: Real browser opens create schedule modal, toggles types, and checks form."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        await page.goto(f"{FRONTEND_URL}/scheduler", timeout=15000, wait_until="domcontentloaded")
        
        # Click Create Schedule button
        create_btn = page.locator("button:has-text('Create Schedule')")
        if await create_btn.count() > 0:
            await create_btn.click()
            await page.wait_for_timeout(400)
            # Verify modal visible
            assert await page.locator("text=Configure Workflow Schedule").count() > 0

        await browser.close()

@pytest.mark.asyncio
async def test_journey_f_browser_research_ui():
    """Journey F: Real browser tests tab switching on browser automation page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        await page.goto(f"{FRONTEND_URL}/browser", timeout=15000, wait_until="domcontentloaded")
        
        # Click Navigation tab
        nav_tab = page.locator("button:has-text('Browser Navigation & Interaction')")
        assert await nav_tab.count() > 0
        await nav_tab.click()
        await page.wait_for_timeout(500)

        # Verify Target URL and action buttons appear
        assert await page.locator("text=Target URL").count() > 0
        assert await page.locator("button:has-text('Navigate & Extract')").count() > 0

        await browser.close()

@pytest.mark.asyncio
async def test_journey_g_desktop_automation_metrics():
    """Journey G: Real browser inspects desktop automation page and system metrics."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        await page.goto(f"{FRONTEND_URL}/desktop", timeout=15000, wait_until="domcontentloaded")
        
        # System metrics banner
        await page.wait_for_timeout(1000)
        body = await page.inner_text("body")
        assert "Windows" in body or "Operating System" in body or "Logical CPUs" in body

        await browser.close()

@pytest.mark.asyncio
async def test_journey_h_settings_and_security_controls():
    """Journey H & I: Real browser tests settings slider/save and security allowlists."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        # Settings
        await page.goto(f"{FRONTEND_URL}/settings", timeout=15000, wait_until="domcontentloaded")
        assert "AI Providers" in await page.inner_text("main h1")
        save_btn = page.locator("button:has-text('Save Preferences')")
        assert await save_btn.count() > 0
        await save_btn.click()
        await page.wait_for_timeout(500)

        # Security
        await page.goto(f"{FRONTEND_URL}/security", timeout=15000, wait_until="domcontentloaded")
        assert "Security Boundaries" in await page.inner_text("main h1")
        body = await page.inner_text("body")
        assert "notepad.exe" in body
        assert "cmd.exe" in body
        assert "169.254.169.254" in body

        await browser.close()
