import pytest
import time
from pathlib import Path
from app.tools.windows_tool import WindowsAutomationTool
from app.core.config import settings

@pytest.mark.asyncio
async def test_windows_system_metrics_and_open_windows():
    tool = WindowsAutomationTool()
    
    # 1. System info
    info = await tool.execute({"action": "get_system_info"})
    assert info["is_success"] is True
    assert "cpu_count" in info
    assert info["ram_total_gb"] > 0

    # 2. List open windows
    win_list = await tool.execute({"action": "list_open_windows"})
    assert win_list["is_success"] is True
    assert win_list["count"] >= 0

@pytest.mark.asyncio
async def test_windows_desktop_screenshot():
    tool = WindowsAutomationTool()
    res = await tool.execute({"action": "capture_screenshot"})
    assert res["is_success"] is True
    assert "screenshot_path" in res
    assert Path(res["screenshot_path"]).exists()

@pytest.mark.asyncio
async def test_windows_notepad_lifecycle_and_typing():
    tool = WindowsAutomationTool()
    
    # 1. Launch approved Notepad app
    launch_res = await tool.execute({
        "action": "launch_app",
        "app_name": "notepad.exe"
    })
    assert launch_res["is_success"] is True
    assert launch_res["status"] == "launched"

    time.sleep(1.0) # Wait for window to appear

    # 2. Inspect controls of Notepad
    inspect_res = await tool.execute({
        "action": "inspect_window_controls",
        "window_title": "Notepad"
    })
    # If UIAutomation window is found
    if inspect_res["is_success"]:
        assert "controls_count" in inspect_res

    # 3. Type text into Notepad
    type_res = await tool.execute({
        "action": "type_text",
        "window_title": "Notepad",
        "text_to_type": "NexusFlow AI Desktop Automation Verified"
    })
    assert type_res["is_success"] is True
    assert type_res["characters_entered"] > 0

    # 4. Close Notepad
    close_res = await tool.execute({
        "action": "close_app",
        "window_title": "Notepad"
    })
    assert close_res["is_success"] is True or "not found" in close_res.get("error", "")

@pytest.mark.asyncio
async def test_windows_security_whitelist_blocks_unauthorized_apps():
    tool = WindowsAutomationTool()
    
    # 1. Arbitrary unauthorized app
    blocked = await tool.execute({
        "action": "launch_app",
        "app_name": "powershell_hidden_miner.exe"
    })
    assert blocked["is_success"] is False
    assert "not in the approved whitelist" in blocked["error"]

    # 2. Command shell cmd.exe must also be blocked to prevent arbitrary shell injection
    cmd_blocked = await tool.execute({
        "action": "launch_app",
        "app_name": "cmd.exe"
    })
    assert cmd_blocked["is_success"] is False
    assert "not in the approved whitelist" in cmd_blocked["error"]
