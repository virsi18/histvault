<div align="center">

# HistVault: Automated Browser History Preservation Vault
### Permanent Local History Archive with Deletion Protection, Multi-Browser Auto-Sync & Modern Web Dashboard

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero_Mandatory_(Stdlib)-brightgreen.svg)](#features)
[![Browsers](https://img.shields.io/badge/Browsers-Chrome_•_Edge_•_Brave_•_Firefox_•_Opera_•_Vivaldi-informational.svg)](#multi-browser-support)
[![Build Status](https://img.shields.io/badge/Tests-9%2F9_Passed-brightgreen.svg)](#running-tests)

```
  _    _ _     _  __      __          _ _   
 | |  | (_)   | | \ \    / /         | | |  
 | |__| |_ ___| |_ \ \  / /_ _ _   _| | |_ 
 |  __  | / __| __| \ \/ / _` | | | | | __|
 | |  | | \__ \ |_   \  / (_| | |_| | | |_ 
 |_|  |_|_|___/\__|   \/ \__,_|\__,_|_|\__|
 >> AUTOMATED BROWSER HISTORY PRESERVATION VAULT <<
 >> PERMANENT ARCHIVE EVEN WHEN BROWSER HISTORY IS DELETED <<
```

**Never lose your browsing history again — even after running "Clear Browsing Data" or closing private sessions.**

</div>

---

## 🌟 Why HistVault?

Mainstream web browsers periodically purge or allow users to clear browsing history. While helpful for local privacy on shared machines, it introduces catastrophic data loss when attempting to retrace research, critical work articles, technical documentation, or forgotten bookmarks.

**HistVault** solves this by establishing a **local, self-hosted, tamper-proof history vault**. It monitors your browser history databases in real time, copies lock-free snapshots to an independent SQLite vault, and categorizes every visit.

> **💡 The Deletion Guarantee:**  
> When you delete your browsing history inside Chrome, Edge, or Firefox, **HistVault retains 100% of the data** in your local vault and clearly tags the entry as `[🔴 PRESERVED FROM DELETION]`.

---

## 🚀 Key Features

* **Anti-Deletion Preservation:** Any record purged from the browser is preserved forever in the local vault with deletion audit timestamps.
* **Lock-Free Shadow Extraction:** Bypasses SQLite database lock issues while browsers are running via atomic shadow snapshots.
* **Cross-Browser Auto-Discovery:** Works seamlessly across:
  * Google Chrome
  * Microsoft Edge
  * Brave Browser
  * Mozilla Firefox
  * Opera & Opera GX
  * Vivaldi
* **Zero Mandatory Dependencies:** Runs out of the box using pure Python standard library (`sqlite3`, `http.server`, `urllib`, `threading`, `csv`, `json`).
* **Full-Text Search (FTS5):** Instant sub-millisecond search across page titles, URLs, domains, and custom notes.
* **Built-in Modern Web Dashboard:** A responsive dark-mode glassmorphic single-page interface served on `http://127.0.0.1:8765`.
* **Automatic Domain Categorization:** Auto-tags URLs into *Development & Tech, Search & Reference, Social Media, Media & Streaming, Shopping & Finance, News, etc.*
* **Multi-Format Export Engine:** Export your entire history or just deleted entries to **JSON**, **CSV (Excel)**, **Markdown (Obsidian/Notion)**, or **Standalone Searchable HTML**.
* **Background Watcher Daemon:** Continuously polls and archives history changes without consuming CPU cycles.

---

## 🔬 How It Works

```mermaid
flowchart TD
    subgraph Browsers ["Host Web Browsers (Running or Closed)"]
        Chrome["Google Chrome (History SQLite)"]
        Edge["Microsoft Edge (History SQLite)"]
        Firefox["Mozilla Firefox (places.sqlite)"]
        Brave["Brave Browser (History SQLite)"]
    end

    subgraph HistVault_Engine ["HistVault Extraction Engine"]
        Discovery["Profile Auto-Discovery"]
        ShadowCopy["Lock-Free Atomic Shadow Copy"]
        Parser["Chromium & Firefox Schema Parser"]
        Categorizer["Domain Classifier & Normalizer"]
        
        Browsers --> Discovery
        Discovery --> ShadowCopy
        ShadowCopy --> Parser
        Parser --> Categorizer
    end

    subgraph Vault ["Persistent Local Vault (vault.db)"]
        SQLite["SQLite WAL Mode + FTS5 Search"]
        Detector{"Is URL missing from current browser?"}
        
        Categorizer --> SQLite
        SQLite --> Detector
        Detector -- "Yes (User Cleared History)" --> FlagDeleted["Flag: is_deleted_from_browser = True"]
        Detector -- "No (Still in Browser)" --> FlagActive["Flag: is_deleted_from_browser = False"]
        FlagDeleted & FlagActive --> PermanentStorage["Permanent Archive (Zero Data Loss)"]
    end

    subgraph Interfaces ["User Access Interfaces"]
        WebGUI["Modern Local Web Dashboard (http://127.0.0.1:8765)"]
        CLI["Command-Line Interface (histvault CLI)"]
        Exporter["Export (JSON / CSV / HTML / Markdown)"]
        
        PermanentStorage --> WebGUI
        PermanentStorage --> CLI
        PermanentStorage --> Exporter
    end
```

---

## ⚡ Quick Start

### Installation

```bash
git clone https://github.com/virsi18/histvault.git
cd histvault
pip install -r requirements.txt
pip install -e .
```

### 1. Launch the Native Desktop Application (iOS Interface)

HistVault can run as a **native standalone desktop app** with dedicated window controls, Apple iOS design, and zero external browser tabs required:

```bash
# Via CLI command:
histvault desktop

# Or via Python launcher:
python run_desktop.py

# Or on Windows, simply double-click:
HistVault-Desktop.bat
```

* 🖥️ **Native Window:** Embedded Edge WebView2 desktop container (1180x820 window with native close/minimize/maximize).
* 🔍 **Instant Spotlight Search:** Instant history search across titles, URLs, and domains.
* 🛡️ **Anti-Deletion Guarantee:** Clear filter to inspect items deleted from browser history.

---

### 2. Launch in Web Server Mode (Alternative)

If you prefer accessing HistVault via standard web browser:

```bash
histvault serve
```
Then open: **`http://127.0.0.1:8765`**

---

### 3. Command-Line Interface (CLI)

#### Synchronize All Browsers
```bash
histvault sync
```

Output:
```text
>>> Scanning installed browsers and synchronizing history into Vault...

[SYNC COMPLETE]
 * Profiles Scanned:          5
 * New URLs Archived:         123
 * Updated URLs:              0
 * Newly Detected Deleted:    0 (Preserved in Vault!)
 * Total Records in Vault:    123
```

#### View Vault Statistics & Top Domains
```bash
histvault stats
```

Output:
```text
================ HISTVAULT STATISTICS ================
 Total Preserved History:     123 entries
 Deleted in Browser:          0 entries (100% Preserved)
 Active in Browser:           123 entries
 Total Recorded Visits:       214 visits
 Unique Domains:              17

--- Browser Breakdown ---
  * Chrome         : 106 records
  * Edge           : 17 records

--- Category Breakdown ---
  * Search & Reference       : 62 records
  * Development & Tech       : 40 records
  * General Browsing         : 21 records

--- Top Visited Domains ---
  * github.com               : 109 visits (40 URLs)
  * google.com               : 28 visits (24 URLs)
  * accounts.google.com      : 25 visits (24 URLs)
  * bing.com                 : 15 visits (10 URLs)
======================================================
```

#### Search Preserved History
```bash
histvault list -q "github" -n 10
```

#### List Only History That Was Deleted in Browser
```bash
histvault list --deleted-only
```

#### Export Your History Archive
```bash
# Export all history as an offline interactive HTML report
histvault export -f html -o report.html

# Export only deleted URLs to CSV for Excel
histvault export -f csv -o deleted_history.csv --deleted-only

# Export complete database to JSON
histvault export -f json -o backup.json

# Export to Markdown for Obsidian or Notion
histvault export -f md -o history.md
```

#### Run in Background as a Daemon
Continuously monitor browser database updates and archive changes automatically:
```bash
histvault watch --interval 30
```

---

## 💻 Python API Integration

```python
from histvault.core.database import VaultDatabase
from histvault.service.synchronizer import VaultSynchronizer
from histvault.service.exporter import HistoryExporter

# 1. Initialize local vault
db = VaultDatabase()
synchronizer = VaultSynchronizer(db)

# 2. Sync all installed browsers
report = synchronizer.sync_all()
print(f"Preserved {report.total_preserved_urls} URLs across {report.profiles_scanned} profiles.")

# 3. Query history with anti-deletion filter
deleted_items = db.search_urls(deleted_only=True)
for item in deleted_items:
    print(f"[PRESERVED DELETED] {item.browser_name} | {item.domain} | {item.title} -> {item.url}")

# 4. Export to standalone report
exporter = HistoryExporter(db)
exporter.export_html("my_history_archive.html")
```

---

## 🧪 Running Tests

The test suite runs using standard `unittest`:

```bash
python -m unittest discover tests
```

Output:
```text
.........
----------------------------------------------------------------------
Ran 9 tests in 0.143s

OK

 [TEST VERIFIED] Browser history purged, but 100% preserved in HistVault!
```

---

## 📂 Project Structure

```text
histvault/
├── histvault/
│   ├── __init__.py
│   ├── constants.py               # Cross-platform browser paths & category rules
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py              # Data models (HistoryEntry, BrowserProfile, SyncReport)
│   │   ├── categorizer.py         # Automatic domain classifier
│   │   ├── database.py            # SQLite WAL persistent vault with FTS5 search
│   │   └── extractor.py           # Multi-browser lock-free snapshot extractor
│   ├── service/
│   │   ├── __init__.py
│   │   ├── synchronizer.py        # Multi-profile synchronization coordinator
│   │   ├── watcher.py             # Background daemon file watcher
│   │   └── exporter.py            # JSON, CSV, Markdown, Standalone HTML exporter
│   ├── server/
│   │   ├── __init__.py
│   │   ├── app.py                 # Pure standard library HTTP REST API server
│   │   └── static/
│   │       ├── index.html         # Responsive glassmorphic Web GUI dashboard
│   │       ├── style.css          # Dark slate modern styling
│   │       └── app.js             # Client controller with live search & filters
│   └── cli/
│       ├── __init__.py
│       └── main.py                # Command-line interface
├── tests/
│   ├── test_database.py           # Vault database tests
│   ├── test_categorizer.py        # Domain classifier tests
│   ├── test_exporter.py           # Multi-format export tests
│   └── test_synchronizer_deletion.py # Core deletion preservation lifecycle test
├── pyproject.toml
├── setup.py
├── requirements.txt
├── .gitignore
├── LICENSE                        # Apache License 2.0
└── README.md
```

---

## ⚖️ License

Distributed under the **Apache License, Version 2.0**. See the [LICENSE](LICENSE) file for details.

```text
Copyright 2026 HistVault Open Source Project Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```

