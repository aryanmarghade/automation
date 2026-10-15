# NexusFlow AI — Safe Backup & Disaster Recovery Guide

This document outlines the authoritative backup, restoration, and disaster recovery procedures for **NexusFlow AI** on Windows.

---

## 1. Authoritative Architecture & Data Paths

All runtime state in NexusFlow AI is isolated to persistent directories without external cloud database dependencies:

* **Primary SQLite Database:** `D:\projects\Automation\backend\backend\data\nexusflow.db`
* **Persistent Workspace Files & Artifacts:** `D:\projects\Automation\backend\workspace\`
* **Backups Archive Location:** `D:\projects\Automation\backups/`

---

## 2. Automated Safe Backup Procedure

NexusFlow AI includes a dedicated, non-destructive backup tool: `backup_restore.py`.

### Why standard file copy is unsafe for SQLite:
Blindly copying a live SQLite database during active writes can result in corrupted page locks or torn pages. The `backup_restore.py` utility utilizes **SQLite's Online Backup API** (`sqlite3.Connection.backup()`), which acquires clean shared read locks, streams pages safely, and verifies the resulting database with `PRAGMA integrity_check;`.

### Command to Create a Backup:
```powershell
python backup_restore.py backup --name release_m10_snapshot
```

### What is Included in a Backup:
1. **`nexusflow.db`**: All workflow definitions, execution history, agent tasks, cron schedules, tool configurations, and notification logs.
2. **`workspace/`**: All user-uploaded documents, generated charts, Excel reports, screenshots, and transformed datasets (excluding temporary caches).
3. **`manifest.json`**: Metadata containing timestamp, source database path, file counts, and integrity status.

> [!NOTE]
> Secrets, API keys, passwords, and user credentials are **never** bundled into the backup archive.

---

## 3. Isolated Restoration & Verification Procedure

To test or restore a backup without endangering the live environment, restore to an isolated test target.

### Command for Non-Destructive Isolated Verification:
```powershell
python backup_restore.py verify-isolated-restore
```
This command automatically:
1. Creates a consistent live snapshot.
2. Restores it into a sandboxed temporary directory (`%TEMP%`).
3. Verifies schema tables (`workflows`, `schedules`, `executions`, etc.).
4. Validates record counts against the source.
5. Cleans up temporary artifacts upon completion.

### Manual Targeted Restoration:
```powershell
python backup_restore.py restore --backup-dir "D:\projects\Automation\backups\release_m10_snapshot" --target-db "D:\projects\Automation\backend\backend\data\nexusflow.db" --target-workspace "D:\projects\Automation\backend\workspace"
```

---

## 4. Disaster Recovery Checklist

In the event of hardware replacement or accidental data loss:
1. Ensure Python 3.11+ and Node.js v20+ are installed.
2. Restore the latest backup snapshot directory into `D:\projects\Automation\backups\`.
3. Run `python backup_restore.py restore` pointing to the target database and workspace locations.
4. Execute `python health_check.py` to confirm all 7 schema tables and storage permissions are validated.
5. Start the platform with `start_nexusflow.bat`.
