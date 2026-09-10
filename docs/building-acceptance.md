# Architectural acceptance — 2026-09-09

Tested on this PC with German AutoCAD 2019 and the unchanged bundled Cua Driver 0.25.0-local.1. This is a controlled drafting study, not a construction-approved design or a universal unattended compatibility claim.

- Created a 120-entity drawing set: 18 × 12 m six-room office plan, 300/150 mm walls, six windows, six internal door swings, two exterior openings, furniture, room areas, nine dimensions, elevation and schematic section.
- Independently checked coordinates, radii, areas, layers, labels and dimensions. Additional checks covered a continuous 2200 mm corridor, 900 mm internal openings, 1200/1000 mm exterior openings, furniture/wall intersections and door clearances.
- Native PDF rendering exposed three labels crossing door swings and one cabinet intrusion. Cua Move with verified handles corrected them; unrelated geometry stayed unchanged. A1 portrait output at 1:50 was inspected and an 18 m feature measured approximately 359.96 mm on paper.
- Created a 3D wall shell, cut a doorway, added 250 mm floor/roof slabs and exported three solids through Wblock. Independent bounds/volumes and disk reload confirmed 170.64 m³ total. This does not validate a detailed 3D building model or its visual presentation.
- Six matched Circle/Copy/Rotate/full Undo runs passed with full geometry checks after each operation. Overlay on/off medians were 33.74/33.68 s: no meaningful speedup for this keyboard-driven test. These include client startup, checks and cleanup, and exclude app launch and model reasoning. Earlier 88% Calculator savings do not transfer to all apps.
- No foreground/focus/cursor changes were observed in 233,857 samples over 41.85 minutes. Background launch was separately guarded. Sampling is not proof against every shorter transition; stacking was not independently logged.

## Failures and retained lessons

Startup typing was ignored; a fresh Rectangle ribbon Invoke recovered. Typed Arc repeatedly stayed idle; Arc ribbon Invoke worked. Short Undo entered an unexpected Rectangle command; full `._UNDO` worked after cancellation and geometry inspection. A Box height prompt changed when a default existed. The harness stopped rather than sending remaining answers.

The named canvas capture remained blank, including after reload. A second Extents plot was cropped after temporary geometry was removed; explicit Window plotting fixed it. The original PDF plotter would launch a viewer, so a separate no-viewer configuration was prepared; the original was unchanged and the temporary installed copy was removed. AutoCAD's PDF contained a duplicate PageMode key warning from the independent parser; it rendered and passed page/scale checks.

The Start screen lacked the command palette after Close, so independent disk reload used AutoCAD's read-only API, not Cua input. The API needed a bounded readiness read after Open. Read-only window titles also differed. Both saved DWGs were independently verified before the owned app was closed normally.

Two exact-float harness comparisons were corrected to numerical tolerances; these were test errors, not wrong AutoCAD geometry. Visual collisions were drafting errors. The optional `read_drawing.ps1 -Detailed` adds bounds and text/dimension placement without expanding the default read. It passed a full 120-entity read and a selected-handle read; wrong-window/path refusal and truncation checks passed. All 24 existing automated tests passed.

The three skill entrypoints remain unchanged at 601 words. Detailed evidence and replay scripts are separate audit artifacts; no fixed room generator or machine-specific HWNDs were added to the plugin. Hatches, blocks with attributes, xrefs, multi-layout publishing, large external projects and other AutoCAD versions remain outside this acceptance.
