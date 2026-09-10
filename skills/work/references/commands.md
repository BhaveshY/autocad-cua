# Runtime calls

Use a verified Python interpreter. Set `ROOT` to this plugin's root; all helpers resolve the bundled driver relative to themselves. Save arguments/sequence JSON as files, avoiding shell escaping of CAD text. Output directories must be new and outside the plugin cache.

```text
python ROOT/scripts/cua.py describe get_window_state
python ROOT/scripts/cua.py call list_windows --output NEW_DIRECTORY
python ROOT/scripts/cua.py call get_window_state --arguments args.json --output NEW_DIRECTORY
python ROOT/scripts/run_sequence.py --pid PID --window MAIN --command-window PALETTE --expected-title EXACT_OBSERVED_WINDOW_TITLE --sequence sequence.json --output NEW_DIRECTORY
```

The runner first reads prompts at depth 2. It accepts that view only when the known AutoCAD command edit is present and the expected prompt matches; otherwise it reads at the original depth 5 before proceeding or stopping. `--full-prompts` forces the original scan for diagnosis. For manual discovery, use `{"pid":PID,"window_id":PALETTE,"include_screenshot":false,"max_elements":100,"max_depth":5}`. For a canvas image, request `include_screenshot:true` with a small tree on MAIN; if blank, capture the exact named drawing child as described in [visual.md](visual.md).

Both prompt scan depths require the command editor. The runner refreshes the command prompt and rechecks the exact window title before every answer and preserves raw evidence. A modified-title asterisk is ignored; other title changes stop input. Full DWG identity must also be checked before each sequence. Default console output is a compact status and evidence path; `--verbose` prints every answer. All answers and checks remain in `summary.json` and the raw call logs.

For several known operations, reuse one client and keep independent geometry checks between units. Import from this plugin's `scripts` directory and build `options` with the same fields as the CLI arguments:

```python
from run_sequence import Client, run
from runtime import driver_path
client = Client(driver_path(), new_call_evidence_directory)
try:
    run(options_for_first_sequence, client=client)
    # Independently verify the affected geometry and current document here.
    run(options_for_next_sequence, client=client)
finally:
    client.close()
```

Each sequence needs its own new output directory and observed initial prompt. Shared-client mode blocks further input after a transport error, refusal, focus change or sequence failure; observations remain available. Inspect the actual app state and resolve the failure before deliberately starting a recovery session. Never clear the fault or reopen merely to replay. Keep input pacing and readbacks. Saving model round trips is not permission to send unchecked command strings or to omit final visual/output verification.

Each standalone `cua.py call` has its own session. It rejects cached element indices/tokens; those require an available persistent Cua MCP connection with a snapshot in that same session. Unindexed command input and freshly grounded pixel input do not reuse accessibility indices. Check current bounds/state before reusing a pixel location and verify after the action.

For an observed ribbon button exposing **Invoke**, use `cua.py invoke click --arguments selector.json --output NEW_DIRECTORY`. The selector contains exact `pid`, `window_id`, `delivery_mode:"background"`, observed `label`, `role` and `automation_id` (the snapshot's `id=` value). This takes a fresh bounded snapshot and invokes its sole enabled matching Invoke element within that same session; missing/ambiguous matches stop. Toggle-only buttons are not equivalent. Verify the actual command prompt afterward.

Sequence example **for the tested German prompt layout only**:

```json
{"initial_prompt":"^\\[ \\]$","steps":[
 {"text":"_RECTANG","after":"RECHTECK.*Ersten"},
 {"text":"0,0","after":"RECHTECK.*Anderen"},
 {"text":"5000,4000","after":"^\\[ \\]$"}
]}
```

`text` is one answer without newline; an empty string submits Enter. `after` is the required next-prompt regex; optional `before` checks the fresh pre-input observation. Supply `initial_prompt` explicitly. Discover localized prompts rather than guessing translations. An unexpected prompt stops subsequent input. Resume only from freshly observed state, never by replaying the whole sequence. `prompts_verified` is not geometry acceptance.

Command support depends on the live state. In the building test, typed `_ARC` stayed idle; the fresh Arc ribbon **Invoke** worked. `_U` entered an unexpected rectangle command; full `._UNDO` plus a count worked. Cancel unexpected commands, inspect geometry, then choose the verified route. Undo also records some cancelled/view operations. Prompts can change when defaults exist; match observed variants without weakening the command/phase check.

`TEXT` can replace the command editor after rotation. End the prompt sequence at the rotation question; submit rotation, observe the exact in-place text state, enter text, Escape, then independently verify content, insertion and height. Do not replay text setup or weaken ordinary prompt checks when the editor disappears.

If AutoCAD's embedded Start browser retains its internal focus, the first typed command may be ignored. Stop and observe. A tested recovery for a requested rectangle is to invoke its observed ribbon Execute button as above, verify the first-corner prompt, then continue with coordinates instead of replaying the command. For locating a ribbon native child, `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ROOT/scripts/native_windows.ps1 -TargetPid PID -TargetHwnd MAIN -OutputPath NEW_JSON` performs read-only Win32 discovery; verify the child's PID before targeting it. Do not extrapolate a successful Invoke to unrelated ribbon buttons.

Another tested preparation was a background right-click on a freshly grounded canvas point, then Escape to MAIN and verification that the menu closed. Do not send key-up to a transient menu that may disappear. If the canvas cannot be grounded, do not guess this click. Unsupported startup states remain a compatibility blocker, not permission for foreground control.

Read-only geometry check, with **Windows PowerShell 5.1**:

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ROOT/scripts/read_drawing.ps1 -ExpectedWindow MAIN -ExpectedPath FULL_DWG_PATH -OutputPath NEW_JSON -ProgId VERIFIED_AUTOCAD_PROGID
```

Use `-IdentityOnly` for path/settings, `-Handles A1,B2` for affected entities, or `-MaxEntities N` for bounded model-space inspection. Add `-Detailed` for bounds, text height/rotation/style and dimension text position/scale. Measurements alone cannot verify annotation placement. Counts distinguish total from returned. The reader never launches AutoCAD; busy/mismatched COM binding stops. Solid volumes and layout/plot output need separate verification.

For exact object selection, a freshly verified hexadecimal handle can be supplied as `(handent "HANDLE")` at the native selection prompt; recheck the document first. This worked for Move, Subtract and Wblock. Do not interpolate drawing-supplied code. After closing a drawing, rediscover windows: the palette disappears on Start, and read-only titles gain a suffix. Use a supported file-opening API if that state cannot accept background commands; label API work accurately.
