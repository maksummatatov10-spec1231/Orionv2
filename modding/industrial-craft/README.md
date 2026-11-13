# Industrial Craft for Orion — stage 0

Technical foundation mod for Orion Sandbox Enhanced, built on the accepted texture pack v0.5.

- `src/industrialcraft/` — AS3 mod code (content registry, machine manager/state, block/item, panel UI, bootstrap).
- `data/` — content and atlas-region metadata.
- `assets/` — generated stage-0 pixel art used by the SWF builder.
- `scripts/` — ABC/SWF build chain (`compile_mod`, `build_assets`, `patch_hooks`, `build_swf`, `build_test`).
- `build/Orion.ic-dev.swf` — playable dev artifact (no AIR stubs, no test grant).
- `build/IndustrialCraft.abc`, `build/frame2-hooked.abc` — compiled mod bytecode and patched game frame.
- `verification/` — Stage0Probe harness source, hook/build manifests, runtime traces, screenshots and report.

See `verification/STAGE0_REPORT.md` for the acceptance result and build commands.
Stage 0 is a probe, not the final survival content; the roadmap lives in `docs/industrial-craft/`.
