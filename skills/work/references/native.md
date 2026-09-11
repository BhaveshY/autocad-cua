# Native execution

The same plugin exposes four stable tools: `cad_inspect`, `cad_prepare`, `cad_execute`, `cad_result`. Windows PowerShell 5.1 attaches to running AutoCAD through COM; it never launches it. No add-in, new service or separate SDK installation is required. Tested in full AutoCAD 2019; other editions/versions need local acceptance.

## Prepare and execute

1. Inspect once to bind the intended drawing; retain the returned `task` across reconnections. Subsequent inspections remain bound even after saves change its disk hash. Save unnamed drawings first. Identity includes process start, application/document HWNDs, full path and on-disk SHA-256. Unsaved edits need task-specific preconditions; file identity alone cannot detect them. Use `new_task:true` only when the user actually chooses another drawing.
2. Prepare noninteractive AutoLISP with a short description and read-only precondition. Prefer `entmakex`, `entget`, `entmod` and `vla-*` database operations; use `command-s` with complete arguments when necessary. Bind ModelSpace/PaperSpace deliberately. Avoid prompts, dialogs, document switches and unbounded loops. Scripts are trusted code, not sandboxed.
3. Execute the returned job and exact hash. The bridge stages short source chunks to avoid command-line limits, rechecks target/preconditions inside AutoCAD and groups edits for Undo. Do not change global security settings or trust paths. Only explicitly authorized interruption permits `allow_interruption:true`.
4. Inspect affected handles or bounded geometry independently. Return/save intended handles from the Lisp result when useful. The reported model-space total is separate from returned entities. Check measurements with a stated tolerance, text, layers, layout and rendered output. Verify saved files separately.

Example precondition for an empty metric model:

```lisp
(and (= (getvar "INSUNITS") 4)
     (= (getvar "CTAB") "Model")
     (= (vla-get-Count
          (vla-get-ModelSpace
            (vla-get-ActiveDocument (vlax-get-acad-object)))) 0))
```

Match real state; count alone is insufficient when editing existing entities. A false precondition fails before the body runs. Preconditions themselves must not mutate anything.

## Recovery

Before scaling unfamiliar work, check required methods/properties read-only (for example `vlax-method-applicable-p` / `vlax-property-available-p`); availability alone does not prove correct behavior. Reuse a successful probe only while version, feature, units/space and relevant entity assumptions still match. Keep its method, elapsed time and verification result with task evidence; compare completed, verified work when evaluating speed.

- Repeating `cad_execute` for the same job returns its existing record; it does not run again. Changed plan/hash is refused. Prepare a new job only after reviewing the actual state.
- Errors can leave partial changes; there is no automatic rollback promise. If no intervening changes occurred, prepare `(command-s "._UNDO" "1")` with `undo_group:false`; verify exact restoration. Saving and read-only queries can also use `undo_group:false` to avoid unnecessary Undo marks.
- Missing, incomplete or unreadable receipts/timeouts are uncertain, not failure proof. Poll `cad_result`; native execution may still finish. Use Cua to inspect/cancel a demonstrated incomplete prompt. Once target and relevant geometry are inspected and AutoCAD is idle, `cad_result(resolve_after_inspection:true)` permits a new job without marking the old one successful.
- A stale drawing/file hash requires fresh inspection and preparation. Do not substitute another drawing or clear a job record. AutoCAD's command errors may be localized; raw error text stays with the job evidence.
- Older AutoLISP has string-literal limits. Construct long text with `strcat` pieces instead of one oversized literal. The bridge handles transport chunking; do not add sleeps or hand-send generated scripts through GUI typing.

MCP is the default interface; a Python caller may import `CadBridge` from bundled `scripts` and reuse it. That uses the same checks and receipts. Direct COM/SDK calls do not inherit them. Use Cua or a supported API for a demonstrated capability gap, not to evade an unresolved native outcome.

For replacement and tested primitives, read [helpers.md](helpers.md) or request `instructions(topic:"native-helpers")`. Use identity-only inspection between non-geometric jobs. Request `handles` and `detailed:true` for corrected text/dimension properties. Small edits need affected-object verification and a visual check; new/replaced plans need one full geometry scan at acceptance. Do not rescan after saves or settings changes.

`saved:false` is normal unsaved state: preserve it when needed, rather than failing and repeating inspection. For small edits to a user-declared disposable fixture, skip extra backups. Replacement jobs still require the plugin's verified backup.

Autodesk references: [SendCommand and asynchronous cases](https://help.autodesk.com/cloudhelp/2021/ENU/AutoCAD-ActiveX-Reference/files/GUID-E13A580D-04CA-46C1-B807-95BB461A0A57.htm), [AutoLISP exception handling](https://help.autodesk.com/cloudhelp/2023/ENU/AutoCAD-AutoLISP-Reference/files/GUID-E08CC2A6-787A-422F-8BD3-18812996794C.htm).
