# AutoCAD Cua for Codex

**Controlled-use preview, not a universal unattended production release.** Three short skills choose between native AutoCAD batches, Cua visual control, setup and general Windows app recovery. Four stable native tools inspect a drawing, prepare task-specific AutoLISP, execute its exact hash once and retrieve results. New tasks can use new scripts without adding a tool per task. Exact targeting, shared ownership and independent verification remain essential.

## Install

1. Extract the complete archive and open **Install.cmd**. It uses the installed Codex CLI, preserves other plugins, and refuses to overwrite an existing source installation. No administrator service or VM is required.
2. Start a **new Codex thread** and ask: **“Check AutoCAD Cua setup on this PC.”**
3. Open the intended drawing normally, then ask: **“Use AutoCAD Cua to draw this dimensioned plan in the background and verify it.”**

For other apps, ask for the **computer-use** skill. The plugin exposes 18 MCP tools, including four native AutoCAD tools and a guarded Cua session. Workers need no shell tool to use them. Requirements: Windows x64, Codex with plugin support, Python 3.10+ (located automatically; Codex's runtime works), and the target app. Native AutoCAD uses Windows PowerShell 5.1 and COM; no extra add-in, service or SDK installation. Python and apps are not bundled. `Install.ps1 -CheckOnly` checks prerequisites, not app control.

## Verified scope and limits

German AutoCAD 2019 tests produced a 120-entity office plan, elevation, section, A1 PDF at 1:50, and a separate three-solid massing model. Independent checks covered geometry, annotations, save/reload and repeated edits/Undo. Command failures and visual collisions required recovery. The live canvas remained blank; the PDF supplied final visual evidence. See [building acceptance](docs/building-acceptance.md).

Calculator background arithmetic passed. Earlier PowerPoint GUI workflows passed, but a later normal launch self-activated; a minimized native API route worked. Thunderbird field editing passed in an empty profile, but a startup button self-activated. No general mailbox workflow is certified. See [app results](docs/general-optimization.md).

By default the helper rejects input to your foreground app, verifies live window ownership, and observes focus changes. It cannot prevent an app's first self-activation or detect every short transition. Explicit user permission can enable `allow_interruption` for a session; exact targets, failure tracking and evidence still apply. This plugin's MCP tools use those guards; unrelated Cua connections do not. Host restrictions on MCP tools still apply. Other AutoCAD versions, languages, LT, mixed-DPI setups, complex dialogs and large projects remain unqualified. [Release audit](docs/release-readiness.md) records current gaps and checks.

## Performance

The native bridge created a 41-entity six-room test layout and independently checked geometry in 8.61 seconds on this PC; native dispatch took 3.48 seconds of that. Setup, debugging, later annotation refinement and plotting are excluded. Repeat-call prevention, changed-hash refusal, false preconditions, partial-error reporting, exact Undo restoration and saving passed in AutoCAD 2019. This is not a matched Cua speed comparison. Generated Lisp is trusted, unsandboxed code; timeouts may leave uncertain or partial changes. The [native workflow](skills/work/references/native.md) covers diagnosis and recovery.

Disabling decorative animation reduced a verified five-action Calculator task from 6.47 to 0.78 seconds on this PC. The matched AutoCAD edit/Undo benchmark stayed effectively unchanged at 33.74 versus 33.68 seconds. These are different workloads, not universal speed guarantees. The current runner adds fresh prompt checks; earlier timings are historical. No comparative model or token benchmark was performed.

## Package and data

The package includes relative-path helpers, tests, source patch, dependency notices and a hash-pinned downstream Cua Driver 0.25.0 executable. It is not an official Cua or Autodesk release. See [runtime identity](runtime.json) and [rebuild instructions](source/README.md).

Helpers run locally, but observed content and screenshots can enter the Codex conversation. Local evidence may contain drawing information. The plugin adds no listener, cloud service or separate API key.

Uninstall through Codex's Plugins UI. Original Cua, other plugins and DWGs are not replaced; the source folder and marketplace listing may remain. Updates should be reviewed in Codex before reinstalling.
