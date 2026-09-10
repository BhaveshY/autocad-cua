# Validation and scope: 0.1.0

## General Windows optimization, 2026-09-09

The latest helper uses `mcp --direct --no-overlay`, keeping the same pinned binary, background restrictions and verification. Three interleaved runs per setting reduced the fully checked five-action Calculator task from **6.465 s to 0.776 s median**, including startup/cleanup. All six runs and the additional 39-action Calculator regression passed. **24 automated tests passed.** No cached-state shortcut or SDK runtime was added.

The three skill entrypoints fell from 987 to 601 words; all skill Markdown, including references, fell from 3007 to 2282 words. Exact targeting, prompt/value semantics, no replay and task verification remain.

This iteration recorded PowerPoint startup focus failures, including a correctly quoted normal launch. Minimized Office/CAD launches preserved focus but hid necessary GUI controls. A native PowerPoint API fallback saved a verified four-slide test presentation; the untouched AutoCAD fixture was independently checked and closed. No new AutoCAD drawing mutation or Thunderbird mail test is claimed for this iteration. The physical cursor remained unchanged in valid observations; monitoring had a documented gap. See [general-optimization.md](general-optimization.md) and [general-results.json](general-results.json) for all results and failures. Earlier sections are historical evidence.

## Performance iteration, 2026-09-09

The latest update retains the same pinned driver and input pacing. Three baseline runs, three runs with smaller sufficient prompt reads and one shared connection, and three final runs with faster read-only COM property access all passed the same full geometry and settings checks. Median four-operation task time fell from **32.0 s to 27.4 s to 13.3 s**, including verification. **23 automated tests passed.**

Nine additional AutoCAD stages passed for layers, polylines, Mirror/Move/Scale, Unicode text, arcs, dimensions and restored settings/Save. The complete original 15-entity fixture remained intact; five added entities were independently checked. Five reader checks passed for identity-only output, requested handles, explicit truncation and rejection of wrong HWND/path. Calculator's six cases and 39 actions passed again. PowerPoint and Thunderbird results below belong to the earlier expanded run, not a new run of this iteration.

The main AutoCAD screenshot was blank in this session. Capturing its exact named drawing child showed the actual geometry; subsequent zoomed and restored captures reflected the view changes. Full geometry/settings were unchanged after that check. The skill now documents this fallback. Across 139,039 passive observations over 24.8 minutes, no physical cursor, foreground or keyboard-focus change was observed. Sampling cannot exclude every shorter transient.

One idle observation session expired and was replaced for fresh reads. A cleanup `_QUIT` input returned dispatch success but did not close AutoCAD; no blind replay or foreground fallback followed. After binding the sole saved fixture, normal AutoCAD API Quit closed it. Drawing mutations and visual changes used Cua; geometry API access remained read-only. Cleanup failure is retained in the evidence and is outside the successful workflow timing.

See [performance.md](performance.md) and [performance-results.json](performance-results.json). Earlier results below are historical evidence; the current iteration does not certify arbitrary applications or other PCs/models.

## Expanded Windows app tests, 2026-09-09

The update adds one general **computer-use** skill and a sampled foreground/focus guard to the Python helpers. The pinned Cua binary is unchanged. No production documents or real mailboxes were used. This remains one-PC evidence, not universal app, second-PC or model certification.

| App / case | Result and independent evidence |
|---|---|
| AutoCAD 2019: rectangle and layers | Exact 4000 × 3000 mm rectangle; circle on new CUA-TEST layer |
| Copy, Move, Scale, Rotate | Centre/radius checked after each operation, including 90-degree rotation about a different point |
| Concave and mirrored outlines | Exact closed L-shape vertices, mirrored vertices and 8 m² areas; original retained |
| Unicode text and dimension | Exact “Büro 12 m²” at (10000, 4000) mm; new dimension measures 4000 mm |
| Erase, Undo, Redo, Save | Dimension removed/restored/removed, then restored for final file; 15 final entities, original eight entities unchanged; prior current layer and all inspected variables restored |
| AutoCAD visual result | Actual background window captures show the room/door/dimensions, circles, Unicode text and mirrored outlines. Captures followed Zoom Extents, Regenerate All and a zoom margin. This does not establish why earlier sessions were blank |
| PowerPoint | New Slide, title entry, Undo, Redo, another slide with Unicode title, Save; live document readback plus independent saved PPTX readback and actual screenshot. Three final slides |
| Calculator | Six cases / 39 verified button actions: decimals, negative subtraction, square root, backspace, percent, division-by-zero recovery |
| Thunderbird | **Failed background route:** first-run “Skip integration” UIA Invoke activated Thunderbird. Route stopped and isolated empty profile closed. No account, mailbox, message or send operation was tested |
| Thunderbird, alternate field route | Reopened the same empty profile without the modal. Fresh indexed ValuePattern input entered “CUA fixture 42”, then appended “ – Büro”. Both complete values were verified in new snapshots and actual screenshots; no foreground/focus change observed. This is field editing, not a mail-search test |

Across 63 prompt-checked AutoCAD answers, median input-plus-title/prompt checks were **439 ms** (range 378–1902 ms). These exclude process startup, model reasoning and independent geometry reads. Calculator median Invoke was **1237 ms**, excluding snapshot/readback. Thunderbird's two field writes took **23 ms and 17 ms**, excluding discovery/readback. These are measurements, not a speedup claim. Token usage was not measured.

The passive monitor observed no cursor movement. AutoCAD, PowerPoint and Calculator did not become foreground during their tests. Thunderbird did. Sampling cannot exclude shorter transitions or prove that every future action will preserve focus. The new guard stops subsequent helper input on observed foreground/focus changes; eight added fault-injection tests verify its behavior. It does not restore focus or prevent initial self-activation, and does not wrap direct MCP calls.

**16 automated control-logic tests passed**, alongside **25 saved-evidence assertions**. Actual app mutations used Cua only; COM was read-only. The PowerPoint seed was a one-slide file created before GUI testing. An initial Calculator assertion incorrectly expected a literal decimal dot where accessibility said “point”; it was corrected using observed formatting, then all six cases ran from Clear. AutoCAD COM reads rejected during an active command were deferred until idle. An identity-only baseline was unsuitable for geometry comparison; preservation was checked against the earlier full entity snapshot.

See [expanded-results.json](expanded-results.json) for measurements and fixture hashes. The saved DWG, PPTX, raw Cua logs, command specifications, focus trace and screenshots accompany the local test report. They are evidence fixtures, not production templates. Untested scope includes 3D, plotting/layout workflows, image-to-plan accuracy, arbitrary dialogs, other app versions/PCs and comparative Astra/GPT-5.6 performance.

## Initial release evidence

This is a portable local release, validated on Windows x64, German AutoCAD 2019 and Codex CLI 0.149.1. A different directory was used for relocation checks. This is not a second-PC test or a cross-version/model benchmark.

| Task | Guidance / implementation | Evidence level |
|---|---|---|
| Exact 2D geometry, wall offsets, openings, lines/arcs, dimensions | Native AutoCAD commands, one prompt answer at a time | Previous architectural fixture passed, with independent geometry readback |
| Repeated drafting and Undo/Save | Persistent Cua sequence runner, exact title checks | Plugin live test passed |
| Fresh-start keyboard focus failure | Observe refusal/no effect; invoke a freshly identified suitable ribbon command, then continue its actual prompt | Rectangle Execute invocation passed; no universal ribbon claim |
| Edit existing geometry and repeated elements | Bind current affected entities, verify a representative operation and subsequent changes | General workflow guidance; complex transformations need task-specific tests |
| Trace dimensioned sketches/plans | Inspect reference, calibrate scale, translate to drawing coordinates, verify topology/dimensions | Guidance only; image-to-plan accuracy is not benchmarked |
| Pixel picking, styling and visual QA | Fresh usable canvas screenshot and exact viewport required | Background canvas capture remained blank on this never-foregrounded host |
| 3D, layouts, plotting, complex dialogs, other languages/versions | Observe real prompts and validate actual outputs | Not qualified by this release |

## Live plugin checks

- The installer preflight found Codex, verified the bundled driver and made no changes in check-only mode.
- Doctor found a working Python interpreter and AutoCAD ProgID without launching CAD. After replacing recursive runtime-directory scanning, the process completed in about 0.87 seconds on this PC. This is a prerequisite check, not drawing acceptance.
- A new background AutoCAD process opened a separate copy of the existing eight-entity architectural fixture. The first typed rectangle command was ignored because the embedded Start browser held internal focus. The runner stopped without sending coordinates or replaying input.
- A fresh, same-session ribbon Invoke started the rectangle command. Two separately checked coordinate answers created an exact 5000 × 4000 mm rectangle. Read-only geometry inspection confirmed nine entities and exact vertices. Undo restored eight.
- A subsequent three-answer rectangle sequence took 1381.64 ms, including title rechecks and prompt observations, excluding startup, model reasoning and independent geometry readback. Individual answers took 435.15–481.16 ms. Undo varied; constant latency is not promised.
- The exact automation-ID/label/role Invoke selector was tested live, then the uncommitted command was cancelled and the idle prompt verified. Toggle-only controls are rejected by this helper.
- Full, identity-only and affected-handle geometry checks were exercised. An explicit string conversion fixed COM's handle-argument type mismatch. Counts distinguish total model-space entities from the returned subset.
- The prior room fixture remains intact. Its baseline includes 5000 × 4000 mm extents, 200 mm walls, 900 mm opening/door swing and dimensions. No production drawing was used.

Eight automated tests cover invalid sequences, exact title matching, no input on a wrong title, no replay after prompt timeout, rejection of foreground/desktop/stale-token input, pinned-driver hash mismatch, non-Latin prompts under a legacy Windows console encoding, and exact Invoke selectors. These are control-logic tests, not evaluations of Astra or GPT-5.6 task reasoning.

The original standalone skill and driver are retained for rollback. The plugin uses its own identical pinned driver; no global Cua replacement is required. Actual tokens were not measured. The two entrypoint skills remain short; command and visual details load only when relevant.

## Acceptance on a new PC

Check prerequisites, exact document identity and a readable command prompt. In an authorized disposable drawing, create one precisely specified entity; verify geometry; Undo and verify restoration. Check cursor/focus preservation and whether the actual canvas image is usable. Record the actual AutoCAD version/language. Stop at unsupported behavior; the skill does not grant permission to interrupt the user.

Dependency license texts/notices and per-package source download links are in `../licenses/dependencies/index.json`. Cua's unchanged third-party dependencies are not relicensed by this plugin. The source patch and build instructions are included separately.
