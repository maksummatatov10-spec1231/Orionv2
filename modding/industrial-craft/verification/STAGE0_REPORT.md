# Industrial Craft — Stage 0 runtime verification

Date: 2026-11-13 (sandbox clock). Base texture SWF: `modding/textures-v0.5/build/Orion.mod.swf`
(input sha256 `12ee72d5acf5cc9ef5f48dc4566636a5f2ed2faed2c64efd8fe08dc4ae55940a`).

## Result

Stage 0 acceptance is met in the real Flash runtime:

- one new item, block, placeable block item and recipe are registered;
- the block can be crafted, placed by the player, opened by right-click and broken;
- the machine ticks, consumes input and produces output;
- breaking the machine drops the block and its contents once;
- IC state survives the real Orion save/load path, including `EarthWorld` overrides;
- both full and partial world serializers contain a loadable IC section;
- after quitting to lobby and restarting the SWF, the saved machine state is restored and the panel opens.

The production/dev artifact is `build/Orion.ic-dev.swf`. It contains no AIR stubs and no test item grant.
The `setup`/`reload` SWFs are test harness builds produced by `scripts/build_test.py`.

## Build chain

```bash
python3 scripts/compile_mod.py       # src -> build/IndustrialCraft.abc (stale-output gate)
python3 scripts/build_assets.py      # stage-0 pixel art + data/atlas-regions.json
python3 scripts/patch_hooks.py       # frame2 -> build/frame2-hooked.abc, verification/hooks.json
python3 scripts/build_swf.py         # v0.5 base + atlases + hooks + mod ABC -> build/Orion.ic-dev.swf
python3 scripts/build_test.py --mode setup   # test-only harness -> build/Orion.ic-setup.swf
python3 scripts/build_test.py --mode reload  # test-only harness -> build/Orion.ic-reload.swf
```

Local toolchain used in this sandbox: ASC jar + JDK under `/tmp/orion-tools` / `/tmp/orionjdk`,
PIL under `/tmp/orionpy`, Flash Player 32 debugger under Xvfb `:99`. The scripts currently hard-code
those paths; they are environment assumptions, not game dependencies.

## Injected hooks

`verification/hooks.json` records five patches:

| Class | Method | Mode |
|---|---|---|
| `orion.worlds.World` | `saveAdditional_v1` | replace empty body |
| `orion.worlds.World` | `loadAdditional_v1` | replace empty body |
| `orion.worlds.earth.EarthWorld` | `saveAdditional_v1` | append after original five ints |
| `orion.worlds.earth.EarthWorld` | `loadAdditional_v1` | append after original load |
| `orion.GameProcess` | `initStatic` | append bootstrap install |

The EarthWorld hooks are required: the real Earth world overrides the base `World` additional
save/load methods. Runtime traces confirmed `IC_LOAD_LEGACY_WORLD` for an old save without the
`ICW1` magic, then real `IC_SAVE` / `IC_LOAD` once the section existed.

## IDs and content

- probe item: `1242`
- probe block: `239`
- probe block item: `495` (`239 + BEG_BLOCKS_ITEMS_ID`)
- recipe: 1 resin (`1032`) + 4 cobblestone (`325`) -> probe block item, crafting category `DECORATION`, first in the workbench list
- save magic: `ICW1` (`0x49435731`), version 1
- atlas regions: `item_1242` @ (16,760), `item_495` @ (64,760), `block_239` @ (972,1682)

ID audit before registration:

```text
freeItemsBefore=3661 freeBlocksBefore=23
blockRanges=77-77,130-131,136-136,139-140,157-157,240-255
```

`ContentRegistry` now validates that the target atlas regions exist before writing content.

## Setup run (test harness)

Observed traces:

```text
IC_TEST_STORAGE flushed
IC_LOAD machines=1
IC_TEST_ID_AUDIT freeItemsBefore=3661 freeBlocksBefore=23 blockRanges=77-77,130-131,136-136,139-140,157-157,240-255
IC_TEST_SETUP panel=302,48 break=305,48
IC_SAVE machines=3
IC_LOAD machines=3
IC_TEST_SAVE_ROUNDTRIP machines=3
IC_TEST_TICK completed=1 running=true output=1
IC_TEST_BREAK tile=0 machines=2 dropsBefore=6 dropsAfter=10
IC_TEST_EXPECTED x=302 y=48 progress=1 completed=1 input=1 output=1
IC_TEST_OPEN_WORKBENCH
```

Manual player actions after the harness opened the workbench:

1. Crafted the first recipe (1 resin + 4 cobblestone). Hotbar slot 0 became item `495`.
2. Placed the crafted block with left click at tile `296,48`; overlay changed to `block=239 machines=3`, hotbar count 5 -> 4.
3. Right-clicked the placed block: `IC_PANEL_OPEN 296,48`; the calibration machine panel opened.
4. Closed the panel, clicked the real floppy save button: `IC_SAVE machines=3`.
5. Confirmed `world.sol` on disk (324325 bytes) and `ic_stage0_expected.sol` (105 bytes).
6. Quit to lobby, stopped Flash, deployed `Orion.ic-reload.swf`, restarted.

Screenshots: `stage0-workbench.png`, `stage0-manual-panel.png`, `stage0-break.png`.

## Reload run

`stage0-reload-traces.txt` (verbatim filtered runtime log):

```text
IC_TEST_STORAGE flushed
IC_LOAD machines=3
IC_TEST_ID_AUDIT freeItemsBefore=3661 freeBlocksBefore=23 blockRanges=77-77,130-131,136-136,139-140,157-157,240-255
IC_TEST_RELOAD_PASS x=302 y=48 progress=1 completed=1 running=false input=1 output=1
IC_SAVE machines=3
IC_LOAD machines=3
IC_TEST_FULL_SAVE count=3
IC_SAVE machines=3
IC_LOAD machines=3
IC_TEST_PARTIAL_SAVE count=3
IC_PANEL_OPEN 302,48
```

The reload harness compared the live machine against the expected state written to the
`ic_stage0_expected` SharedObject during setup, then exercised `World.save` and
`World.savePartial` + `tilesDataPartial` and restored the IC manager from each serialized section.
Screenshot: `stage0-reload-panel.png` shows input resin 1, output module 1, progress 1/5, completed 1, paused.

## Fixes made during verification

- `MachineManager.getOrCreate` validates the tile block before creating state.
- `MachineManager.removed` drops contents through `world.dropTileEntityItem` instead of constructing `ItemEntity` directly; break test drops 6 -> 10 with no duplicate/missing items.
- `MachineState.load` validates input/output stacks (`loadedInput` / `loadedOutput`).
- `compile_mod.py` deletes stale ABC before compiling and fails on compiler errors.
- Test harness pre-requests `SharedObject.getLocal("world").flush(2 MiB)` before the menu, avoiding the Flash local-storage prompt during save.
- EarthWorld save/load hooks added; legacy saves without magic load via peek + rewind.

## Known limitations / non-IC noise

- Headless Flash logs `SoundManager/playRandomEffect` TypeError #1009 from mob step/ambient sounds. It is unrelated to IC; `mm.cfg` `SuppressDebuggerExceptionDialogs=1` prevents modal pauses.
- Panel labels "Сырьё" / "Выход" are partially overlapped by the furnace-style slots; cosmetic only.
- `world.sol` is not flushed instantly by Flash; the harness requests quota up front and the real save button was clicked twice during early checks.
- The setup harness grants test items and prepares two machines. That grant is not present in `Orion.ic-dev.swf`.
- Stage 0 is a technical probe, not the Stage 1+ survival content (copper ore, rubber, power network, macerator, electric furnace).
