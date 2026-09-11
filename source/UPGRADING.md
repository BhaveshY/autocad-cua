# Upgrading the bundled Cua driver

Normal tasks use this plugin's pinned executable. Updating global Cua does not replace it. The upgrade check runs only when requested, adding no delay to normal tasks.

1. Obtain a trusted Windows x64 candidate. Check its published checksum when available:

   ```powershell
   python scripts/check_driver_compatibility.py C:\Downloads\cua-driver.exe --sha256 EXPECTED_SHA256
   ```

   Omit the path to check the current bundled driver. This calls only CLI metadata commands; it never starts MCP, sends input, installs or replaces anything.
2. The check accepts new optional parameters, documentation changes and wider enums. It lists removed parameters, new requirements, changed defaults/constraints and missing launch flags. It cannot prove output formats, targeting, background behavior or app compatibility.
3. Review upstream changes and `autocad-observation.patch`; retain needed observation behavior or verify its upstream replacement. In a separate candidate checkout, replace the bundled EXE and update `runtime.json` with its SHA-256/version/source revision. Update dependency notices if needed. Never weaken the runtime hash check or switch to global Cua.
4. Run `python -m unittest discover -s tests`, then a small disposable task through the candidate plugin: exact window binding, intended edit/readback, and cursor/focus behavior. For AutoCAD also verify dimensions and Undo; for Windows Cua verify the relevant app and permission-controlled restoration. Use foreground control only with explicit permission.
5. After acceptance, refresh `driver-contract.json` from the accepted candidate's `describe` schemas, bump the plugin cachebuster, verify the installed cache and ZIP, and publish a new release. Keep the previous release available for rollback. Do not regenerate the baseline merely to hide a failed check.

The plugin's MCP tools stay stable for agents while its adapter handles reviewed upstream differences. Future breaking changes still need a compatibility fix; metadata passing alone is not release approval.

Upstream references: [CLI metadata](https://cua.ai/docs/reference/cua-driver/cli-reference), [driver updates](https://cua.ai/docs/how-to-guides/driver/update).
