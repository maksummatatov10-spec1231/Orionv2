# Tree sprites — textures v0.3

Retextured oak trees for Orion Sandbox Enhanced. Original atlas geometry, alpha silhouettes,
branch layout and apple placement are preserved; bark and leaf surfaces are replaced.

- `tree_trunk_26.png` — trunk / roots atlas strip (block_26, 131×197).
- `tree_branch_*.png` — branch / canopy sprites (blocks 165, 168–186).
  - Apple-bearing canopies: 168, 170 (and left/right branch variants).
  - Apple-free canopies: 171, 172 (and left/right branch variants).
- `leaves_block_28.png` — placeable leaves block strip.
- `wood_block_29.png` — wood block strip.

Both tree types from the reference screenshots are covered: the apple tree and the tall
apple-free tree. Canopies use large generated leaf surfaces cropped per-sprite to avoid a
repeating 32×32 tile pattern.
