# Measured performance iteration

On one Windows x64 PC with German AutoCAD 2019, the same independently verified four-operation workflow took **13.3 seconds median**, down from **32.0 seconds**: **58.4% less time**. All nine benchmark workflows passed, with full geometry and settings checks after every operation. Input pacing, exact-title checks and foreground monitoring were retained.

| Version | Three task times, seconds | Median |
|---|---|---|
| Previous helpers | 32.79, 31.89, 32.00 | 32.00 s |
| Smaller sufficient prompt reads + shared connection | 27.24, 27.36, 28.18 | 27.36 s |
| Above + direct read-only COM property access | 13.41, 13.27, 13.32 | 13.32 s |

Each workflow created a circle, copied it, rotated the copy and undid all three changes. Its 17 prompt answers were checked individually. Each of the four units ended with a complete entity/settings read: exact centres and radii, preserved original entities, correct units/settings, and full restoration after Undo. Baseline and intermediate runs were interleaved; the final three runs followed the verifier change. All used the same already-open disposable drawing and pinned driver.

Timing includes driver/client startup and cleanup, all Cua calls, full independent readback, assertions and evidence logging. It excludes AutoCAD launch, fixture preparation, model reasoning, separate visual checks and closing the app after the tests. Three repetitions per version establish a local improvement, not a broad latency distribution or a universal promise.

## Changes retained

- Read the small command palette at depth 2 only when its known command edit and expected prompt are present. Otherwise use the original depth 5 before proceeding or stopping. A live inline-text case exercised this fallback. Full scanning remains available with `--full-prompts`.
- Reuse one Cua connection across known units, keeping every answer/title/prompt check and independent verification. The same failure guard remains active across units.
- Replace repeated reflection for read-only COM properties with direct property access. Every previously reported entity field and setting remains; missing properties still fail. Full verification fell from about 22.0 to 7.7 seconds per workflow. No geometry API writes were introduced.
- Print compact status and evidence paths by default. Full raw logs and answer records remain on disk; `--verbose` restores detailed console output. Median console output fell from 2294 to 1035 bytes (55% less). These are bytes, not measured tokens.
- Reject unknown or unguarded helper operations before dispatch. Explicit exact-window background input remains required.
- Capture AutoCAD's independently identified **named drawing child** when MAIN shows a blank canvas. It displayed actual geometry while MAIN remained blank, and its subsequent zoomed/restored captures showed the changed views. The capture target is discovered, never hardcoded.

## Regression evidence

**23 automated tests** passed. Live checks also passed nine additional AutoCAD stages covering layer creation, a concave polyline, Mirror/Move/Scale, Unicode text, arc, dimension, restored settings and Save; five reader contract cases covering identity-only, handle filtering, explicit truncation, wrong HWND and wrong path; and Calculator's six arithmetic/recovery cases with 39 independently verified button actions. The final DWG contains 20 entities: all original 15 remain unchanged, plus five verified additions. Full geometry/settings were unchanged after the visual check.

The passive monitor recorded **139,039 samples over 24.8 minutes** with no observed physical cursor, foreground or keyboard-focus change. No foreground fallback or cursor restoration was used. Sampling cannot rule out every transient or prevent an app from self-activating. The earlier Thunderbird first-run button failure still applies; no new mail workflow was tested. PowerPoint results remain the earlier release's evidence.

One old observation session expired; fresh reads used a new explicit session. The cleanup `_QUIT` input did not close AutoCAD despite successful dispatch. It was not replayed. A normal API Quit closed the sole independently verified saved fixture. This cleanup fallback is not a successful Cua workflow claim and is outside the benchmark.

## Repeat on another PC

Use an authorized disposable drawing, establish its baseline geometry/settings, and record actual AutoCAD version/language. Run the same intended small operations with full output verification after each. Compare complete task times, failures and geometry, including startup and verification; do not compare dispatch alone or remove checks to improve a score. Use a separate passive cursor/focus observation and inspect the actual canvas. Keep previous evidence and the previous package for comparison. Different applications, drawings, hardware, languages and models require local acceptance; 3D, plotting, arbitrary dialogs and general mail workflows remain unqualified.

[Machine-readable measurements](performance-results.json) retain the exact trial times and evidence filenames. The local audit folder holds raw calls, full readbacks, actual screenshots and the saved disposable DWG. They are test evidence, not a reusable production design.
