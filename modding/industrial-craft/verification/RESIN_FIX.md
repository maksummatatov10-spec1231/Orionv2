# IC 0.1.1-stage0 — resin drop and Russian name fix

User report: resin did not drop from trees, and the Russian item name was "Резина"
(rubber) even though the material is tree resin.

## Root causes

1. `orion.worlds.items.blocks.TreeItem.removeItem` always spawned one wood item,
   then computed an extra drop count into a local variable but never spawned it.
   The `TreeBlock.getDroppedItem` resin branch was therefore unreachable in normal
   tree removal.
2. The original Russian dictionary (SWF BinaryData char `1481`) contained
   `"item_resin": "Резина"`. English and several other dictionaries already used
   the correct resin wording.

## Fix

- Version bumped to `0.1.1-stage0`; IC save format remains `ICW1` version 1.
- Added a sixth ABC hook: append `IndustrialCraftBootstrap.dropTreeResin` after
  `TreeItem.removeItem`, forwarding registers `(x, y, data, drop)`.
- The helper spawns exactly one existing resin item (`Item.RESIN`, ID `1032`) only
  when `drop == true`, `data > 11`, and `TreeItem.isTrunk(data)`.
  - first hit / branch-root transition (`data <= 11`): no resin;
  - branches/leaves: no resin;
  - silent removal (`drop == false`): no resin;
  - final trunk removal: one resin per destroyed trunk segment.
- Felling a base trunk can cascade through the whole trunk in Orion. Each destroyed
  trunk segment drops its own resin; the test observed 18 resin from one tall tree.
  This is intentionally generous for stage 0; survival balance belongs to stage 1.
- Patched only two Russian JSON string values in char `1481`:
  - `item_resin`: `Резина` -> `Смола`
  - `item_desc_resin`: now states it is tree resin, drops from trunk blocks, is used
    for the faint torch and calibration machine, and is not rubber.
- The builder validates the expected source strings, replaces only those JSON
  values, parses the result, and proves no other dictionary keys changed.
- Rubber is not added yet. Future rubber must be a separate item/ID/icon, not a
  rename of this amber tree resin.

## Runtime verification

Test build: `scripts/build_test.py --mode resin` (test-only; no item grant in the
playable dev SWF). Russian was selected through the real language menu.

`resin-fix-traces.txt` contains the filtered runtime log. Key lines:

```text
IC_RESIN_READY id=1032 name=Смола trunkDrop=1
IC_LOAD machines=3
IC_TEST_RESIN_NAME_PASS id=1032 name=Смола inventory=4
IC_TEST_TRUNK_PASS x=306 y=48 data=11 finalData=15 firstHitResin=0 resin=18 tileAfter=0
IC_TEST_RESIN_GUARDS_PASS dropFalseBranchFirstHit=0
IC_SAVE machines=3
```

`resin-tooltip.png` shows the real inventory tooltip titled **Смола** with the new
description. The old stage-0 machine save loaded successfully after the patch, and
the real floppy save still emitted `IC_SAVE machines=3`.

Reload regression on the final hooks (`--mode reload` rebuilt from the final dev
SWF): `IC_TEST_RELOAD_PASS x=302 y=48 progress=1 completed=1 running=false
input=1 output=1`, followed by `IC_LOAD machines=3` / `IC_SAVE machines=3`.

## Playable artifact

`modding/industrial-craft/build/Orion.ic-dev.swf`

sha256: `6ead6a180650440d74d049d72913356015ae3f15b1e0bd9a36fc32c5f0cb9f0a`
