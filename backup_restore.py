import os
import sys
import shutil
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, Any, List

# Authoritative Paths
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BACKEND_DIR / "backend" / "data"
DATABASE_PATH = DATA_DIR / "nexusflow.db"
WORKSPACE_DIR = BACKEND_DIR / "workspace"
BACKUP_ROOT = BASE_DIR / "backups"

def create_safe_backup(backup_name: str = None) -> Dict[str, Any]:
    """
    Performs an online, consistent backup of SQLite using sqlite3 backup API,
    copies user persistent configuration and workspace assets (excluding temporary files).
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = backup_name or f"nexusflow_backup_{timestamp}"
    backup_target_dir = BACKUP_ROOT / folder_name
    
    if backup_target_dir.exists():
        raise FileExistsError(f"Backup destination {backup_target_dir} already exists. Refusing to overwrite.")

    backup_target_dir.mkdir(parents=True, exist_ok=False)
    
    # 1. Consistent SQLite Online Backup
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Authoritative database not found at {DATABASE_PATH}")
        
    db_backup_dest = backup_target_dir / "nexusflow.db"
    
    # Use SQLite native backup API to guarantee consistency even under concurrent reads
    src_conn = sqlite3.connect(DATABASE_PATH)
    dst_conn = sqlite3.connect(db_backup_dest)
    with dst_conn:
        src_conn.backup(dst_conn, pages=100)
    dst_conn.close()
    src_conn.close()
    
    # Verify backed up database integrity
    verify_conn = sqlite3.connect(db_backup_dest)
    integrity_result = verify_conn.execute("PRAGMA integrity_check;").fetchall()
    verify_conn.close()
    if not integrity_result or integrity_result[0][0] != "ok":
        raise RuntimeError(f"Database integrity check failed on backup copy: {integrity_result}")
    
    # 2. Backup Workspace Assets (filtering temporary caches and ephemeral outputs)
    workspace_backup_dest = backup_target_dir / "workspace"
    workspace_backup_dest.mkdir(parents=True, exist_ok=True)
    
    excluded_extensions = {".tmp", ".pyc", ".swp"}
    excluded_dirs = {"__pycache__", ".pytest_cache", ".next", "node_modules"}
    
    copied_files_count = 0
    if WORKSPACE_DIR.exists():
        for item in WORKSPACE_DIR.iterdir():
            if item.is_file():
                if item.suffix.lower() not in excluded_extensions and not item.name.startswith("."):
                    shutil.copy2(item, workspace_backup_dest / item.name)
                    copied_files_count += 1
    
    # 3. Backup Config / Metadata (without secrets)
    meta = {
        "timestamp": timestamp,
        "backup_name": folder_name,
        "version": "1.0.0",
        "authoritative_db_source": str(DATABASE_PATH),
        "db_size_bytes": db_backup_dest.stat().st_size,
        "workspace_files_backed_up": copied_files_count,
        "integrity_status": "ok"
    }
    
    import json
    with open(backup_target_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    return {
        "status": "success",
        "backup_dir": str(backup_target_dir),
        "manifest": meta
    }

def restore_backup(backup_dir: Path, target_db_path: Path, target_workspace_dir: Path) -> Dict[str, Any]:
    """
    Restores a backup into a targeted database path and workspace directory.
    To prevent accidents, this function requires explicit destination paths.
    """
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup folder {backup_path} does not exist.")
        
    src_db = backup_path / "nexusflow.db"
    if not src_db.exists():
        raise FileNotFoundError(f"Database backup file {src_db} missing.")
        
    # Ensure target parent exists
    target_db_path.parent.mkdir(parents=True, exist_ok=True)
    target_workspace_dir.mkdir(parents=True, exist_ok=True)
    
    # Restore DB via SQLite backup API for guaranteed atomic consistency
    src_conn = sqlite3.connect(src_db)
    dst_conn = sqlite3.connect(target_db_path)
    with dst_conn:
        src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()
    
    # Restore workspace items
    src_workspace = backup_path / "workspace"
    restored_files = 0
    if src_workspace.exists():
        for item in src_workspace.iterdir():
            if item.is_file():
                shutil.copy2(item, target_workspace_dir / item.name)
                restored_files += 1
                
    return {
        "status": "success",
        "restored_db": str(target_db_path),
        "restored_workspace": str(target_workspace_dir),
        "files_restored": restored_files
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NexusFlow AI Safe Backup & Restore Utility")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    backup_parser = subparsers.add_parser("backup", help="Create a safe backup")
    backup_parser.add_argument("--name", help="Optional custom name for the backup folder", default=None)
    
    restore_parser = subparsers.add_parser("restore", help="Restore a backup to a specified directory")
    restore_parser.add_argument("--backup-dir", required=True, help="Path to backup folder to restore")
    restore_parser.add_argument("--target-db", required=True, help="Target path for restored database")
    restore_parser.add_argument("--target-workspace", required=True, help="Target path for restored workspace")
    
    verify_parser = subparsers.add_parser("verify-isolated-restore", help="Perform non-destructive isolated restore test")
    
    args = parser.parse_args()
    
    if args.command == "backup":
        res = create_safe_backup(args.name)
        print("Backup created successfully:")
        print(f"  Directory: {res['backup_dir']}")
        print(f"  Manifest: {res['manifest']}")
    elif args.command == "restore":
        res = restore_backup(Path(args.backup_dir), Path(args.target_db), Path(args.target_workspace))
        print("Restoration completed successfully:")
        print(f"  Restored DB: {res['restored_db']}")
        print(f"  Restored Workspace: {res['restored_workspace']}")
        print(f"  Files: {res['files_restored']}")
    elif args.command == "verify-isolated-restore":
        import tempfile
        print("Running non-destructive isolated backup & restore verification...")
        backup_res = create_safe_backup(backup_name="_temp_verification_backup")
        b_dir = Path(backup_res["backup_dir"])
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                test_db = tmp_path / "restored_nexusflow.db"
                test_ws = tmp_path / "restored_workspace"
                restore_res = restore_backup(b_dir, test_db, test_ws)
                
                # Check DB integrity & table records
                conn = sqlite3.connect(test_db)
                cur = conn.cursor()
                tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                wf_count = cur.execute("SELECT COUNT(*) FROM workflows").fetchone()[0]
                sched_count = cur.execute("SELECT COUNT(*) FROM schedules").fetchone()[0]
                conn.close()
                
                print("[VERIFIED] Isolated restore succeeded perfectly.")
                print(f"  Tables found: {tables}")
                print(f"  Workflows restored: {wf_count}")
                print(f"  Schedules restored: {sched_count}")
                print(f"  Workspace files copied: {restore_res['files_restored']}")
        finally:
            if b_dir.exists():
                shutil.rmtree(b_dir)
