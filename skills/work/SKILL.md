---
name: work
description: Create, edit and verify AutoCAD drawings; choose native AutoLISP batches or Cua visual control for the task.
---

# AutoCAD work

1. **Bind:** `cad_inspect` pins the first drawing for this task. Retain its `task` token across connections; never reset `new_task` to recover a target mismatch. Preserve existing work and define acceptance criteria.
2. **Choose:** native AutoLISP for precise/repeated edits; Cua for visual discovery, dialogs and UI-only features. Honor Cua-only requests. End Cua before native execution.
3. **Qualify:** reuse locally verified methods where applicable. For unfamiliar commands/APIs, check installed-version Autodesk documentation and required features; do not guess signatures or prompts. Test a representative operation in a disposable copy for uncertain or high-impact batches; verify before scaling. Skip redundant probes for proven operations.
4. **Execute:** read [native.md](references/native.md). Use [helpers](references/helpers.md) for tested primitives. For replacement, use `helpers:true`, `replace_model:true`, a new `backup_path`, and prerequisite-only `setup_code`; the plugin backs up and verifies before clearing. `cad_prepare` freezes code/preconditions; execute its exact job/hash.
5. **Verify/correct:** retain returned handles; inspect only affected entities for intermediate checks. Use identity-only checks for save/plot, full geometry at acceptance, and visual readback. Fix small defects by handle, not full redraw. On failure inspect before recovery; never replay blindly. `executed` alone is insufficient.

Use [GUI control](references/gui.md) for GUI ownership, [commands.md](references/commands.md) for prompt sequences and [visual.md](references/visual.md) for image-based drawings. Never invent unreadable dimensions or assume an untested version works.
