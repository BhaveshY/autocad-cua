# General Windows optimization and SDK investigation

The retained change is small: bundled helper processes start Cua with **`mcp --direct --no-overlay`**. This removes decorative cursor travel, while keeping exact-window background delivery, input pacing, fresh snapshots, post-action verification and foreground/focus monitoring. `Client(..., show_overlay=True)` restores the optional indicator. No global Cua configuration or pinned binary changed, and no SDK dependency was added.

## Controlled comparison

The same Calculator task performed Clear, 1, +, 2, =, with a fresh snapshot before and display verification after **every** action. Three runs of each configuration were interleaved. Both used the same patched executable and helper. Timing includes process/session startup, all 10 reads, five inputs, evidence logging and cleanup; it excludes Calculator launch and model reasoning.

| Configuration | Three task times | Median |
|---|---|---|
| Decorative overlay enabled | 6.525 s, 6.448 s, 6.465 s | 6.465 s |
| Overlay disabled | 0.776 s, 0.782 s, 0.773 s | 0.776 s |

That is **88.0% less time** (8.3 times the completion rate) for this task on this PC. All six runs passed. The broader Calculator regression also passed six cases and 39 verified inputs: decimals, negatives, square root, backspace, percentages and division-by-zero recovery. Its median input dispatch was 5.4 ms; that smaller figure excludes observations and is not the task time.

## What the SDK link revealed

The official [in-process guide](https://cua.ai/docs/how-to-guides/driver/use-sdk-in-process) prompted an isolated test of the hash-verified Windows Python 0.25.0 wheel. No global package was installed. Three verified SDK Calculator tasks took 0.799 s median, versus 6.949 s for the same release's persistent MCP with its default overlay. These timings exclude startup; they are a separate comparison from the table above.

The large difference was not established as IPC overhead. The Windows source's `overlay_glide_to` waits for decorative cursor travel when enabled and returns immediately when disabled. Testing the supported MCP `--no-overlay` flag recovered the large gain while preserving the existing tested driver and avoiding another runtime. SDK and CLI Calculator images, trees and window bounds agreed here. The primary display was at 1x scaling; an [open upstream issue](https://github.com/trycua/cua/issues/3449) concerns the in-process TypeScript host at higher Windows scaling. This iteration does not resolve that issue or certify the SDK across other PCs.

## App results and failures retained

- **Calculator:** 12 small workflows across the SDK and overlay comparisons passed, plus the 39-input regression. The user cursor did not move in valid observations.
- **PowerPoint:** my initial launch split a spaced filename because the driver joins `additional_arguments` as raw text. The resulting error dialog took focus. The owned empty process was terminated during cleanup; that caused a restart warning, which was resolved with the observed No button and a normal app exit. Windows quoting with `[subprocess.list2cmdline(argv)]` fixed the file-open error. A correctly quoted normal launch still briefly activated PowerPoint, so it remains a failed no-interruption route.
- **PowerPoint minimized:** `start_minimized:true` preserved foreground/focus, but the hidden Ribbon could not be targeted through Cua. Native PowerPoint COM then added and saved one test slide while minimized. Independent PPTX inspection verified four slides, retained original slide text, and the exact new text/font. This was an **API fallback**, not a Cua GUI pass.
- **AutoCAD minimized:** launch preserved foreground/focus, but the command palette was unavailable. No drawing commands were sent. Independent readback confirmed the copied 20-entity drawing and inspected settings were intact; it was closed normally. Prior normal-window geometry and image tests remain documented separately.
- **Thunderbird:** no new mail test. Prior empty-profile ValuePattern success and first-run Invoke self-activation limits remain in the guidance.

Passive traces observed no physical cursor movement. They did record PowerPoint launch focus changes. The first monitor stopped when no foreground window existed briefly during cleanup; a replacement continued through transient observation errors. This is not an uninterrupted whole-turn guarantee. Bundled per-input guards remained active. No manual focus restoration, real-cursor input or automatic foreground delivery was used.

## Smaller instructions

| Skill | Before | After |
|---|---:|---:|
| computer-use | 362 words | 220 words |
| work | 400 words | 243 words |
| setup | 225 words | 138 words |

The three entrypoints total **601 words**, down from 987 (39.1% less). Including all skill references, Markdown fell from 3007 to 2282 words. Repeated history and generic reminders were removed; exact targeting, background restrictions, no replay, typed-field semantics, app-specific failures and verification remain. No new control abstraction or cached-state shortcut was added.

**24 automated tests passed.** These are control-logic checks; comparative model performance and actual token usage were not measured. The package retains its original binary and rollback archives. Results are local evidence, not support certification for every application, drawing or Windows version.

[Exact measurements](general-results.json) accompany this report. The local audit folder also holds raw calls, snapshots, focus traces and the saved PowerPoint fixture.
