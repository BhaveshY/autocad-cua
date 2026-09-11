# AutoCAD 2019 helpers

Set `helpers:true` in `cad_prepare`. The exact helper source is frozen into the job hash. It resolves an installed font by absolute path, creates a zero-height text style and initializes `acua:doc`, `acua:ms`, `acua:handles`. Helpers do not choose layout, units or dimensions for the user.

Put resource setup in `setup_code` (layers, units, prerequisite checks). It runs before model deletion. Example: `(progn (setvar "INSUNITS" 4) (acua:layer "A-WALL" 7 40))`. With `replace_model:true`, `backup_path` must be a new absolute DWG path. The host saves and copies the bound drawing, verifies SHA-256, then dispatches code. A failed prerequisite cannot reach model deletion. Code remains trusted, not sandboxed; do not put destructive edits in setup.

All geometry functions return a handle. Points are quoted coordinate lists; angles are radians. Dimensions are drawing units.

| Function | Arguments |
| --- | --- |
| `acua:layer` | name, AutoCAD color index, valid lineweight enum |
| `acua:rect` | x, y, width, height, layer |
| `acua:poly` | point list, layer, closed boolean |
| `acua:line` | start point, end point, layer |
| `acua:text` | point, height, string, layer, centered boolean |
| `acua:arc` | center, radius, start angle, end angle, layer |
| `acua:circle` | center, radius, layer |
| `acua:dim` | first point, second point, dimension location, rotation, text height, layer |
| `acua:plot` | new PDF path, canonical media name, lower/upper window points, scale denominator |

`acua:dim` sets properties on the dimension itself; system-variable overrides alone do not size COM-created dimensions correctly. `acua:plot` uses DWG To PDF.pc3 and monochrome.ctb; confirm the supplied canonical media exists on the host. For A3 landscape: `ISO_full_bleed_A3_(420.00_x_297.00_MM)`.

End a creation job with `(acua:finish)` to return `data.handles` and the model count. Retain the relevant handles for `cad_inspect(handles:[...], detailed:true)` and targeted `entmod`/`vla-*` corrections. Do not re-run a creation job to correct one label. One full geometry inspection and a plotted/screenshot review are normally enough at final acceptance.

For Python, reuse one `CadBridge` or resume with `CadBridge(task=token)`. On MCP the bridge persists for the connection; send the token when reconnecting. A changed active document is rejected, not adopted. `new_task:true` is only for a genuinely different user-selected drawing, never a retry workaround.
