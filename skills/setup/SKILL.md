---
name: setup
description: Check this plugin's Windows platform, pinned Cua driver, Python runtime and AutoCAD prerequisites.
---

# Setup

On first use call this plugin's MCP `status`. Its launcher locates Python and checks the pinned driver automatically. After installation, use a new Codex thread to load its tools.

For startup failure, run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/doctor.ps1`. It launches no app. Resolve missing Python through Codex's `load_workspace_dependencies`.

Doctor proves prerequisites only. Verify a disposable task and cursor/focus preservation on each new host/version. For CAD, check geometry and Undo restoration. Do not replace global Cua, restart CAD or change security settings as repair shortcuts.
