---
name: work
description: Create, edit and verify AutoCAD drawings; choose native AutoLISP batches or Cua visual control for the task.
---

# AutoCAD work

1. **Bind:** `cad_inspect` pins the drawing; retain its `task` across connections. Never reset `new_task` to recover a target mismatch. `saved:false` means unsaved work, not failure. Preserve it and define acceptance criteria.
2. **Choose:** native AutoLISP for precise/repeated edits; Cua for visual discovery, dialogs and UI-only features. Honor Cua-only requests. End Cua before native execution.
3. **Qualify:** reuse locally verified methods where applicable. For unfamiliar commands/APIs, check installed-version Autodesk documentation and required features; do not guess signatures or prompts. Test a representative operation in a disposable copy for uncertain or high-impact batches; verify before scaling. Skip redundant probes for proven operations.
4. **Execute:** read [native.md](references/native.md). Use [helpers](references/helpers.md) for tested primitives. For replacement, use `helpers:true`, `replace_model:true`, a new `backup_path`, and prerequisite-only `setup_code`; the plugin backs up and verifies before clearing. `cad_prepare` freezes code/preconditions; execute its exact job/hash.
5. **Verify/correct:** inspect affected handles for small edits; one full geometry scan for new/replaced plans. Use identity-only reads for saves/settings and visual readback for layout. Correct by handle. Inspect before recovery; never replay blindly. Verify saved output; `executed` alone is insufficient.

Use [GUI control](references/gui.md) for GUI ownership, [commands.md](references/commands.md) for prompt sequences and [visual.md](references/visual.md) for image-based drawings. Never invent unreadable dimensions or assume an untested version works.
