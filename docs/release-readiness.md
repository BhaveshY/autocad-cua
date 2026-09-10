# Release audit — 2026-09-10

**Decision: controlled-use preview. Do not market this as universal unattended production automation.**

## Changes

- A failed or uncertain input now blocks later writes on the same client. Reads remain available. This covers transport timeouts/exits, malformed responses, refusals and failed evidence writes. The client never replays input.
- Both AutoCAD prompt scan depths require the actual command editor. Matching text elsewhere is insufficient. The runner refreshes the prompt before each later answer instead of trusting the previous observation.
- Sequence failures retain their reason in the summary and block further writes on the shared client. Recovery requires inspecting the app and resolving the failed state.
- Boolean PID/HWND values are rejected. All input still requires explicit background delivery and exact positive integer targets.
- Three entry skills reduced from 601 to 478 whitespace-separated words. The README separates supported use, historical timings and unresolved limits. The driver's binary and input implementation are unchanged.

## Verification

29 automated tests cover prompt handling, refusal/timeout/exit, malformed responses, missing editors, state changes between answers, focus changes, unsafe targets, evidence failure and read-only property handling. These are local regression tests, not app compatibility certification.

Fresh German AutoCAD 2019 acceptance used a copy of the previous 120-entity office drawing. A freshly observed Rectangle ribbon Invoke established the first command; later rectangles used native command entry. Three cycles created a 5000 × 4000 mm rectangle at (30000, 20000) mm and performed full Undo. Independent native reads verified coordinates, closure, 20 m² area, unchanged original entities/settings and exact restoration after each Undo.

The full smoke took 48.37 s, including startup of the Cua client, initial verification and cleanup of that client; AutoCAD launch/discovery were separate. Individual create/check/Undo/check cycles took 14.09, 13.60 and 13.59 s. There is no matched old/new benchmark for this change. Extra pre-input checks are a reliability cost; shorter instructions are not proof of faster CAD execution.

No cursor/foreground/focus change was observed during the 48.37 s test; the earlier 20 s launch observation also recorded no focus change. Sampling cannot exclude shorter transitions. Window stacking was not independently measured. The owned drawing was closed without saving and AutoCAD quit normally. Earlier broad architectural and PDF tests remain historical evidence; they were not all repeated in this audit.

## Remaining release gates

| Gap | Evidence needed |
| --- | --- |
| Blank AutoCAD canvas captures | Reliable live capture on the intended graphics/display setup before pixel-based work can be accepted. A PDF preview does not establish this. |
| App self-activation | Target-specific workflows that preserve focus during startup, dialogs and input. The helper detects changes after they occur; it cannot guarantee prevention. |
| Cross-PC compatibility | Live acceptance on the AutoCAD versions/languages, DPI layouts and Windows hosts claimed as supported. Same-PC folder relocation is only a packaging check. |
| Production drawing workflows | Representative blocks/attributes, hatches, xrefs, layouts, publishing and large-file fixtures with independent geometric and visual checks. |
| State binding | The runner checks PID/HWND/title and prompt, but full-path identity is a separate native check. Same-name documents and close/reopen events require revalidation; checks are not an atomic lock against concurrent edits. |
| General apps | PowerPoint and Thunderbird startup failures remain unresolved. A field test is not a complete application workflow. |

The native reader covers bounded model-space properties, not every entity feature. `complete` means the requested entity scope was returned; it is not comprehensive CAD correctness. Curved polylines, non-default planes, blocks, layouts and solids need additional checks appropriate to their geometry.

Use the verified command route for supervised work with independent output checks. A new connection must never be used simply to evade a failure guard. The package does not claim a universal no-interruption guarantee or construction approval.

## Shared-desktop follow-up

The helper now checks live HWND ownership and rejects input to the process owning the user's foreground window, including another window in that same process. A focus change during preflight also stops dispatch. Failures before dispatch are logged as not uncertain; no input was sent. This remains a check, not an atomic desktop lock.

36 automated tests passed. A live Windows check rejected the foreground target before any input RPC, allowed subsequent readback, and admitted a different process to preflight. No GUI input was sent in that test. The preflight averaged 0.14 ms across 100 checks; this is overhead measurement, not an application task benchmark. The previous AutoCAD drawing tests were not repeated for this follow-up.

The practical route is a supported app API or browser control when it meets the request, otherwise verified background Cua input. Stop unsupported actions instead of taking over the desktop. [Cua's limits](https://cua.ai/docs/reference/cua-driver/limits) explicitly make background delivery dependent on available OS/app routes. Windows' [LockSetForegroundWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-locksetforegroundwindow) is callable by the foreground process and is not a universal lock available to this background helper. No focus-lock service or system policy change was added.

## Execution reliability follow-up

The Thunderbird run was not a plugin-only success: one worker switched to the older connected Cua driver after a shell denial; a duplicate worker launched Notepad to read instructions. No mailbox scroll was verified. These were orchestration failures, not evidence of plugin compatibility.

The helper now verifies the exact bundled executable path and hash before creating a process, writes a runtime receipt, and holds a Windows named mutex for the client lifetime. A second cooperating client is rejected immediately, including same-thread duplicates. A crashed owner releases its OS mutex. Failed startup releases ownership; existing evidence logs are not overwritten. Confirm worker descendants have exited before replacing them, even after a crash.

41 automated tests passed, including a real cross-process lock/crash test. A live pinned MCP session initialized, rejected a second client before process creation and admitted a fresh client after closing. No GUI input or mailbox reads occurred in this follow-up. The earlier drawing tests were not repeated.

The three entry skills now total 439 whitespace-separated words (previously 479). Their shared workflow is access check, single GUI owner, exact target, then effect verification. Conditional app details remain in references. The structure was informed by Matt Pocock's [writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md); it was not copied as a new dependency.

The installed C2 hook rejects Luna shell execution. The next revision below removes that shell dependency; it does not change mail policy. Do not read instructions through another application or replace the requested driver.

These guards apply to cooperating clients using this helper. They do not constrain unrelated MCP tools, guarantee model compliance, prevent app self-activation, or fix blank canvas capture. No service, daemon, dependency or additional skill was added.

## Native MCP transport repair

The plugin now registers its own stdio MCP server with 14 tools. Its launcher discovers Python and verifies the same pinned driver. Workers obtain instructions and operate one persistent guarded session directly through MCP, without shell access. Passive connections do not acquire the GUI lock. This removes the transport dependency that caused the earlier worker substitution; all host mail restrictions remain in force.

52 automated tests cover the existing guards plus MCP routing, instruction access, session ownership, launch validation, image forwarding and malformed-message recovery. The actual PowerShell launcher passed initialization, tool discovery, pinned identity, instruction retrieval and session lifecycle checks. These checks used no GUI input or mailbox reads. They do not prove Thunderbird scrolling, app self-activation prevention or a production-grade universal desktop solution. A new Codex thread must load the newly registered tools before a live plugin-only Thunderbird retest.

## Three-app live follow-up, 10 September 2026

AutoCAD 2019: Cua added an 8000 x 6000 mm, two-room annex to a disposable copy of the 120-entity office drawing. Eighteen new entities include walls, furniture, three native dimensions and four labels. Independent geometry checks preserved the original entities and verified Move/Undo, save and PDF output; the rendered sheet was inspected. TEXT's in-place editor required a corrected workflow in the command reference. One test used exact float equality; dimension acceptance now uses a 0.000001 mm tolerance. This was a drawing revision test, not a newly designed construction-ready building.

PowerPoint: Cua selected Ion for a three-slide fixture, changed the first slide to Title Slide, and saved it. Empty theme/layout popup trees were handled using fresh screenshots and background pixel input. App readback and all rendered slides confirmed the changes and preserved text. COM only opened/exported the fixture and read results; it did not apply the design changes. Broader visual editing remains unqualified.

The user authorized interruption for these tests. `start_session(allow_interruption:true)` now permits foreground input while retaining exact ownership and failure tracking; default sessions retain background-only behavior. Five additional regression tests pass (57 total). Thunderbird's separate C2 connector paths were repaired, but its native-host connection remains offline and its draft lane unconfigured. No mail was read or draft created. These results do not establish universal app support or a new speedup ratio.

## Native AutoCAD bridge acceptance

Four stable tools now complement Cua: inspect, prepare, execute and result. Task-specific AutoLISP runs through the installed AutoCAD COM interface. The bridge freezes the exact plan hash, binds process start/application HWND/document HWND/full path/disk hash, checks the supplied precondition inside AutoCAD, and records at-most-once dispatch. File identity does not capture unsaved edits; task-specific geometry preconditions remain necessary. Lisp is trusted code with local-user authority, not a sandbox.

Live AutoCAD 2019 acceptance generated a 41-entity six-room metric layout with walls, desks/chairs, text, columns and two native dimensions. Initial generation plus complete independent geometry comparison took 8.61 seconds (3.48 seconds native dispatch); fixture setup, debugging, annotation refinement and plotting are excluded. The final dimensions were checked for 18000/12000 mm measurements, scale 50 and text height 2.5. A separate ObjectDBX database opened the saved DWG copy and verified persisted objects and formatting. The final PDF was visually inspected. This is a mechanism test fixture, not a construction-ready design.

Duplicate execute did not add objects. A changed hash was refused, a false precondition made no geometry, a deliberately failing script exposed partial changes, and one Undo restored exact prior entities. Two early oversized-input attempts remained uncertain: Cua/state inspection proved idle or incomplete prompts and empty geometry before recovery. The bridge now stages short source strings and evaluates raw forms once, avoiding nested oversized Lisp string literals. Cua plot typing was ineffective in that host state; a native command-s plot succeeded after independent state inspection. No security setting or trust path was changed.

71 automated tests pass. Actual stdio MCP acceptance covers all four native tools and the existing guarded Cua session. A job timeout may leave ongoing/partial execution; result retrieval never replays it, and unresolved native jobs prevent another native dispatch until inspected and resolved. No generic script correctness, total transactional rollback, universal foreground isolation, or cross-version certification is claimed.
