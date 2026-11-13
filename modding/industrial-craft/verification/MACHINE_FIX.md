# Stage 0 calibration machine: texture, panel and timing fix

This is a stage-0 hotfix, **not completion of stage 1**. Copper/resources and
hostile-mob pathfinding are not included in this build.

## Changes

- Orion's default block renderer selects one of four 32-pixel variants from
  `blockData`; the old single 32x32 region did not provide those variants. The
  custom block now selects its own frame. A vertical three-frame sheet contains
  idle and two working frames, and animation changes only while that individual
  machine is running and has a valid recipe. Existing machines' old random bits
  no longer determine a bogus atlas sample.
- The atlas builder checks image bounds, collisions against the original XML,
  existing opaque pixels, and overlapping injected regions.
- Replaced the furnace panel artwork with a purpose-built machine panel showing
  input, output, progress, status and a control button. The panel still pauses
  the game, so the machine runs when it is closed.
- Flash timer callbacks delayed more than one second used to be clipped to
  100 ms, making a nominal five-second operation take much longer on slow
  systems. Elapsed active time is now accounted for; each machine has its own
  subsecond accumulator. Full seconds/progress use the unchanged ICW1 v1 save
  representation; a fraction under one second is not saved.

## Verification

In the Flash runtime using a test-only probe against the same dev SWF:

```text
IC_LOAD machines=3
IC_TIMING_START x=304 y=46 blockData=0
IC_TIMING_3S completed=0 progress=3 frame=1 elapsed=3004
IC_TIMING_PASS completed=1 progress=0 elapsed=5637
```

This establishes that the operation was unfinished at ~3 seconds and finished
by ~5.6 seconds in this run, not an exact measured completion timestamp. Test
SWFs inject AIR stubs and a probe; the playable dev SWF contains neither.
`machine-fixed-world.png` shows blocks rendered in-game; the world is at night.
`machine-fixed-panel.png` shows the new panel in-game. After the final changes,
`machine-fixed-reload-traces.txt` shows the existing three machines loaded and
both full and partial serialization tests; the saved machine's inventory and
progress matched the previous run. No AI changes or stage-1 content are claimed.

Build output `build/Orion.ic-dev.swf`: SHA-256
`7f837f3f8686db91d0f3a3d0c22fd1c063fff4a0983b59448a4e08f804e804f2`.
