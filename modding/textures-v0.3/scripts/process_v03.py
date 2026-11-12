#!/usr/bin/env python3
"""v0.3 texture processing: natural stone, softer dirt, long tall grass, sand,
red-granite (visually matched to block_167), and retextured apple / tall trees.
Preserves original atlas geometry, alpha silhouettes, apple placement and icon frames.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
import json, hashlib, random, shutil

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / 'input'; GEN = ROOT / 'generated'; PROC = ROOT / 'processed'; PREV = ROOT / 'preview'
V02 = ROOT.parent / 'textures-v0.2/processed'
PROC.mkdir(exist_ok=True); PREV.mkdir(exist_ok=True)
for p in PROC.glob('*.png'):
    p.unlink()
OFFS = (0, 33, 66, 99); GUT = (32, 65, 98)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clamp(v): return max(0, min(255, int(round(v))))

def native(master, colors=28, sat=1.0, con=1.0, blur=0.0, crop=0):
    im = Image.open(master).convert('RGB')
    if crop: im = im.crop((crop, crop, im.width - crop, im.height - crop))
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    im = im.resize((32, 32), Image.Resampling.LANCZOS)
    im = ImageEnhance.Color(im).enhance(sat); im = ImageEnhance.Contrast(im).enhance(con)
    return im.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')

def bevel(im, strength=0.12, highlight=3):
    out = im.copy(); px = out.load()
    for y in range(32):
        for x in range(32):
            d = min(x, y, 31 - x, 31 - y); f = 1.0
            if d == 0: f = 1 - strength
            elif d == 1: f = 1 - strength * 0.45
            r, g, b = px[x, y]
            if x + y < 5: r += highlight; g += highlight; b += highlight
            if x > 26 and y > 26: r -= 3; g -= 3; b -= 3
            px[x, y] = (clamp(r * f), clamp(g * f), clamp(b * f))
    return out

def variant(base, i, kind, seed=0):
    im = base.copy()
    if kind in ('dirt', 'stone', 'cobble', 'sand', 'granite'):
        if i in (1, 3): im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if i in (2, 3): im = im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    else:
        if i % 2: im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    rnd = random.Random(3030 + i * 131 + seed); px = im.load()
    for _ in range(8):
        x = rnd.randrange(2, 30); y = rnd.randrange(2, 30); r, g, b = px[x, y]; d = rnd.choice((-6, -3, 3, 6))
        px[x, y] = (clamp(r + d), clamp(g + d), clamp(b + d))
    if i == 2: im = ImageEnhance.Brightness(im).enhance(1.02)
    if i == 3: im = ImageEnhance.Brightness(im).enhance(0.985)
    return im

def strip(name, base, kind, seed=0):
    orig = Image.open(IN / f'{name}.png').convert('RGBA'); out = orig.copy()
    for x in GUT:
        for y in range(32): out.putpixel((x, y), orig.getpixel((x, y)))
    for i, off in enumerate(OFFS): out.paste(variant(base, i, kind, seed).convert('RGBA'), (off, 0))
    p = PROC / f'{name}.png'; out.save(p); return p

def copy_v02(name):
    src = V02 / name
    if not src.exists(): raise FileNotFoundError(src)
    shutil.copyfile(src, PROC / name)

# Carry forward accepted v0.2 grass/cobble and their icons.
for n in ['grass_block_18.png', 'cobblestone_block_75.png', 'grass_icon_atlas_273.png', 'grass_icon_ui_273.png', 'cobblestone_icon_atlas_325.png', 'cobblestone_icon_ui_325.png']:
    copy_v02(n)

# Dirt: keep v0.2 detail but make large clumps less prominent.
dirt = Image.open(V02 / 'dirt_block_14.png').convert('RGBA')
soft = dirt.filter(ImageFilter.GaussianBlur(0.85))
dirt = Image.blend(dirt, soft, 0.38)
dirt = ImageEnhance.Contrast(dirt).enhance(0.82)
dirt = ImageEnhance.Color(dirt).enhance(0.92)
dirt = ImageEnhance.Brightness(dirt).enhance(1.025)
dirt.save(PROC / 'dirt_block_14.png')

stone_base = bevel(native(GEN / 'natural_stone_master_v3.png', 24, 0.90, 0.86, 0.35), 0.10, 2)
sand_base = bevel(native(GEN / 'sand_master_v2.png', 26, 0.98, 0.94, 0.25, crop=24), 0.10, 2)
granite_base = bevel(native(GEN / 'red_granite_master_v2.png', 18, 0.78, 0.70, 1.15), 0.10, 2)
strip('stone_block_4', stone_base, 'stone', 4)
strip('sand_block_16', sand_base, 'sand', 16)
# The user's "red granite" screenshot visually matches vanilla block_167 (bronze ore).
strip('red_granite_block_167', granite_base, 'granite', 167)

# Tall grass: long airy blades, not a compact bush.
def key_magenta(path):
    # Coverage-based downscale: keep blades solid/crisp at 32x32 instead of fading
    # thin blades into low-alpha LANCZOS ghosts. Magenta is keyed out at full res.
    im = Image.open(path).convert('RGB'); W, H = im.size; src = im.load()
    out = Image.new('RGBA', (32, 32), (0, 0, 0, 0)); px = out.load()
    for cy in range(32):
        for cx in range(32):
            rs = gs = bs = n = 0
            y0 = cy * H // 32; y1 = (cy + 1) * H // 32
            x0 = cx * W // 32; x1 = (cx + 1) * W // 32
            for y in range(y0, y1):
                for x in range(x0, x1):
                    r, g, b = src[x, y]
                    if r > 140 and b > 140 and g < 120 and r > g * 1.25 and b > g * 1.25: continue
                    if g >= b * 1.05 and g >= r * 0.70:
                        rs += r; gs += g; bs += b; n += 1
            cell = (y1 - y0) * (x1 - x0)
            if n >= cell * 0.04:
                px[cx, cy] = (rs // n, gs // n, bs // n, 255)
    return out

master = key_magenta(GEN / 'tallgrass_long_master_v3.png')
bbox = master.getbbox(); tile = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
if bbox:
    crop = master.crop(bbox); scale = min(32 / crop.width, 26 / crop.height, 1.0)
    nw = max(1, round(crop.width * scale)); nh = max(1, round(crop.height * scale))
    crop = crop.resize((nw, nh), Image.Resampling.NEAREST); tile.paste(crop, ((32 - nw) // 2, 32 - nh), crop)
orig = Image.open(IN / 'tallgrass_block_19.png').convert('RGBA'); out = orig.copy()
for x in GUT:
    for y in range(32): out.putpixel((x, y), (0, 0, 0, 0))
for i, off in enumerate(OFFS):
    v = tile.copy()
    if i % 2: v = v.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if i == 2: v = ImageEnhance.Brightness(v).enhance(1.04)
    if i == 3: v = ImageEnhance.Brightness(v).enhance(0.97)
    out.paste(v, (off, 0))
out.save(PROC / 'tallgrass_block_19.png')

# Tree retexturing: preserve exact alpha/silhouette/apple placement. Use large generated
# surfaces cropped per-sprite plus smooth lighting so canopies do not repeat a 32px tile.
bark = native(GEN / 'bark_master_v2.png', 28, 0.68, 0.92, 0.15)
leaf = native(GEN / 'leaf_canopy_master_v2.png', 30, 1.0, 0.96, 0.15)
bark_big = Image.open(GEN / 'bark_master_v2.png').convert('RGB')
leaf_big = Image.open(GEN / 'leaf_canopy_master_v2.png').convert('RGB')

def lum(r, g, b): return 0.299 * r + 0.587 * g + 0.114 * b

def surface_for(big, size, seed):
    rnd = random.Random(8100 + seed); w, h = size
    cw = min(big.width, max(96, w * 3)); ch = min(big.height, max(96, h * 3))
    x0 = rnd.randrange(0, big.width - cw + 1); y0 = rnd.randrange(0, big.height - ch + 1)
    return big.crop((x0, y0, x0 + cw, y0 + ch)).resize(size, Image.Resampling.LANCZOS).load()

def smooth_light(im, radius):
    gray = ImageOps.grayscale(im.convert('RGB')).filter(ImageFilter.GaussianBlur(radius))
    gp = gray.load(); ap = im.getchannel('A').load()
    vals = [gp[x, y] for y in range(im.height) for x in range(im.width) if ap[x, y] > 0]
    mean = sum(vals) / len(vals) if vals else 128.0
    return gp, max(1.0, mean)

def retexture_sprite(name, seed=0):
    im = Image.open(IN / f'{name}.png').convert('RGBA'); out = im.copy(); px = out.load()
    leaf_px = surface_for(leaf_big, im.size, seed)
    bark_px = surface_for(bark_big, im.size, seed + 101)
    light, mean = smooth_light(im, 5.0 if name.startswith('tree_branch') or name == 'leaves_block_28' else 2.5)
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a == 0: continue
            L = lum(r, g, b)
            is_apple = r > 110 and r > g * 1.35 and r > b * 1.35 and g < 130
            is_green = (g > r * 1.02 and g > b * 1.02) or (g >= r and g >= b and g > 35 and b < 160)
            f = max(0.62, min(1.22, 0.86 + 0.34 * (light[x, y] / mean - 1.0)))
            if is_apple:
                px[x, y] = (clamp(r * 1.06 + 6), clamp(g * 0.96), clamp(b * 0.96), a)
            elif is_green:
                sr, sg, sb = leaf_px[x, y]
                px[x, y] = (clamp(sr * f), clamp(sg * f), clamp(sb * f), a)
            else:
                sr, sg, sb = bark_px[x, y]
                nr, ng, nb = sr * f, sg * f, sb * f
                # pull bark toward a natural oak brown, away from the original orange tint
                nr = nr * 0.72 + 108 * 0.28; ng = ng * 0.72 + 80 * 0.28; nb = nb * 0.72 + 54 * 0.28
                if L > 150 and r > 160 and g > 110 and r > b * 1.15:
                    nr = nr * 0.35 + 208 * 0.65; ng = ng * 0.35 + 174 * 0.65; nb = nb * 0.35 + 128 * 0.65
                px[x, y] = (clamp(nr), clamp(ng), clamp(nb), a)
    out.save(PROC / f'{name}.png'); return out

retexture_sprite('tree_trunk_26', 26)
retexture_sprite('leaves_block_28', 28)
retexture_sprite('wood_block_29', 29)
for i in [165, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186]:
    retexture_sprite(f'tree_branch_{i}', i)

# Icons from updated blocks/surfaces. Preserve original silhouettes/frames.
def icon_from_tile(tile, atlas_name, ui_name):
    tile = tile.convert('RGBA')
    atlas_orig = Image.open(IN / f'{atlas_name}.png').convert('RGBA')
    atlas = tile.resize(atlas_orig.size, Image.Resampling.LANCZOS)
    if atlas_orig.getchannel('A').getextrema()[0] < 255: atlas.putalpha(atlas_orig.getchannel('A'))
    else: atlas = atlas.convert('RGB')
    atlas.save(PROC / f'{atlas_name}.png')
    ui_orig = Image.open(IN / f'{ui_name}.png').convert('RGBA'); alpha = ui_orig.getchannel('A'); bbox = alpha.getbbox()
    ui = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    if bbox:
        w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
        ui.paste(tile.resize((w, h), Image.Resampling.LANCZOS), (bbox[0], bbox[1]))
    ui.putalpha(alpha); ui.save(PROC / f'{ui_name}.png')

for block, atlas, ui in [('stone_block_4', 'stone_icon_atlas_259', 'stone_icon_ui_259'),
                         ('dirt_block_14', 'dirt_icon_atlas_269', 'dirt_icon_ui_269'),
                         ('sand_block_16', 'sand_icon_atlas_271', 'sand_icon_ui_271'),
                         ('red_granite_block_167', 'red_granite_icon_atlas_421', 'red_granite_icon_ui_421'),
                         ('leaves_block_28', 'leaves_icon_atlas_281', 'leaves_icon_ui_281'),
                         ('wood_block_29', 'wood_icon_atlas_282', 'wood_icon_ui_282')]:
    tile = Image.open(PROC / f'{block}.png').crop((0, 0, 32, 32)); icon_from_tile(tile, atlas, ui)

# Particles: preserve original alpha, recolor to updated materials.
def palette(im):
    q = im.convert('RGB').resize((16, 16)).quantize(colors=12, dither=Image.Dither.NONE).convert('RGB')
    return sorted(set(q.getdata()))

def particle(name, pal, seed):
    orig = Image.open(IN / f'{name}.png').convert('RGBA'); out = orig.copy(); px = out.load(); rnd = random.Random(seed)
    for y in range(orig.height):
        for x in range(orig.width):
            a = orig.getpixel((x, y))[3]
            if a == 0: px[x, y] = (0, 0, 0, 0); continue
            c = pal[rnd.randrange(len(pal))]
            if x + y < 4: c = tuple(clamp(v + 22) for v in c)
            if x > orig.width - 3 and y > orig.height - 3: c = tuple(clamp(v - 18) for v in c)
            px[x, y] = (*c, a)
    out.save(PROC / f'{name}.png')

particle('hit_dirt', palette(Image.open(PROC / 'dirt_block_14.png')), 14)
particle('hit_stone', palette(stone_base), 4)
particle('hit_sand', palette(sand_base), 16)
particle('hit_bronze', palette(granite_base), 167)
particle('hit_wood', palette(bark), 29)
particle('hit_leaves', palette(leaf), 28)
plant_pal = [c for c in palette(leaf) if c[1] > c[0] * 1.05 and c[1] > c[2] * 1.05] or [(0, 120, 24), (0, 170, 36), (24, 205, 52), (140, 225, 70)]
particle('hit_plant', plant_pal, 19)

# Filter build targets to the intended v0.3 scope.
targets = json.loads((ROOT / 'verification/targets.json').read_text())
keep_prefix = ('stone_block', 'dirt_block', 'grass_block', 'tallgrass_block', 'cobblestone_block', 'sand_block', 'red_granite_block',
               'tree_', 'leaves_block', 'wood_block', 'stone_icon', 'dirt_icon', 'grass_icon', 'cobblestone_icon', 'sand_icon',
               'red_granite_icon', 'leaves_icon', 'wood_icon', 'hit_dirt', 'hit_stone', 'hit_plant', 'hit_sand', 'hit_wood', 'hit_leaves', 'hit_bronze')
kept = [t for t in targets['targets'] if t['label'].startswith(keep_prefix)]
targets['targets'] = kept; targets['version'] = 'textures-v0.3'
(ROOT / 'verification/targets.json').write_text(json.dumps(targets, indent=2))
for t in kept:
    if not (PROC / f"{t['label']}.png").exists(): raise FileNotFoundError(t['label'])

# Previews
def load_preview(name):
    im = Image.open(PROC / f'{name}.png').convert('RGBA')
    if name == 'tallgrass_block_19':
        bg = Image.new('RGBA', im.size, (40, 32, 20, 255)); bg.alpha_composite(im); im = bg
    return im.convert('RGB')

rows = [('STONE', 'stone_block_4'), ('DIRT', 'dirt_block_14'), ('SAND', 'sand_block_16'), ('RED GRANITE', 'red_granite_block_167'), ('TALL GRASS', 'tallgrass_block_19')]
scale = 6; w = 131 * scale; h = 32 * scale; gap = 24; label = 22
sheet = Image.new('RGB', (w * 3 + gap * 2, (h + label) * len(rows) + gap * (len(rows) - 1) + 20), (18, 20, 24)); d = ImageDraw.Draw(sheet)
for row, (title, name) in enumerate(rows):
    y = row * (h + label + gap) + label + 10
    old = Image.open(IN / f'{name}.png').convert('RGBA')
    if name == 'tallgrass_block_19':
        bg = Image.new('RGBA', old.size, (40, 32, 20, 255)); bg.alpha_composite(old); old = bg
    old = old.convert('RGB')
    v02p = V02 / f'{name}.png'
    mid = Image.open(v02p).convert('RGBA') if v02p.exists() else old.convert('RGBA')
    if name == 'tallgrass_block_19':
        bg = Image.new('RGBA', mid.size, (40, 32, 20, 255)); bg.alpha_composite(mid); mid = bg
    mid = mid.convert('RGB'); new = load_preview(name)
    for col, im in enumerate([old, mid, new]):
        x = col * (w + gap); d.text((x, y - 18), f'{title} ' + ['ORIGINAL', 'v0.2', 'v0.3'][col], fill=(220, 220, 220) if col < 2 else (140, 255, 170)); sheet.paste(im.resize((w, h), Image.Resampling.NEAREST), (x, y))
sheet.save(PREV / 'terrain-before-after-v03.png')

for n in ['tree_trunk_26', 'tree_branch_168', 'tree_branch_171']:
    im = Image.open(PROC / f'{n}.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (135, 180, 220, 255)); bg.alpha_composite(im)
    bg.convert('RGB').resize((im.width * 3, im.height * 3), Image.Resampling.NEAREST).save(PREV / f'{n}-v03.png')

# Tall grass correctly stacked above a grass block (not overlapping it).
stack = Image.new('RGBA', (131, 64), (0, 0, 0, 0))
stack.alpha_composite(Image.open(PROC / 'grass_block_18.png').convert('RGBA'), (0, 32))
stack.alpha_composite(Image.open(PROC / 'tallgrass_block_19.png').convert('RGBA'), (0, 0))
bg = Image.new('RGBA', stack.size, (135, 180, 220, 255)); bg.alpha_composite(stack)
bg.convert('RGB').resize((131 * 8, 64 * 8), Image.Resampling.NEAREST).save(PREV / 'tallgrass-on-grass-v03.png')

manifest = {'version': 'textures-v0.3', 'kept_targets': len(kept), 'files': {p.name: {'sha256': sha(p), 'size': list(Image.open(p).size)} for p in PROC.glob('*.png')}}
(ROOT / 'verification/processed.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
