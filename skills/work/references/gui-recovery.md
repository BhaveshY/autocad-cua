# Windows control and recovery

## Routing

- **App API / document library:** use for structured edits or independent readback when supported and consistent with the user's request. Report this as API work, not Cua input. Mail-controller restrictions still apply.
- **Plugin MCP:** default for visual discovery and adaptive UI actions; keeps tokens and evidence in one guarded session, without worker shell access.
- **Bundled Python Client / sequence CLI:** use for known, prompt-checked batches. Reuse the Client across units; one-shot CLI is for diagnostics or isolated unindexed calls. Close the previous owner before switching; refresh targets and tokens.
- **In-process SDK:** consider only in an available, verified integration with equivalent targeting, ownership and permission checks. It is not bundled as a guarded input route. Earlier same-release testing reduced startup overhead but did not establish a universal task speedup. Do not swap the pinned runtime or bypass guards to use it.

Switch to resolve a concrete capability/access problem or a measured bottleneck. Compare completion including verification; changing transport does not repair an unsupported app control.

## Calls

Use this plugin's MCP tools first: `status`, `start_session`, bounded `list_windows`/`get_window_state`, supported input, verification, `end_session`. The returned session owns one persistent guarded Client; evidence is under `%LOCALAPPDATA%/AutoCAD-Cua/evidence`. `instructions` reads fixed bundled references without worker shell access. End the MCP session before using a bundled CLI sequence, which acquires the same ownership lock.

For missing plugin tools, verify installation and load a new Codex thread. For startup errors, diagnose with setup. Other apps and global Cua are not substitutes for reading instructions. Host restrictions still apply. The OS releases crashed owners; confirm old workers and descendants have exited before replacement. Other drivers do not participate in this lock.

Probe `cua.py describe TOOL` before unfamiliar calls. `--arguments` takes a **JSON file path**, not inline JSON. `cua.py invoke click` takes observed exact `pid`, `window_id`, `delivery_mode`, `label`, `role` and `automation_id`; it snapshots and invokes the unique enabled match in one session. Ordinary one-shot calls reject external element tokens.

For short sequences, import from this plugin's `scripts` directory:

```python
from runtime import driver_path
from run_sequence import Client
client = Client(driver_path(), new_evidence_directory)
try:
    state, ms = client.call("get_window_state", exact_target_and_bounds)
    # Select a current supported action, execute it, then verify the result.
finally:
    client.close()
```

The client uses local `mcp --direct --no-overlay`: no decorative glide delay, unchanged input pacing and checks. `show_overlay=True` opts back into the indicator. Neither option enables foreground input. Full evidence stays on disk; return concise verified results. Measure completion including verification, not dispatch alone.

## Recovery

When the user explicitly permits interruption, start a session with `allow_interruption:true` (Python Client has the same keyword). This permits exact-window foreground input and normal launch; changes remain logged. Default sessions retain background guards. Permission does not establish that an action worked.

The helper refuses input when the target process owns the foreground window, including another window in that process. Let the user finish there, then recheck document and command state before recovery. It also checks live HWND ownership before dispatch. These checks reduce collisions; they cannot lock the desktop or prevent a later app activation.

- `session_ended`: explicitly start the intended label, then refresh state. Reviving a different label does not repair implicit-session calls. After an input timeout, observe before any retry.
- Missing controls: inspect `../../../scripts/native_windows.ps1` output for the exact PID/HWND, then snapshot a relevant named child. A minimized app can hide its children entirely. Bounds around `-32000` are not usable screen coordinates. Do not automatically restore or activate it.
- Store launcher exits: discover the AUMID through `list_apps`; bind the returned live window. Calculator may belong to `ApplicationFrameHost.exe`. A launch PID or splash screen alone does not establish readiness.
- Windows launch paths with spaces: this pinned driver joins `additional_arguments` as raw text. Pass `[subprocess.list2cmdline(argv)]` to preserve quoting. This fixes argument splitting, not app self-activation. `start_minimized:true` preserved foreground in local Office/CAD starts, but hid controls needed for GUI work. Prefer an already-open normal window or a supported app API.
- `background_unavailable`, self-activation or missing readback: inspect current state and identify the unsupported control, stale target or app readiness issue. Repair the cause using supported background operations or an authorized app API, then verify before resuming. Reopening a connection does not repair the cause. Foreground control requires explicit permission.

## AutoCAD

COM reads may be rejected during an active command; wait for observed idle and retry only the read. Capture the named drawing child if the main image is blank.
