#!/usr/bin/env python3
"""v0.5: orange oak trees + all ores rebuilt on the accepted stone texture.
Preserves atlas geometry, alpha masks, animation frame counts and icon frames.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
import json, hashlib, random, shutil, math, colorsys

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / 'input'; GEN = ROOT.parent / 'textures-v0.4/generated'; PROC = ROOT / 'processed'; PREV = ROOT / 'preview'
V03 = ROOT.parent / 'textures-v0.3/processed'
V03GEN = ROOT.parent / 'textures-v0.3/generated'
PROC.mkdir(exist_ok=True); PREV.mkdir(exist_ok=True)
for p in PROC.glob('*.png'): p.unlink()
OFFS = (0, 33, 66, 99); GUT = (32, 65, 98)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clamp(v): return max(0, min(255, int(round(v))))
def lum(r, g, b): return 0.299 * r + 0.587 * g + 0.114 * b

def native(master, colors=28, sat=1.0, con=1.0, blur=0.0, crop=0):
    im = Image.open(master).convert('RGB')
    if crop: im = im.crop((crop, crop, im.width - crop, im.height - crop))
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    im = im.resize((32, 32), Image.Resampling.LANCZOS)
    im = ImageEnhance.Color(im).enhance(sat); im = ImageEnhance.Contrast(im).enhance(con)
    return im.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')

def bevel(im, strength=0.10, highlight=2):
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

def variant(base, i, seed=0):
    im = base.copy()
    if i in (1, 3): im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if i in (2, 3): im = im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    rnd = random.Random(4040 + i * 131 + seed); px = im.load()
    for _ in range(8):
        x = rnd.randrange(2, 30); y = rnd.randrange(2, 30); r, g, b = px[x, y]; d = rnd.choice((-5, -3, 3, 5))
        px[x, y] = (clamp(r + d), clamp(g + d), clamp(b + d))
    if i == 2: im = ImageEnhance.Brightness(im).enhance(1.02)
    if i == 3: im = ImageEnhance.Brightness(im).enhance(0.985)
    return im

def strip(name, base, seed=0):
    orig = Image.open(IN / f'{name}.png').convert('RGBA'); out = orig.copy()
    for i, off in enumerate(OFFS): out.paste(variant(base, i, seed).convert('RGBA'), (off, 0))
    # rebuild padding gutters from the NEW cell edges; otherwise original-color gutters bleed as seams
    px = out.load()
    for gx in GUT:
        if gx >= out.width: continue
        for y in range(out.height):
            l = px[gx - 1, y] if gx - 1 >= 0 else None
            r = px[gx + 1, y] if gx + 1 < out.width else None
            if l and r and l[3] and r[3]:
                px[gx, y] = tuple((l[k] + r[k]) // 2 for k in range(3)) + (max(l[3], r[3]),)
            elif l and l[3]: px[gx, y] = l
            elif r and r[3]: px[gx, y] = r
    p = PROC / f'{name}.png'; out.save(p); return p

def copy_v03(name):
    src = V03 / name
    if not src.exists(): raise FileNotFoundError(src)
    shutil.copyfile(src, PROC / name)

# Carry accepted v0.3 assets (bronze ore is intentionally NOT carried: it stays original).
carry = ['stone_block_4.png', 'sand_block_16.png', 'grass_block_18.png', 'cobblestone_block_75.png',
         'stone_icon_atlas_259.png', 'stone_icon_ui_259.png', 'sand_icon_atlas_271.png', 'sand_icon_ui_271.png',
         'grass_icon_atlas_273.png', 'grass_icon_ui_273.png', 'cobblestone_icon_atlas_325.png', 'cobblestone_icon_ui_325.png',
         'dirt_icon_atlas_269.png', 'dirt_icon_ui_269.png',
         'hit_dirt.png', 'hit_stone.png', 'hit_sand.png', 'hit_plant.png']
for n in carry: copy_v03(n)

# Dirt: slightly lighter than v0.3, keep softened clumps.
dirt = Image.open(V03 / 'dirt_block_14.png').convert('RGBA')
dirt = ImageEnhance.Brightness(dirt).enhance(1.13)
dirt = ImageEnhance.Contrast(dirt).enhance(0.97)
dirt.save(PROC / 'dirt_block_14.png')
# refresh dirt icons from lighter tile
tile = dirt.crop((0, 0, 32, 32))
for atlas, ui in [('dirt_icon_atlas_269', 'dirt_icon_ui_269')]:
    ao = Image.open(IN / f'{atlas}.png').convert('RGBA'); tile.resize(ao.size, Image.Resampling.LANCZOS).save(PROC / f'{atlas}.png')
    uo = Image.open(IN / f'{ui}.png').convert('RGBA'); alpha = uo.getchannel('A'); bbox = alpha.getbbox()
    ui_im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    if bbox: ui_im.paste(tile.resize((bbox[2]-bbox[0], bbox[3]-bbox[1]), Image.Resampling.LANCZOS), (bbox[0], bbox[1]))
    ui_im.putalpha(alpha); ui_im.save(PROC / f'{ui}.png')

# Tall grass: long (23-30 px), sparse individual blades; no dense bush / neon tips.
def tallgrass_tile(seed):
    rnd = random.Random(7100 + seed)
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0)); px = im.load()
    bases = [3.5, 8.0, 13.0, 18.0, 23.0, 28.0]
    heights = [30, 25, 28, 23, 29, 26]
    for bi, (bx, h) in enumerate(zip(bases, heights)):
        bx += rnd.uniform(-1.0, 1.0); h += rnd.randint(-1, 1)
        lean = rnd.uniform(-3.5, 3.5); curl = rnd.uniform(-1.2, 1.2)
        dry = rnd.random() < 0.22
        for step in range(h + 1):
            t = step / h
            x = bx + lean * (t ** 1.35) + math.sin(t * math.pi) * curl
            y = 31 - step
            xi = int(round(x))
            if not (0 <= xi < 32 and 0 <= y < 32): continue
            # natural green gradient, darker at the root; a few dry tips
            r = int(30 + 58 * t); g = int(78 + 62 * t); b = int(30 + 26 * t)
            if dry and t > 0.72:
                r = int(r * 0.45 + 126 * 0.55); g = int(g * 0.45 + 118 * 0.55); b = int(b * 0.45 + 62 * 0.55)
            a = 255 if step < h - 1 else 210
            px[xi, y] = (clamp(r), clamp(g), clamp(b), a)
            if step < 3 and xi + 1 < 32: px[xi + 1, y] = (clamp(r * 0.82), clamp(g * 0.82), clamp(b * 0.82), 230)
        # tiny seed head on one blade, not a cluster
        if bi == seed % 6:
            tx = int(round(bx + lean)); ty = 31 - h
            if 0 <= tx < 31 and 0 <= ty < 31:
                px[tx, ty] = (132, 124, 70, 235); px[tx + 1, ty] = (118, 112, 62, 220)
    return im
orig = Image.open(IN / 'tallgrass_block_19.png').convert('RGBA'); out = orig.copy()
for x in GUT:
    for y in range(32): out.putpixel((x, y), (0, 0, 0, 0))
for i, off in enumerate(OFFS):
    v = tallgrass_tile(i)
    if i % 2: v = v.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if i == 2: v = ImageEnhance.Brightness(v).enhance(1.03)
    if i == 3: v = ImageEnhance.Brightness(v).enhance(0.97)
    out.paste(v, (off, 0))
out.save(PROC / 'tallgrass_block_19.png')
# soften neon fringe on the grass block itself (keep accepted soil/clumps)
gp = PROC / 'grass_block_18.png'; gim = Image.open(gp).convert('RGBA'); gpx = gim.load()
for y in range(7):
    for x in range(gim.width):
        r, g, b, a = gpx[x, y]
        if a and g > 100 and g > r * 1.25 and g > b * 1.25:
            gpx[x, y] = (clamp(r * 0.35 + 64 * 0.65), clamp(g * 0.35 + 122 * 0.65), clamp(b * 0.35 + 48 * 0.65), a)
gim.save(gp)

# Materials
stone_base = native(V03GEN / 'natural_stone_master_v3.png', 24, 0.90, 0.86, 0.35)
clay_base = bevel(native(GEN / 'red_clay_master.png', 24, 0.92, 0.90, 0.35, crop=16), 0.10, 2)
planks_base = native(GEN / 'oak_planks_master.png', 28, 0.95, 0.95, 0.15)
furniture_big = Image.open(GEN / 'furniture_wood_master.png').convert('RGB')
planks_big = Image.open(GEN / 'oak_planks_master.png').convert('RGB')
cloth_big = Image.open(GEN / 'bed_cloth_master.png').convert('RGB')
armor_big = Image.open(GEN / 'wooden_armor_master.png').convert('RGB')
stone_big = Image.open(V03GEN / 'natural_stone_master_v3.png').convert('RGB')
bark_big = Image.open(V03GEN / 'bark_master_v2.png').convert('RGB')
# desaturate bark strongly; make a seamless 32px trunk tile
bark_tile = native(V03GEN / 'bark_master_v2.png', 26, 0.55, 0.90, 0.25)
# vertical seamless blend: blend top/bottom 5 rows toward their opposite edge
bp = bark_tile.load()
for y in range(5):
    t = (5 - y) / 5 * 0.5
    for x in range(32):
        r1, g1, b1 = bp[x, y]; r2, g2, b2 = bp[x, 31 - y]
        bp[x, y] = (clamp(r1 * (1 - t) + r2 * t), clamp(g1 * (1 - t) + g2 * t), clamp(b1 * (1 - t) + b2 * t))
        bp[x, 31 - y] = (clamp(r2 * (1 - t) + r1 * t), clamp(g2 * (1 - t) + g1 * t), clamp(b2 * (1 - t) + b1 * t))
leaf_big = Image.open(V03GEN / 'leaf_canopy_master_v2.png').convert('RGB')
leaf_big = ImageEnhance.Color(leaf_big).enhance(0.78)
leaf_big = ImageEnhance.Brightness(leaf_big).enhance(0.92)

strip('clay_block_17', clay_base, 17)
strip('wood_block_29', planks_base, 29)
strip('wood_planks_block_114', planks_base, 114)
# Background walls: dedicated flat backdrop materials, NOT darkened foreground blocks.
# Low relief / low contrast so placed walls read as background, with real masonry / board structure.
def wall_stone_tile(seed=0):
    rnd = random.Random(8200 + seed); im = Image.new('RGB', (32, 32)); px = im.load()
    shades = [(78, 80, 84), (72, 74, 78), (84, 86, 89), (68, 70, 74)]
    for y in range(32):
        row = y // 8; off = 8 if row % 2 else 0; by = y % 8
        for x in range(32):
            xx = (x + off) % 32; bx = xx % 16
            if by == 0 or bx == 0:
                c = (46, 48, 52)
            else:
                bid = (xx // 16 + row * 2) % 4; base = shades[bid]
                n = rnd.randint(-3, 3); c = tuple(clamp(v + n) for v in base)
                if by == 1 or bx == 1: c = tuple(clamp(v + 9) for v in c)
                if by == 7 or bx == 15: c = tuple(clamp(v - 10) for v in c)
            px[x, y] = c
    return im

def wall_dirt_tile(seed=0):
    rnd = random.Random(8300 + seed); im = Image.new('RGB', (32, 32)); px = im.load()
    for y in range(32):
        band = -7 if y % 8 == 0 else (-3 if y % 8 == 1 else 0)
        for x in range(32):
            n = rnd.randint(-4, 4)
            px[x, y] = (clamp(88 + n + band), clamp(66 + n + band), clamp(48 + n + band))
    # sparse embedded pebbles / roots, wrapped so the tile repeats cleanly
    for _ in range(14):
        x = rnd.randrange(32); y = rnd.randrange(32); w = rnd.choice((2, 3)); dark = rnd.random() < 0.6
        for dx in range(w):
            for dy in range(2):
                c = px[(x + dx) % 32, (y + dy) % 32]
                d = -14 if dark else 12
                px[(x + dx) % 32, (y + dy) % 32] = tuple(clamp(v + d) for v in c)
    return im

def wall_wood_tile(seed=0):
    rnd = random.Random(8400 + seed); im = Image.new('RGB', (32, 32)); px = im.load()
    for y in range(32):
        row = y // 8; off = 8 if row % 2 else 0; by = y % 8
        for x in range(32):
            xx = (x + off) % 32; bx = xx % 16
            grain = int(3 * math.sin((x + seed) * 0.9 + row) + 2 * math.sin(x * 0.23))
            if by == 0 or bx == 0:
                c = (52, 38, 27)
            else:
                base = (98 + grain, 73 + grain, 51 + grain)
                if by == 1: base = tuple(clamp(v + 8) for v in base)
                if by == 7: base = tuple(clamp(v - 9) for v in base)
                c = base
            px[x, y] = c
    # small square nails at staggered board joints
    for row in range(4):
        off = 8 if row % 2 else 0
        for j in (1, 17):
            x = (j + off) % 32; y = row * 8 + 4
            px[x, y] = (40, 32, 24); px[(x + 1) % 32, y] = (122, 98, 72)
    return im

strip('wall_stone_4', wall_stone_tile(4), 4)
strip('wall_dirt_5', wall_dirt_tile(5), 5)
strip('wall_wood_6', wall_wood_tile(6), 6)

def surface_for(big, size, seed):
    rnd = random.Random(9100 + seed); w, h = size
    cw = min(big.width, max(96, w * 3)); ch = min(big.height, max(96, h * 3))
    x0 = rnd.randrange(0, big.width - cw + 1); y0 = rnd.randrange(0, big.height - ch + 1)
    return big.crop((x0, y0, x0 + cw, y0 + ch)).resize(size, Image.Resampling.LANCZOS).load()

def smooth_light(im, radius):
    gray = ImageOps.grayscale(im.convert('RGB')).filter(ImageFilter.GaussianBlur(radius))
    gp = gray.load(); ap = im.getchannel('A').load()
    vals = [gp[x, y] for y in range(im.height) for x in range(im.width) if ap[x, y] > 0]
    mean = sum(vals) / len(vals) if vals else 128.0
    return gp, max(1.0, mean)

def edge_extend_gutters(im):
    """Restore padding gutters from nearest cell edges to prevent texture bleeding/seams."""
    out = im.copy(); px = out.load(); w, h = im.size
    cols = (w + 1) // 33; rows = (h + 1) // 33
    # vertical gutters
    for c in range(1, cols):
        x = c * 33 - 1
        if x >= w: continue
        for y in range(h):
            if px[x, y][3] == 0: continue
            left = px[x - 1, y] if x - 1 >= 0 else None
            right = px[x + 1, y] if x + 1 < w else None
            if left and right and left[3] and right[3]:
                px[x, y] = tuple((left[i] + right[i]) // 2 for i in range(3)) + (px[x, y][3],)
            elif left and left[3]: px[x, y] = left
            elif right and right[3]: px[x, y] = right
    # horizontal gutters
    for r in range(1, rows):
        y = r * 33 - 1
        if y >= h: continue
        for x in range(w):
            if px[x, y][3] == 0: continue
            up = px[x, y - 1] if y - 1 >= 0 else None
            down = px[x, y + 1] if y + 1 < h else None
            if up and down and up[3] and down[3]:
                px[x, y] = tuple((up[i] + down[i]) // 2 for i in range(3)) + (px[x, y][3],)
            elif up and up[3]: px[x, y] = up
            elif down and down[3]: px[x, y] = down
    return out

# Unified bark: one desaturated brown palette for trunk, branches and crown bases.
# The old branch pass kept the original orange hue; here every bark pixel is remapped
# through the same ramp, while original shading / contours / knots are preserved.
BARK_RAMP = [(62, 33, 15), (92, 49, 19), (126, 68, 25), (158, 91, 34), (190, 122, 52)]
def ramp_color(t, ramp=BARK_RAMP):
    t = max(0.0, min(1.0, t)) * (len(ramp) - 1)
    i = min(len(ramp) - 2, int(t)); f = t - i
    a, b = ramp[i], ramp[i + 1]
    return tuple(clamp(a[k] * (1 - f) + b[k] * f) for k in range(3))

def classify_tree_pixel(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255); h *= 360
    if (h < 18 or h > 345) and s > 0.45 and v > 0.35 and r > 105: return 'apple'
    if 38 <= h <= 170 and s > 0.14 and v > 0.10: return 'leaf'
    return 'bark'

def bark_pixel(x, y, L, detail, seed, vertical=False):
    if vertical:
        grain = 0.45 * math.sin((x * 2 * math.pi) / 8 + math.sin(y * 2 * math.pi / 32) * 0.7) + 0.25 * math.sin((x * 2 * math.pi) / 3 + y * 0.02)
    else:
        grain = 0.35 * math.sin(x * 0.33 + y * 0.11 + seed) + 0.25 * math.sin(x * 0.10 - y * 0.41 + seed * 0.7)
    t = 0.18 + 0.58 * (L / 255) + 0.10 * (detail / 32) + 0.055 * grain
    return ramp_color(t)

# Tree trunk: seamless 32px bark, no pale cut band at vertical joints.
trunk_orig = Image.open(IN / 'tree_trunk_26.png').convert('RGBA')
trunk = trunk_orig.copy(); tp = trunk.load()
trunk_light, trunk_mean = smooth_light(trunk_orig, 3.0)
trunk_gray = ImageOps.grayscale(trunk_orig.convert('RGB')).load()
for row in range(6):
    for col in range(4):
        ox = col * 33; oy = row * 33
        for y in range(32):
            for x in range(32):
                r, g, b, a = trunk_orig.getpixel((ox + x, oy + y))
                if a == 0: continue
                L = lum(r, g, b); detail = trunk_gray[ox + x, oy + y] - trunk_light[ox + x, oy + y]
                shade = 0.82 + 0.30 * (trunk_light[ox + x, oy + y] / trunk_mean)
                c = bark_pixel(x, y, L * shade, detail, col, vertical=True)
                tp[ox + x, oy + y] = (*c, a)
trunk = edge_extend_gutters(trunk)
trunk.save(PROC / 'tree_trunk_26.png')

def retexture_sprite(name, seed=0):
    im = Image.open(IN / f'{name}.png').convert('RGBA'); out = im.copy(); px = out.load()
    leaf_px = surface_for(leaf_big, im.size, seed)
    light, mean = smooth_light(im, 4.0)
    gray = ImageOps.grayscale(im.convert('RGB')).load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a == 0: continue
            kind = classify_tree_pixel(r, g, b)
            L = lum(r, g, b); detail = gray[x, y] - light[x, y]
            f = max(0.66, min(1.16, 0.88 + 0.26 * (light[x, y] / mean - 1.0)))
            if kind == 'apple':
                px[x, y] = (clamp(r * 1.04 + 3), clamp(g * 0.98), clamp(b * 0.98), a)
            elif kind == 'leaf':
                sr, sg, sb = leaf_px[x, y]
                px[x, y] = (clamp(sr * f), clamp(sg * f), clamp(sb * f), a)
            else:
                c = bark_pixel(x, y, L, detail, seed)
                px[x, y] = (*c, a)
    out = edge_extend_gutters(out)
    out.save(PROC / f'{name}.png'); return out

retexture_sprite('leaves_block_28', 28)
for i in [165, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186]:
    retexture_sprite(f'tree_branch_{i}', i)

# Generic furniture / stone / cloth retexture preserving alpha and shading.
def retexture_surface(name, big, seed, mode='wood'):
    im = Image.open(IN / f'{name}.png').convert('RGBA'); out = im.copy(); px = out.load()
    surf = surface_for(big, im.size, seed)
    stone_surf = surface_for(stone_big, im.size, seed + 7)
    cloth_surf = surface_for(cloth_big, im.size, seed + 13)
    light, mean = smooth_light(im, 2.0)
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a == 0: continue
            L = lum(r, g, b)
            f = max(0.55, min(1.25, 0.78 + 0.42 * (L / 255)))
            if mode == 'bed':
                is_cloth = (r > g * 1.15 and r > b * 1.10) or (r > 120 and g < 110 and b < 110)
                src = cloth_surf if is_cloth else surf
            elif mode == 'furnace':
                is_flame = r > 140 and g > 50 and b < 130 and r > b * 1.4
                if is_flame:
                    # flame gradient by luminance, preserve animation shape
                    t = L / 255
                    if t > 0.75: c = (255, 245, 190)
                    elif t > 0.5: c = (255, 190, 60)
                    elif t > 0.3: c = (240, 110, 25)
                    else: c = (180, 55, 15)
                    px[x, y] = (*c, a); continue
                src = stone_surf
            elif mode == 'torch':
                is_flame = r > 140 and g > 70 and b < 150 and r > b * 1.35
                if is_flame:
                    t = L / 255
                    if t > 0.78: c = (255, 250, 205)
                    elif t > 0.55: c = (255, 205, 70)
                    elif t > 0.35: c = (250, 130, 30)
                    else: c = (210, 70, 18)
                    px[x, y] = (*c, a); continue
                if L < 70:
                    px[x, y] = (clamp(40 * f), clamp(34 * f), clamp(28 * f), a); continue
                src = surf
            else:
                src = surf
            sr, sg, sb = src[x, y]
            px[x, y] = (clamp(sr * f), clamp(sg * f), clamp(sb * f), a)
    out = edge_extend_gutters(out)
    out.save(PROC / f'{name}.png'); return out

retexture_surface('workbench_block_44', furniture_big, 44)
retexture_surface('ladder_block_52', furniture_big, 52)
retexture_surface('chair_block_64', furniture_big, 64)
retexture_surface('table_block_65', furniture_big, 65)
retexture_surface('bed_block_50', furniture_big, 50, mode='bed')
retexture_surface('furnace_off_block_45', stone_big, 45, mode='furnace')
retexture_surface('furnace_on_block_46', stone_big, 46, mode='furnace')
retexture_surface('furnace_part_block_47', stone_big, 47, mode='furnace')
retexture_surface('torch_block_53', furniture_big, 53, mode='torch')
retexture_surface('small_torch_block_54', furniture_big, 54, mode='torch')
# torch in-hand animation frames
for p in sorted(IN.glob('torch_anim_*.png')):
    retexture_surface(p.stem, furniture_big, int(p.stem.split('_')[-1]), mode='torch')

# Icons: recolor original icon art with matching surfaces, preserve alpha/frame.
def recolor_icon(atlas_name, ui_name, big, seed, mode='wood'):
    for name in (atlas_name, ui_name):
        im = Image.open(IN / f'{name}.png').convert('RGBA'); out = im.copy(); px = out.load()
        surf = surface_for(big, im.size, seed)
        stone_surf = surface_for(stone_big, im.size, seed + 7)
        cloth_surf = surface_for(cloth_big, im.size, seed + 13)
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = im.getpixel((x, y))
                if a == 0: continue
                L = lum(r, g, b); f = max(0.55, min(1.25, 0.78 + 0.42 * (L / 255)))
                if mode == 'bed':
                    is_cloth = (r > g * 1.15 and r > b * 1.10) or (r > 120 and g < 110 and b < 110)
                    src = cloth_surf if is_cloth else surf
                elif mode == 'furnace':
                    is_flame = r > 140 and g > 50 and b < 130 and r > b * 1.4
                    if is_flame:
                        t = L / 255
                        c = (255, 245, 190) if t > 0.75 else (255, 190, 60) if t > 0.5 else (240, 110, 25) if t > 0.3 else (180, 55, 15)
                        px[x, y] = (*c, a); continue
                    src = stone_surf
                elif mode == 'torch':
                    is_flame = r > 140 and g > 70 and b < 150 and r > b * 1.35
                    if is_flame:
                        t = L / 255
                        c = (255, 250, 205) if t > 0.78 else (255, 205, 70) if t > 0.55 else (250, 130, 30) if t > 0.35 else (210, 70, 18)
                        px[x, y] = (*c, a); continue
                    if L < 70: px[x, y] = (clamp(40 * f), clamp(34 * f), clamp(28 * f), a); continue
                    src = surf
                else:
                    src = surf
                sr, sg, sb = src[x, y]
                px[x, y] = (clamp(sr * f), clamp(sg * f), clamp(sb * f), a)
        out.save(PROC / f'{name}.png')

icon_jobs = [
    ('clay_icon_atlas_272', 'clay_icon_ui_272', GEN / 'red_clay_master.png', 272, 'wood'),
    ('wood_icon_atlas_282', 'wood_icon_ui_282', GEN / 'oak_planks_master.png', 282, 'wood'),
    ('wood_planks_icon_atlas_363', 'wood_planks_icon_ui_363', GEN / 'oak_planks_master.png', 363, 'wood'),
    ('workbench_icon_atlas_291', 'workbench_icon_ui_291', GEN / 'furniture_wood_master.png', 291, 'wood'),
    ('furnace_icon_atlas_292', 'furnace_icon_ui_292', V03GEN / 'natural_stone_master_v3.png', 292, 'furnace'),
    ('bed_icon_atlas_295', 'bed_icon_ui_295', GEN / 'furniture_wood_master.png', 295, 'bed'),
    ('ladder_icon_atlas_297', 'ladder_icon_ui_297', GEN / 'furniture_wood_master.png', 297, 'wood'),
    ('torch_icon_atlas_298', 'torch_icon_ui_298', GEN / 'furniture_wood_master.png', 298, 'torch'),
    ('small_torch_icon_atlas_299', 'small_torch_icon_ui_299', GEN / 'furniture_wood_master.png', 299, 'torch'),
    ('chair_icon_atlas_309', 'chair_icon_ui_309', GEN / 'furniture_wood_master.png', 309, 'wood'),
    ('table_icon_atlas_310', 'table_icon_ui_310', GEN / 'furniture_wood_master.png', 310, 'wood'),
    ('wall_stone_icon_atlas_4', 'wall_stone_icon_ui_4', V03GEN / 'natural_stone_master_v3.png', 4, 'wood'),
    ('wall_dirt_icon_atlas_5', 'wall_dirt_icon_ui_5', V03GEN / 'dirt_master_v2.png', 5, 'wood'),
    ('wall_wood_icon_atlas_6', 'wall_wood_icon_ui_6', GEN / 'oak_planks_master.png', 6, 'wood'),
    ('wood_pickaxe_icon_atlas_1058', 'wood_pickaxe_icon_ui_1058', GEN / 'furniture_wood_master.png', 1058, 'wood'),
    ('cudgel_icon_atlas_1064', 'cudgel_icon_ui_1064', GEN / 'furniture_wood_master.png', 1064, 'wood'),
    ('wooden_helmet_icon_atlas_1208', 'wooden_helmet_icon_ui_1208', GEN / 'wooden_armor_master.png', 1208, 'wood'),
    ('wooden_chainmail_icon_atlas_1209', 'wooden_chainmail_icon_ui_1209', GEN / 'wooden_armor_master.png', 1209, 'wood'),
    ('wooden_greaves_icon_atlas_1215', 'wooden_greaves_icon_ui_1215', GEN / 'wooden_armor_master.png', 1215, 'wood'),
    ('leaves_icon_atlas_281', 'leaves_icon_ui_281', V03GEN / 'leaf_canopy_master_v2.png', 281, 'wood'),
]
# wall dirt icon should use dirt tile, not a possibly absent master; handle separately below.
icon_jobs = [j for j in icon_jobs if j[0] != 'wall_dirt_icon_atlas_5']
for atlas, ui, master, seed, mode in icon_jobs:
    big = Image.open(master).convert('RGB')
    recolor_icon(atlas, ui, big, seed, mode)
# wall dirt icon from processed dirt wall tile
wt = Image.open(PROC / 'wall_dirt_5.png').crop((0, 0, 32, 32))
for name in ['wall_dirt_icon_atlas_5', 'wall_dirt_icon_ui_5']:
    im = Image.open(IN / f'{name}.png').convert('RGBA'); alpha = im.getchannel('A')
    out = wt.resize(im.size, Image.Resampling.LANCZOS).convert('RGBA'); out.putalpha(alpha); out.save(PROC / f'{name}.png')

# Worn wooden armor: keep the ORIGINAL hand-drawn plates / straps / grain / silhouettes.
# The previous procedural wood overlay flattened all of that detail. Only a mild material
# grade + unsharp is applied, so the equipped armor matches the quality of the original art.
def grade_armor(im):
    im = im.convert('RGBA'); alpha = im.getchannel('A')
    rgb = im.convert('RGB')
    # Walnut grade: visibly cooler/darker than the original orange wood, but the
    # original hand-drawn plates / straps / grain / silhouettes are fully preserved.
    rgb = ImageEnhance.Color(rgb).enhance(0.72)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.20)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.94)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.0, percent=100, threshold=2))
    px = rgb.load()
    for y in range(rgb.height):
        for x in range(rgb.width):
            r, g, b = px[x, y]; px[x, y] = (clamp(r), clamp(g * 0.97), clamp(b * 0.92))
    out = rgb.convert('RGBA'); out.putalpha(alpha); return out
for p in sorted(IN.glob('armor_*.png')):
    grade_armor(Image.open(p)).save(PROC / f'{p.stem}.png')
# armor icons: same detail-preserving grade (do NOT run the generic surface recolorer)
for n in ['wooden_helmet_icon_atlas_1208', 'wooden_helmet_icon_ui_1208',
          'wooden_chainmail_icon_atlas_1209', 'wooden_chainmail_icon_ui_1209',
          'wooden_greaves_icon_atlas_1215', 'wooden_greaves_icon_ui_1215']:
    grade_armor(Image.open(IN / f'{n}.png')).save(PROC / f'{n}.png')
# wall icons must match the new dedicated wall tiles, not the foreground materials
for mat, cid in [('stone', 4), ('dirt', 5), ('wood', 6)]:
    wt = Image.open(PROC / f'wall_{mat}_{cid}.png').crop((0, 0, 32, 32))
    for n in [f'wall_{mat}_icon_atlas_{cid}', f'wall_{mat}_icon_ui_{cid}']:
        im = Image.open(IN / f'{n}.png').convert('RGBA'); alpha = im.getchannel('A')
        o = wt.resize(im.size, Image.Resampling.LANCZOS).convert('RGBA'); o.putalpha(alpha); o.save(PROC / f'{n}.png')

# Particles
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
particle('hit_clay', palette(clay_base), 17)
particle('hit_wood', palette(planks_base), 29)
particle('hit_leaves', palette(leaf_big.resize((32, 32))), 28)

# --- v0.5: all six ores rebuilt on the accepted stone texture ---
# Background = exact processed stone variants; mineral overlays = original ore shapes/shading.
ORE_DEFS = [
    ('coal', 5, 260, 1024, 'coal'),
    ('bronze', 167, 420, 1194, 'bronze'),
    ('iron', 6, 261, 1025, 'iron'),
    ('gold', 7, 262, 1026, 'gold'),
    ('diamond', 8, 263, 1027, 'diamond'),
    ('fire_iron', 9, 264, 1028, 'fire_iron'),
]
stone_orig_strip = Image.open(IN / 'stone_block_4.png').convert('RGBA')
stone_new_strip = Image.open(PROC / 'stone_block_4.png').convert('RGBA')
ore_reports = {}; ore_mineral_colors = {}

def ore_mask_alpha(name, r, g, b, diff):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255); h *= 360
    L = lum(r, g, b)
    a = max(0.0, (diff - 10) / 28)
    if name == 'coal' and L < 80: a = max(a, (80 - L) / 25)
    if name == 'bronze' and 10 <= h <= 48 and s > 0.30: a = max(a, (s - 0.30) / 0.25)
    if name == 'iron' and L > 140 and s < 0.35: a = max(a, (L - 140) / 35)
    if name == 'gold' and 38 <= h <= 65 and s > 0.35: a = max(a, (s - 0.35) / 0.25)
    if name == 'diamond' and 160 <= h <= 210 and s > 0.25: a = max(a, (s - 0.25) / 0.25)
    if name == 'fire_iron' and 250 <= h <= 330 and s > 0.18: a = max(a, (s - 0.18) / 0.22)
    return clamp(min(1.0, a) * 255)

def grade_mineral_icon(im, name):
    im = im.convert('RGBA'); alpha = im.getchannel('A'); rgb = im.convert('RGB')
    params = {
        'coal': (0.90, 1.15, 1.05), 'bronze': (1.05, 1.08, 1.00),
        'iron': (0.85, 1.12, 1.03), 'gold': (1.05, 1.08, 1.02),
        'diamond': (1.08, 1.10, 1.03), 'fire_iron': (1.05, 1.08, 1.02),
    }
    sat, con, bri = params[name]
    rgb = ImageEnhance.Color(rgb).enhance(sat)
    rgb = ImageEnhance.Contrast(rgb).enhance(con)
    rgb = ImageEnhance.Brightness(rgb).enhance(bri)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=0.8, percent=70, threshold=2))
    out = rgb.convert('RGBA'); out.putalpha(alpha); return out

def ore_block_icon(tile_cell, size):
    w, h = size; out = Image.new('RGBA', size, (0, 0, 0, 0))
    mx = 1 if w <= 18 else 2; my = 1 if h <= 16 else 2
    iw, ih = w - 2*mx, h - 2*my
    inner = tile_cell.resize((iw, ih), Image.Resampling.LANCZOS).convert('RGBA')
    out.alpha_composite(inner, (mx, my))
    px = out.load()
    for x in range(mx, w-mx):
        r, g, b, a = px[x, my]; px[x, my] = (clamp(r+18), clamp(g+18), clamp(b+18), a)
        r, g, b, a = px[x, h-my-1]; px[x, h-my-1] = (clamp(r-22), clamp(g-22), clamp(b-22), a)
    for y in range(my, h-my):
        r, g, b, a = px[mx, y]; px[mx, y] = (clamp(r+10), clamp(g+10), clamp(b+10), a)
        r, g, b, a = px[w-mx-1, y]; px[w-mx-1, y] = (clamp(r-16), clamp(g-16), clamp(b-16), a)
    return out

for name, block_id, place_id, drop_id, hit in ORE_DEFS:
    orig = Image.open(IN / f'{name}_ore_block_{block_id}.png').convert('RGBA')
    out = stone_new_strip.copy(); mineral_colors = []; bg_exact = 0; total_px = 0
    for off in OFFS:
        oc = orig.crop((off, 0, off+32, 32))
        si = stone_orig_strip.crop((off, 0, off+32, 32))
        so = stone_new_strip.crop((off, 0, off+32, 32))
        layer = Image.new('RGBA', (32, 32), (0, 0, 0, 0)); lp = layer.load()
        op = oc.load(); sp = si.load()
        for y in range(32):
            for x in range(32):
                r, g, b, a = op[x, y]
                rr, gg, bb, aa = sp[x, y]
                diff = max(abs(r-rr), abs(g-gg), abs(b-bb))
                al = ore_mask_alpha(name, r, g, b, diff)
                if al:
                    lp[x, y] = (r, g, b, al)
                    if al > 180: mineral_colors.append((r, g, b))
        layer = layer.filter(ImageFilter.MedianFilter(3))
        alpha = layer.getchannel('A')
        rgb = ImageEnhance.Contrast(layer.convert('RGB')).enhance(1.08)
        rgb = ImageEnhance.Color(rgb).enhance(1.05)
        layer = rgb.convert('RGBA'); layer.putalpha(alpha)
        so.alpha_composite(layer)
        out.paste(so, (off, 0))
        # background match stats
        opx = out.load(); spx = stone_new_strip.load()
        for y in range(32):
            for x in range(32):
                total_px += 1
                if opx[off+x, y] == spx[off+x, y]: bg_exact += 1
    out.save(PROC / f'{name}_ore_block_{block_id}.png')
    ore_mineral_colors[name] = mineral_colors or [(128, 128, 128)]
    ore_reports[name] = {'block_id': block_id, 'background_exact_fraction': round(bg_exact / total_px, 4),
                         'mineral_pixels_sampled': len(mineral_colors)}
    # dropped mineral icons: preserve original silhouette/alpha, grade to match the block mineral
    for p in IN.glob(f'{name}_ore_drop_icon_*.png'):
        grade_mineral_icon(Image.open(p), name).save(PROC / p.name)
    # dedicated placeable icon exists only for bronze in the original atlas; make it read as an ore block
    tile_cell = out.crop((0, 0, 32, 32))
    for p in IN.glob(f'{name}_ore_block_icon_*.png'):
        im = Image.open(p)
        ore_block_icon(tile_cell, im.size).save(PROC / p.name)
    # hit / destroy particles: stone + mineral palette, original alpha
    hp = IN / f'hit_{hit}.png'
    if hp.exists():
        orig_hit = Image.open(hp).convert('RGBA'); ph = orig_hit.copy(); px = ph.load()
        rnd = random.Random(9500 + block_id)
        spal = palette(stone_new_strip.crop((0, 0, 32, 32)))
        mpal = sorted(set(ore_mineral_colors[name]))
        if len(mpal) > 14:
            q = Image.new('RGB', (len(mpal), 1))
            q.putdata(mpal); mpal = palette(q)
        for y in range(ph.height):
            for x in range(ph.width):
                r, g, b, a = orig_hit.getpixel((x, y))
                if a == 0: px[x, y] = (0, 0, 0, 0); continue
                h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                use_mineral = s > 0.22 or rnd.random() < 0.42
                c = (mpal if use_mineral else spal)[rnd.randrange(len(mpal if use_mineral else spal))]
                if x + y < 3: c = tuple(clamp(v+18) for v in c)
                if x > ph.width-3 and y > ph.height-3: c = tuple(clamp(v-16) for v in c)
                px[x, y] = (*c, a)
        ph.save(PROC / f'hit_{hit}.png')

# Verify every target has a processed file.
targets = json.loads((ROOT / 'verification/targets.json').read_text())
for t in targets['targets']:
    if not (PROC / f"{t['label']}.png").exists(): raise FileNotFoundError(t['label'])
targets['version'] = 'textures-v0.5'
(ROOT / 'verification/targets.json').write_text(json.dumps(targets, indent=2))

# Previews
def on_bg(im, bg=(135, 180, 220, 255)):
    b = Image.new('RGBA', im.size, bg); b.alpha_composite(im); return b.convert('RGB')
# trunk stacked preview: repeat row0 cell vertically to check seams
tr = Image.open(PROC / 'tree_trunk_26.png').convert('RGBA')
cell = tr.crop((0, 0, 32, 32))
stack = Image.new('RGBA', (32, 32 * 8), (0, 0, 0, 0))
for i in range(8): stack.alpha_composite(cell, (0, i * 32))
on_bg(stack).resize((32 * 6, 32 * 8 * 6), Image.Resampling.NEAREST).save(PREV / 'trunk-stacked-seam-check.png')
on_bg(tr).resize((tr.width * 3, tr.height * 3), Image.Resampling.NEAREST).save(PREV / 'tree_trunk_26-v05.png')
for n in ['tree_branch_168', 'tree_branch_171']:
    im = Image.open(PROC / f'{n}.png').convert('RGBA'); on_bg(im).resize((im.width * 3, im.height * 3), Image.Resampling.NEAREST).save(PREV / f'{n}-v05.png')
# grass stacked
stack = Image.new('RGBA', (131, 64), (0, 0, 0, 0))
stack.alpha_composite(Image.open(PROC / 'grass_block_18.png').convert('RGBA'), (0, 32))
stack.alpha_composite(Image.open(PROC / 'tallgrass_block_19.png').convert('RGBA'), (0, 0))
on_bg(stack).resize((131 * 8, 64 * 8), Image.Resampling.NEAREST).save(PREV / 'tallgrass-on-grass-v05.png')
# terrain compare
rows = [('DIRT', 'dirt_block_14'), ('TALL GRASS', 'tallgrass_block_19'), ('CLAY', 'clay_block_17'), ('PLANKS', 'wood_block_29')]
scale = 6; w = 131 * scale; h = 32 * scale; gap = 24; label = 22
sheet = Image.new('RGB', (w * 3 + gap * 2, (h + label) * len(rows) + gap * (len(rows) - 1) + 20), (18, 20, 24)); d = ImageDraw.Draw(sheet)
for row, (title, name) in enumerate(rows):
    y = row * (h + label + gap) + label + 10
    old = Image.open(IN / f'{name}.png').convert('RGBA')
    v03p = V03 / f'{name}.png'
    mid = Image.open(v03p).convert('RGBA') if v03p.exists() else old
    new = Image.open(PROC / f'{name}.png').convert('RGBA')
    for col, im in enumerate([old, mid, new]):
        if name == 'tallgrass_block_19': im = on_bg(im, (40, 32, 20, 255)).convert('RGBA')
        x = col * (w + gap); d.text((x, y - 18), f'{title} ' + ['ORIGINAL', 'v0.3', 'v0.5'][col], fill=(220, 220, 220) if col < 2 else (140, 255, 170)); sheet.paste(im.convert('RGB').resize((w, h), Image.Resampling.NEAREST), (x, y))
sheet.save(PREV / 'terrain-before-after-v05.png')
# furniture / items contact sheet
names = ['workbench_block_44', 'furnace_off_block_45', 'furnace_on_block_46', 'ladder_block_52', 'chair_block_64', 'table_block_65', 'bed_block_50', 'torch_block_53', 'wall_stone_4', 'wall_dirt_5', 'wall_wood_6', 'wood_planks_block_114']
cellw = 300; cellh = 220; cols = 3; rowsn = math.ceil(len(names) / cols)
sheet = Image.new('RGB', (cols * cellw, rowsn * cellh), (24, 26, 30)); d = ImageDraw.Draw(sheet)
for idx, name in enumerate(names):
    im = Image.open(PROC / f'{name}.png').convert('RGBA')
    sc = min((cellw - 20) / im.width, (cellh - 40) / im.height, 4)
    big = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.Resampling.NEAREST)
    x = (idx % cols) * cellw; y = (idx // cols) * cellh
    d.text((x + 6, y + 4), name, fill=(220, 220, 220))
    bg = Image.new('RGBA', big.size, (60, 64, 72, 255)); bg.alpha_composite(big); sheet.paste(bg.convert('RGB'), (x + (cellw - big.width) // 2, y + 24))
sheet.save(PREV / 'furniture-walls-v05.png')
# icons sheet
icon_names = ['clay_icon_ui_272', 'wood_icon_ui_282', 'workbench_icon_ui_291', 'furnace_icon_ui_292', 'bed_icon_ui_295', 'ladder_icon_ui_297', 'torch_icon_ui_298', 'chair_icon_ui_309', 'table_icon_ui_310', 'wood_pickaxe_icon_ui_1058', 'cudgel_icon_ui_1064', 'wooden_helmet_icon_ui_1208', 'wooden_chainmail_icon_ui_1209', 'wooden_greaves_icon_ui_1215', 'wall_stone_icon_ui_4', 'wall_dirt_icon_ui_5', 'wall_wood_icon_ui_6']
cell = 120; cols = 6; rowsn = math.ceil(len(icon_names) / cols)
sheet = Image.new('RGB', (cols * cell, rowsn * cell), (24, 26, 30)); d = ImageDraw.Draw(sheet)
for idx, name in enumerate(icon_names):
    im = Image.open(PROC / f'{name}.png').convert('RGBA'); big = im.resize((96, 96), Image.Resampling.NEAREST)
    x = (idx % cols) * cell; y = (idx // cols) * cell
    d.text((x + 4, y + 2), name.replace('_icon_ui', ''), fill=(220, 220, 220))
    bg = Image.new('RGBA', big.size, (60, 64, 72, 255)); bg.alpha_composite(big); sheet.paste(bg.convert('RGB'), (x + 12, y + 20))
sheet.save(PREV / 'icons-v05.png')

# --- targeted verification for v0.5: orange oak + ores on accepted stone ---
fixes = {'version': 'textures-v0.5-oak-ores', 'trees': {}, 'ores': ore_reports, 'armor': {}, 'grass': {}, 'walls': {}}
ramp_samples = [ramp_color(i / 96) for i in range(97)]
def near_bark_ramp(r, g, b):
    return min((r-c[0])**2 + (g-c[1])**2 + (b-c[2])**2 for c in ramp_samples) <= 12
bark_px_total = 0; bark_rgb = [0, 0, 0]
tree_names = ['tree_trunk_26'] + [f'tree_branch_{i}' for i in [165, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186]]
for n in tree_names:
    im = Image.open(PROC / f'{n}.png').convert('RGBA')
    for r, g, b, a in im.getdata():
        if a < 128 or not near_bark_ramp(r, g, b): continue
        bark_px_total += 1; bark_rgb[0] += r; bark_rgb[1] += g; bark_rgb[2] += b
assert bark_px_total > 10000, bark_px_total
mean_bark = [round(v / bark_px_total, 2) for v in bark_rgb]
assert mean_bark[0] > mean_bark[1] > mean_bark[2] and mean_bark[0] > 90, mean_bark
fixes['trees'] = {'orange_oak_bark_pixels': bark_px_total, 'mean_bark_rgb': mean_bark,
                  'unified_bark_ramp': BARK_RAMP, 'trunk_and_branch_ids': [26, 165, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186]}
for name, rep in ore_reports.items():
    assert rep['background_exact_fraction'] > 0.30, (name, rep)
    assert rep['mineral_pixels_sampled'] > 20, (name, rep)
# gutter columns must remain exactly the accepted stone gutters
for name, block_id, *_ in ORE_DEFS:
    ore = Image.open(PROC / f'{name}_ore_block_{block_id}.png').convert('RGBA')
    for gx in GUT:
        assert ore.crop((gx, 0, gx+1, 32)).tobytes() == stone_new_strip.crop((gx, 0, gx+1, 32)).tobytes(), (name, gx)
# armor: alpha must be identical and pixels close to original (detail preserved, not repainted)
adiffs = []; amax = 0
for p in sorted(IN.glob('armor_*.png')):
    a = Image.open(p).convert('RGBA'); b = Image.open(PROC / p.name).convert('RGBA')
    assert a.size == b.size and a.getchannel('A').tobytes() == b.getchannel('A').tobytes(), p.name
    da = a.convert('RGB').tobytes(); db = b.convert('RGB').tobytes()
    md = sum(abs(x - y) for x, y in zip(da, db)) / len(da); adiffs.append(md); amax = max(amax, md)
fixes['armor'] = {'frames': len(adiffs), 'mean_abs_rgb_diff': round(sum(adiffs) / len(adiffs), 3), 'max_frame_mean_abs_diff': round(amax, 3),
                  'standalone_worn_sheets': len(list(IN.glob('armor_standalone_*.png'))),
                  'method': 'original artwork preserved; walnut color/contrast grade + unsharp; no procedural surface overlay; standalone worn sheets replaced'}
assert amax < 24, amax
# grass: taller + sparser than the previous 18px dense bush
tg = Image.open(PROC / 'tallgrass_block_19.png').convert('RGBA'); heights = []; covers = []
for off in OFFS:
    cell = tg.crop((off, 0, off + 32, 32)); ys = [y for y in range(32) for x in range(32) if cell.getpixel((x, y))[3] > 40]
    heights.append(32 - min(ys) if ys else 0); covers.append(round(len(ys) / 1024, 4))
fixes['grass'] = {'blade_heights_px': heights, 'alpha_coverage_per_variant': covers, 'max_coverage': max(covers), 'min_height': min(heights)}
assert min(heights) >= 23 and max(covers) < 0.24, fixes['grass']
# walls: dedicated materials, lower luminance than foreground counterparts
wall_ids = {'stone': 4, 'dirt': 5, 'wood': 6}
for mat, fg in [('stone', 'stone_block_4'), ('dirt', 'dirt_block_14'), ('wood', 'wood_planks_block_114')]:
    w = Image.open(PROC / f'wall_{mat}_{wall_ids[mat]}.png').convert('RGB')
    f = Image.open(PROC / f'{fg}.png').convert('RGB')
    wl = sum(lum(*p) for p in w.getdata()) / (w.width * w.height); fl = sum(lum(*p) for p in f.getdata()) / (f.width * f.height)
    fixes['walls'][mat] = {'wall_mean_luma': round(wl, 2), 'foreground_mean_luma': round(fl, 2), 'darker_than_foreground': wl < fl}
    assert wl < fl, mat
(ROOT / 'verification/fixes-v05.json').write_text(json.dumps(fixes, indent=2))

# correction previews: armor detail + dedicated walls
anames = ['armor_male_armor_head_1208_0', 'armor_male_armor_body_1209_0', 'armor_male_armor_legs_1215_0', 'armor_male_armor_body_1209_5', 'armor_female_armor_body_1209_0', 'wooden_helmet_icon_ui_1208', 'wooden_chainmail_icon_ui_1209', 'wooden_greaves_icon_ui_1215']
cw = 300; ch = 250; cols = 4; s = Image.new('RGB', (cw * cols, ch * 2), (24, 26, 30)); d = ImageDraw.Draw(s)
for idx, n in enumerate(anames):
    x = (idx % cols) * cw; y = (idx // cols) * ch; d.text((x + 6, y + 4), n + '  ORIG / v0.4', fill=(220, 220, 220))
    for j, folder in enumerate([IN, PROC]):
        im = Image.open(folder / f'{n}.png').convert('RGBA'); sc = min(130 / im.width, 190 / im.height, 8)
        big = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.Resampling.NEAREST)
        bg = Image.new('RGBA', big.size, (30, 55, 58, 255)); bg.alpha_composite(big); s.paste(bg.convert('RGB'), (x + j * 150 + (130 - big.width) //2, y + 28))
s.save(PREV / 'armor-detail-v05.png')
wnames = ['wall_stone_4', 'wall_dirt_5', 'wall_wood_6']; s = Image.new('RGB', (131 * 4 * 3, 32 * 4 * 3 + 60), (24, 26, 30)); d = ImageDraw.Draw(s)
for idx, n in enumerate(wnames):
    im = Image.open(PROC / f'{n}.png').convert('RGBA'); big = on_bg(im, (45, 51, 56, 255)).resize((131 * 4, 32 * 4), Image.Resampling.NEAREST)
    y = idx * (32 * 4 + 20); d.text((6, y + 2), n, fill=(220, 220, 220)); s.paste(big.convert('RGB'), (0, y + 18))
s.save(PREV / 'walls-v05.png')

# v0.5 ore contact sheet: original block / new block / drop icon / particle
s = Image.new('RGB', (1180, 6 * 170 + 30), (24, 26, 30)); d = ImageDraw.Draw(s)
for idx, (name, block_id, place_id, drop_id, hit) in enumerate(ORE_DEFS):
    y = idx * 170 + 24
    d.text((8, y - 16), f'{name.upper()}  block {block_id} / drop {drop_id}', fill=(230, 230, 230))
    old = Image.open(IN / f'{name}_ore_block_{block_id}.png').convert('RGBA')
    new = Image.open(PROC / f'{name}_ore_block_{block_id}.png').convert('RGBA')
    s.paste(old.resize((524, 128), Image.Resampling.NEAREST).convert('RGB'), (8, y))
    s.paste(new.resize((524, 128), Image.Resampling.NEAREST).convert('RGB'), (548, y))
    icon = Image.open(PROC / f'{name}_ore_drop_icon_ui_{drop_id}.png').convert('RGBA')
    bg = Image.new('RGBA', icon.size, (50, 55, 65, 255)); bg.alpha_composite(icon)
    s.paste(bg.resize((96, 96), Image.Resampling.NEAREST).convert('RGB'), (1090, y))
    if (PROC / f'hit_{hit}.png').exists():
        p = Image.open(PROC / f'hit_{hit}.png').convert('RGBA'); bg = Image.new('RGBA', p.size, (50, 55, 65, 255)); bg.alpha_composite(p)
        s.paste(bg.resize((48, 48), Image.Resampling.NEAREST).convert('RGB'), (1090, y + 104))
s.save(PREV / 'ores-before-after-v05.png')
# orange oak tree compare
s = Image.new('RGB', (1240, 460), (24, 26, 30)); d = ImageDraw.Draw(s)
for j, (folder, label) in enumerate([(IN, 'ORIGINAL'), (PROC, 'v0.5 ORANGE OAK')]):
    d.text((j * 620 + 8, 4), label, fill=(230, 230, 230))
    im = Image.open(folder / 'tree_branch_168.png').convert('RGBA')
    bg = Image.new('RGBA', im.size, (135, 180, 220, 255)); bg.alpha_composite(im)
    s.paste(bg.resize((600, 400), Image.Resampling.NEAREST).convert('RGB'), (j * 620 + 8, 28))
s.save(PREV / 'oak-tree-before-after-v05.png')

manifest = {'version': 'textures-v0.5', 'targets': len(targets['targets']), 'files': {p.name: {'sha256': sha(p), 'size': list(Image.open(p).size)} for p in PROC.glob('*.png')}}
(ROOT / 'verification/processed.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps({'targets': manifest['targets'], 'files': len(manifest['files']), 'fixes': fixes}))
