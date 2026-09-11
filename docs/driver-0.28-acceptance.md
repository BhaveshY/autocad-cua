# Driver 0.28.0 acceptance — 2026-09-11

Both plugins bundle Cua Driver 0.28.0 with the existing observation patch (downstream identity `0.28.0-local.1`). Upstream tag: `cua-driver-rs-v0.28.0`, commit `1b50c02e2d34734f64d2d22f54eb76cc97b4a663`. The Windows x64 build uses locked dependencies, Rust 1.97.1 and the static MSVC runtime.

The patch applies unchanged: bounded UIA traversal, direct HWND lookup, and untitled owned-window discovery. Input delivery code is unchanged by our patch. Reviewed schema change: click's optional target no longer accepts null; plugin MCP tools do not expose this override and continue using exact PID/HWND. The compatibility checker remains conservative; its baseline now records the accepted release.

Validation on this Windows PC:
- AutoCAD plugin: 96 automated tests passed. Windows plugin: 59 passed.
- Through the candidate Windows plugin MCP adapter: background text entry and button invocation independently verified by the disposable app's saved text. Input calls took 13 ms and 12 ms, excluding discovery and verification.
- AutoCAD 2019 bounded observation with screenshot: 1.52 seconds. A stale target after the app restarted was rejected; fresh discovery succeeded.
- Thunderbird, PowerPoint and Word bounded accessibility reads succeeded (76–102 ms). These were observations, not new mail or document-edit acceptance tests.
- Input guards reported no focus change during the two fixture inputs. The user was active during testing; overall cursor movement and one focus change were observed. This does not certify uninterrupted operation for every app.

Native AutoCAD bridge, geometry helpers and agent skills are unchanged. Their earlier drawing acceptance remains documented separately; a full drawing/Undo task was not repeated during the user's active AutoCAD work. This upgrade does not broaden the supported application/version claims. Each new PC still needs its small setup and disposable app check.

The previous release remains available for rollback. Future upstream versions are reviewed and pinned, never silently downloaded during ordinary tasks.
