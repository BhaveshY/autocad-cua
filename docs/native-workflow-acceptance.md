# Native workflow acceptance — 11 September 2026

Tested locally in full German AutoCAD 2019 on Windows, using the installed plugin. Windows Cua was unchanged.

The disposable drawing test passed: tab switching rejected by the original task, backup verified, deliberate prerequisite failure preserved all 239 entities, three helper objects created with a measured 6000 mm dimension and 150 mm text height, duplicate execution did not duplicate objects, and partial failure recovered by handle. Temporary fixture closure was subsequently verified.

The installed update then replaced the authorized Office drawing with a 3-BHK concept: 283 entities, 12 native dimensions checked against intended millimetre values, 144 m² enclosed footprint, two bathrooms, balcony, furniture, and A3 PDF at 1:75. The original 2-BHK was backed up with matching SHA-256. The DWG was saved and its delivery copy hash checked. Visual review moved two labels and one dimension without rebuilding. The other open drawing retained its original window, 41 entities and unsaved state.

Final layout/code through visual acceptance took **5m49s**, including planning and review. Preliminary layout reasoning occurred during plugin development, so this is not a clean from-scratch benchmark. Three successful native jobs took 7.43s, 3.12s and 3.33s; no failed drawing dispatch or redraw. The main batch used 94 staging chunks, versus roughly 263–282 in the prior 2-BHK run. One complete geometry inspection replaced repeated full scans; other reads were identity-only or targeted. Token usage was unavailable. Foreground interruption was authorized; a focus change was observed during plotting, so this is not cursor-preservation proof.

Development exposed and fixed a backup-hash dependency on a missing PowerShell cmdlet. Separate test-harness failures involved execution policy, path quoting and cleanup; they are not counted as successful acceptance. AutoCAD also transiently rejected read calls. An uncertain mutation must still be inspected before recovery.

Repository checks and a clean-profile installation on this host are not another-PC certification. Full AutoCAD 2019 is the supported local baseline; colleagues should run setup and a disposable drawing check. This is a validated concept-drafting workflow, not a promise to execute every AutoCAD command or deliver construction approval.
