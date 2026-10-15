import os
import sys
import socket
import urllib.request
import urllib.error
import json
import sqlite3
import shutil
import platform
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BACKEND_DIR / "backend" / "data"
DATABASE_PATH = DATA_DIR / "nexusflow.db"
WORKSPACE_DIR = BACKEND_DIR / "workspace"

def check_port(port: int, host: str = "127.0.0.1") -> bool:
    """Returns True if the port is currently accepting connections (i.e. service is running)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def check_backend_api():
    url = "http://127.0.0.1:8000/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NexusFlowHealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return True, f"Backend API is healthy (version: {data.get('version', 'unknown')}, app: {data.get('app', 'NexusFlow AI')})"
            return False, f"Backend returned HTTP {resp.status}"
    except Exception as e:
        return False, f"Backend API is not responding on {url}: {e}"

def check_frontend():
    url = "http://localhost:3000"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NexusFlowHealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                return True, f"Frontend web server is online on {url} (HTTP 200)"
            return False, f"Frontend returned HTTP {resp.status}"
    except Exception as e:
        return False, f"Frontend is not responding on {url}: {e}"

def check_database():
    if not DATABASE_PATH.exists():
        return False, f"Authoritative SQLite database file not found at {DATABASE_PATH}"
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        integrity = cur.execute("PRAGMA integrity_check;").fetchone()[0]
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        if integrity == "ok":
            return True, f"SQLite database integrity verified ({len(tables)} tables present: {', '.join(tables)})"
        return False, f"SQLite integrity check reported: {integrity}"
    except Exception as e:
        return False, f"Database connectivity error: {e}"

def check_workspace():
    if not WORKSPACE_DIR.exists():
        try:
            WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"Cannot create workspace directory: {e}"
    
    test_file = WORKSPACE_DIR / ".healthcheck_write_test.tmp"
    try:
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("write_ok")
        test_file.unlink()
        return True, f"Workspace is writable at {WORKSPACE_DIR}"
    except Exception as e:
        return False, f"Workspace write permission failure: {e}"

def check_playwright():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Check if chromium executable exists / can launch headless
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content("<html><body><h1>Health Check</h1></body></html>")
            title = page.locator("h1").text_content()
            browser.close()
            if title == "Health Check":
                return True, "Playwright Chromium headless browser engine is installed and operational"
            return False, "Playwright launched but rendered unexpected content"
    except Exception as e:
        return False, f"Playwright browser automation dependency check failed: {e}"

def check_ollama():
    url = "http://127.0.0.1:11434/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NexusFlowHealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                return True, f"Ollama local LLM server is active with models: {', '.join(models) if models else 'None'}"
            return False, f"Ollama returned HTTP {resp.status}"
    except Exception:
        return False, "Ollama local LLM server is offline (Optional: Built-in heuristic fallback planner will be used)"

def check_windows_automation():
    if platform.system() != "Windows":
        return False, f"Windows desktop automation is unavailable on non-Windows OS ({platform.system()})"
    try:
        from pywinauto import Desktop
        windows = Desktop(backend="uia").windows()
        window_count = len(windows)
        return True, f"Windows UIAutomation / pywinauto is initialized ({window_count} window targets accessible)"
    except Exception as e:
        return False, f"Windows UIAutomation access error: {e}"

def run_all_checks():
    print("=" * 70)
    print("           NEXUSFLOW AI — PRE-DEMO HEALTH CHECK")
    print("=" * 70)
    print(f"Timestamp: {platform.node()} | OS: {platform.platform()}")
    print("-" * 70)
    
    required_checks = [
        ("Database Connectivity", check_database),
        ("Workspace Storage & Write Permissions", check_workspace),
        ("Browser Automation (Playwright)", check_playwright),
    ]
    
    # Check if services are running or just static checks
    backend_running = check_port(8000)
    frontend_running = check_port(3000)
    
    if backend_running:
        required_checks.insert(0, ("Backend API Readiness", check_backend_api))
    else:
        print("[!] Backend service is NOT currently running on port 8000 (Start with start_backend.bat or start_nexusflow.bat)")

    if frontend_running:
        required_checks.append(("Frontend UI Server Readiness", check_frontend))
    else:
        print("[!] Frontend service is NOT currently running on port 3000 (Start with start_frontend.bat or start_nexusflow.bat)")
    
    print()
    print("--- [ REQUIRED CORE DEPENDENCIES ] ---")
    all_req_passed = True
    for name, check_fn in required_checks:
        passed, msg = check_fn()
        status_icon = "[OK]" if passed else "[FAILED]"
        print(f"{status_icon:<8} {name}: {msg}")
        if not passed:
            all_req_passed = False
            
    print()
    print("--- [ OPTIONAL & ENVIRONMENT CAPABILITIES ] ---")
    
    # Ollama (Optional)
    ollama_ok, ollama_msg = check_ollama()
    if ollama_ok:
        print(f"[OK]     Ollama LLM Engine: {ollama_msg}")
    else:
        print(f"[INFO]   Ollama LLM Engine: {ollama_msg}")
        
    # Windows Desktop Automation (Optional / Environment dependent)
    win_ok, win_msg = check_windows_automation()
    if win_ok:
        print(f"[OK]     Windows Automation: {win_msg}")
    else:
        print(f"[WARN]   Windows Automation: {win_msg}")
        
    print()
    print("=" * 70)
    if all_req_passed:
        print("SUMMARY: ALL CRITICAL PRE-DEMO CHECKS PASSED. Ready for demonstration.")
    else:
        print("SUMMARY: CRITICAL CHECKS FAILED. Resolve the issues above before proceeding.")
    print("=" * 70)
    return all_req_passed

if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
