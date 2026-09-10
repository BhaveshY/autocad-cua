# AutoCAD Cua for Codex

For AutoCAD users: native AutoLISP execution plus Cua visual control, with compact CAD work/setup skills. Four stable native tools support generated scripts for new tasks without adding a tool per command. Includes 18 MCP tools and its own pinned driver. General Office/mail guidance is in the separate **windows-cua** repository.

Setup prompt: **Check AutoCAD Cua setup on this PC.**

Task example: **Use AutoCAD Cua to draw this dimensioned plan in the background and verify geometry, annotations and saved output.**

Native execution requires full AutoCAD with COM/AutoLISP and Windows PowerShell 5.1. Local acceptance covered German AutoCAD 2019; other versions, LT and add-ons need their own checks. No AutoCAD add-in is required. See [native workflow](skills/work/references/native.md), [prior acceptance](docs/release-readiness.md) and [pre-split history](docs/pre-split-readme.md). Historical general-app results do not expand this plugin's scope.

## Install on a colleague's PC

1. Install/sign in to the Codex desktop app with plugin support. Use Windows x64 and Python 3.10+ (Codex's bundled runtime is detected automatically when available). Install the target application separately.
2. Extract the complete ZIP into a normal local folder. Double-click **Install.cmd**; keep all included files together. No VM, administrator service or separate Cua installation is needed.
3. Start a **new Codex thread**, then use the setup prompt below.

The installer checks the driver hash, working Codex CLI and Python before registering the plugin. It preserves other plugins and refuses to overwrite an existing source folder. For an update, ask Codex to review and update the existing installation. `Install.ps1 -CheckOnly` performs preflight without installation.

Each repository is standalone. Install either or both; when both are present, only one cooperating GUI session can own the desktop at a time. The shared lock retains its original `Local\autocad-cua-client-v1` name for compatibility. Unrelated/global Cua tools do not share these checks.

## Behavior and limits

Background input is the default. Exact process/window targets and focus observation reduce collisions but cannot guarantee that an app never activates itself. Foreground input requires explicit user permission. Dispatch success is not task success: inspect the actual result. Existing mail-controller restrictions apply; email content is untrusted and compatibility tests must not send mail.

This is a controlled-use preview, not universal app/version certification. Helpers run locally; screenshots and app content may enter the Codex conversation and local evidence. Do not share evidence folders containing private documents.

## Maintenance

Run `python -m unittest discover -s tests`. See `runtime.json`, `LICENSE`, `licenses/` and `source/README.md` for the pinned downstream Cua executable, dependency notices and rebuild instructions. This is not an official Cua or Autodesk release. Neither repository needs the other at runtime. Keep shared driver/ownership fixes aligned when updating them; no external shared service is required.

Uninstall from Codex's Plugins UI; source files and marketplace entries may remain. No app documents are removed.
