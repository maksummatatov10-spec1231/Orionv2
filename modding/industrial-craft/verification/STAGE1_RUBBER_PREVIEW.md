# Stage 1 work in progress: rubber preview

This is **not the complete stage 1**. It adds one new material as a small
increment to the verified stage-0 machine build; copper ore and its migration,
copper bars/dust, plates, wiring, coil, circuit, casing and wrench remain to
be implemented and verified. Hostile mob pathfinding is not changed.

## Rubber

`ic:rubber` is a new item, ID 1243, distinct from existing tree resin ID 1032.
It has its own icon and is crafted at the workbench (Decorations tab): **2
resin → 1 rubber**. This is a preliminary recipe for the stage-1 preview; rubber
currently has no downstream use until the other components arrive. Neither the
resin ID nor its Russian name is changed.

The game's item registry and texture atlas are checked before installation.
`ItemStack` persists the rubber using its ID. A saved inventory containing it
requires this build or a later compatible build: back up saves before testing,
and do not load that inventory in an older build that lacks ID 1243.

## Verification

The test-only harness granted resin and called the normal `Crafting` API:
`IC_RUBBER_TEST_PASS id=1243 resinId=1032 consumed=2 output=1 restored=true`.
A real click on the workbench recipe then increased rubber from 1 to 2 and
reduced resin from 4 to 2, shown in `stage1-rubber-crafting.png`. The world
was saved using the in-game save button. After closing and restarting the SWF,
`IC_RUBBER_RELOAD_PASS count=2 resin=2` and `IC_LOAD machines=3` confirmed the
rubber inventory and existing machine states loaded; see
`stage1-rubber-traces.txt`. The playable dev build contains no test grant or AIR
stub; test SWFs do. This does not constitute a complete survival walkthrough.

Preview SWF SHA-256: `7200ff2c4ead5d567b83cfdaf6c80d8680ac2f63bf90239c2bb8c3ebe4aa4ac8`.
