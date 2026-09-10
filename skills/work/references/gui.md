# AutoCAD GUI control

1. **Choose the route.** Preserve the user's requested tool. Otherwise prefer a supported app API for document operations, this MCP for UI discovery, and the bundled persistent runner for known sequences. SDK is not automatically faster; see [routing](gui-recovery.md#routing).
2. **Connect once.** MCP: `status`, `start_session`; retain its token. `instructions` works without shell. One GUI worker; confirm it and descendants exited before replacement. Reuse the existing app window.
3. **Bind and act.** Snapshot exact PID/HWND/document; use fresh tokens and explicit background delivery. Preserve cursor, focus, clipboard and stacking. Only explicit user permission allows `allow_interruption:true` and foreground fallback. Indexed text appends; verify the complete value.
4. **Recover and verify.** Diagnose failures, repair the cause, then retry from observed state. Verify each effect before dependent input. End the session; report completed versus untested work and evidence.

For GUI recovery read [gui-recovery.md](gui-recovery.md); for CAD prompt sequences read [commands.md](commands.md).
