---
name: work
description: Create, edit and verify AutoCAD drawings; choose native AutoLISP batches or Cua visual control for the task.
---

# AutoCAD work

1. **Inspect:** `cad_inspect` binds the live target, units/UCS/space and bounded geometry. Preserve existing work; define measurable acceptance criteria.
2. **Choose:** native AutoLISP for precise/repeated edits; Cua for visual discovery, dialogs and UI-only features. Honor Cua-only requests. End Cua before native execution.
3. **Qualify:** reuse locally verified methods where applicable. For unfamiliar commands/APIs, check installed-version Autodesk documentation and required features; do not guess signatures or prompts. Test a representative operation in a disposable copy for uncertain or high-impact batches; verify before scaling. Skip redundant probes for proven operations.
4. **Execute:** read [native.md](references/native.md). `cad_prepare` freezes code/preconditions; `cad_execute` takes job/hash. Check relevant units, space and affected geometry. Batch independent edits; verify before dependent stages.
5. **Recover/verify:** on uncertainty inspect `cad_result` and actual state; correct the cause before retrying or switching routes. Never replay blindly. Compare geometry, dimensions, saved files and rendering against acceptance criteria; `executed` is insufficient.

Use [GUI control](references/gui.md) for GUI ownership, [commands.md](references/commands.md) for prompt sequences and [visual.md](references/visual.md) for image-based drawings. Never invent unreadable dimensions or assume an untested version works.
