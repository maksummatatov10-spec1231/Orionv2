#!/usr/bin/env python3
"""v0.4: fix trunk seams, lower grass, lighter dirt, clay correction, furniture/items/walls/armor.
Preserves atlas geometry, alpha masks, animation frame counts and icon frames.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
import json, hashlib, random, shutil, math

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / 'input'; GEN = ROOT / 'generated'; PROC = ROOT / 'processed'; PREV = ROOT / 'preview'
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

# Tall grass: lower than v0.3 (18px), still long blades not a bush.
def key_magenta(path):
    im = Image.open(path).convert('RGB'); W, H = im.size; src = im.load()
    out = Image.new('RGBA', (32, 32), (0, 0, 0, 0)); px = out.load()
    for cy in range(32):
        for cx in range(32):
            rs = gs = bs = n = 0
            y0 = cy * H // 32; y1 = (cy + 1) * H // 32; x0 = cx * W // 32; x1 = (cx + 1) * W // 32
            for y in range(y0, y1):
                for x in range(x0, x1):
                    r, g, b = src[x, y]
                    if r > 140 and b > 140 and g < 120 and r > g * 1.25 and b > g * 1.25: continue
                    if g >= b * 1.05 and g >= r * 0.70: rs += r; gs += g; bs += b; n += 1
            cell = (y1 - y0) * (x1 - x0)
            if n >= cell * 0.04: px[cx, cy] = (rs // n, gs // n, bs // n, 255)
    return out
master = key_magenta(V03GEN / 'tallgrass_long_master_v3.png')
bbox = master.getbbox(); tile = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
if bbox:
    crop = master.crop(bbox); scale = min(32 / crop.width, 18 / crop.height, 1.0)
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
# walls: darker background variants
strip('wall_stone_4', ImageEnhance.Brightness(stone_base).enhance(0.72), 4)
strip('wall_dirt_5', ImageEnhance.Brightness(dirt.crop((0, 0, 32, 32)).convert('RGB')).enhance(0.78), 5)
strip('wall_wood_6', ImageEnhance.Brightness(planks_base).enhance(0.80), 6)

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

# Tree trunk: seamless bark tile per cell + edge-extended gutters.
trunk_orig = Image.open(IN / 'tree_trunk_26.png').convert('RGBA')
trunk = trunk_orig.copy(); tp = trunk.load()
for row in range(6):
    for col in range(4):
        ox = col * 33; oy = row * 33
        shift = (col * 7 + row * 3) % 32
        for y in range(32):
            for x in range(32):
                r, g, b, a = trunk_orig.getpixel((ox + x, oy + y))
                if a == 0: continue
                sr, sg, sb = bark_tile.getpixel(((x + shift) % 32, y))
                L = lum(r, g, b)
                f = 0.72 + 0.40 * (L / 255)
                nr, ng, nb = sr * f, sg * f, sb * f
                # pale cut rings / fresh wood
                if L > 150 and r > 160 and g > 110 and r > b * 1.15:
                    nr = nr * 0.30 + 205 * 0.70; ng = ng * 0.30 + 172 * 0.70; nb = nb * 0.30 + 126 * 0.70
                tp[ox + x, oy + y] = (clamp(nr), clamp(ng), clamp(nb), a)
trunk = edge_extend_gutters(trunk)
trunk.save(PROC / 'tree_trunk_26.png')

def retexture_sprite(name, seed=0):
    im = Image.open(IN / f'{name}.png').convert('RGBA'); out = im.copy(); px = out.load()
    leaf_px = surface_for(leaf_big, im.size, seed)
    bark_px = surface_for(bark_big, im.size, seed + 101)
    light, mean = smooth_light(im, 5.0)
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a == 0: continue
            L = lum(r, g, b)
            is_apple = r > 110 and r > g * 1.35 and r > b * 1.35 and g < 130
            is_green = (g > r * 1.02 and g > b * 1.02) or (g >= r and g >= b and g > 35 and b < 160)
            f = max(0.62, min(1.18, 0.86 + 0.30 * (light[x, y] / mean - 1.0)))
            if is_apple:
                px[x, y] = (clamp(r * 1.05 + 4), clamp(g * 0.97), clamp(b * 0.97), a)
            elif is_green:
                sr, sg, sb = leaf_px[x, y]
                px[x, y] = (clamp(sr * f), clamp(sg * f), clamp(sb * f), a)
            else:
                sr, sg, sb = bark_px[x, y]
                nr, ng, nb = sr * f * 0.75 + 90 * 0.25, sg * f * 0.75 + 66 * 0.25, sb * f * 0.75 + 46 * 0.25
                if L > 150 and r > 160 and g > 110 and r > b * 1.15:
                    nr = nr * 0.35 + 205 * 0.65; ng = ng * 0.35 + 172 * 0.65; nb = nb * 0.35 + 126 * 0.65
                px[x, y] = (clamp(nr), clamp(ng), clamp(nb), a)
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

# Worn wooden armor frames: recolor with armor surface, preserve alpha/shading.
for p in sorted(IN.glob('armor_*.png')):
    im = Image.open(p).convert('RGBA'); out = im.copy(); px = out.load()
    surf = surface_for(armor_big, im.size, int(hashlib.md5(p.stem.encode()).hexdigest()[:8], 16) % 10000)
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a == 0: continue
            L = lum(r, g, b); f = max(0.55, min(1.25, 0.78 + 0.42 * (L / 255)))
            sr, sg, sb = surf[x, y]
            px[x, y] = (clamp(sr * f), clamp(sg * f), clamp(sb * f), a)
    out.save(PROC / f'{p.stem}.png')

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

# Verify every target has a processed file.
targets = json.loads((ROOT / 'verification/targets.json').read_text())
for t in targets['targets']:
    if not (PROC / f"{t['label']}.png").exists(): raise FileNotFoundError(t['label'])
targets['version'] = 'textures-v0.4'
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
on_bg(tr).resize((tr.width * 3, tr.height * 3), Image.Resampling.NEAREST).save(PREV / 'tree_trunk_26-v04.png')
for n in ['tree_branch_168', 'tree_branch_171']:
    im = Image.open(PROC / f'{n}.png').convert('RGBA'); on_bg(im).resize((im.width * 3, im.height * 3), Image.Resampling.NEAREST).save(PREV / f'{n}-v04.png')
# grass stacked
stack = Image.new('RGBA', (131, 64), (0, 0, 0, 0))
stack.alpha_composite(Image.open(PROC / 'grass_block_18.png').convert('RGBA'), (0, 32))
stack.alpha_composite(Image.open(PROC / 'tallgrass_block_19.png').convert('RGBA'), (0, 0))
on_bg(stack).resize((131 * 8, 64 * 8), Image.Resampling.NEAREST).save(PREV / 'tallgrass-on-grass-v04.png')
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
        x = col * (w + gap); d.text((x, y - 18), f'{title} ' + ['ORIGINAL', 'v0.3', 'v0.4'][col], fill=(220, 220, 220) if col < 2 else (140, 255, 170)); sheet.paste(im.convert('RGB').resize((w, h), Image.Resampling.NEAREST), (x, y))
sheet.save(PREV / 'terrain-before-after-v04.png')
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
sheet.save(PREV / 'furniture-walls-v04.png')
# icons sheet
icon_names = ['clay_icon_ui_272', 'wood_icon_ui_282', 'workbench_icon_ui_291', 'furnace_icon_ui_292', 'bed_icon_ui_295', 'ladder_icon_ui_297', 'torch_icon_ui_298', 'chair_icon_ui_309', 'table_icon_ui_310', 'wood_pickaxe_icon_ui_1058', 'cudgel_icon_ui_1064', 'wooden_helmet_icon_ui_1208', 'wooden_chainmail_icon_ui_1209', 'wooden_greaves_icon_ui_1215', 'wall_stone_icon_ui_4', 'wall_dirt_icon_ui_5', 'wall_wood_icon_ui_6']
cell = 120; cols = 6; rowsn = math.ceil(len(icon_names) / cols)
sheet = Image.new('RGB', (cols * cell, rowsn * cell), (24, 26, 30)); d = ImageDraw.Draw(sheet)
for idx, name in enumerate(icon_names):
    im = Image.open(PROC / f'{name}.png').convert('RGBA'); big = im.resize((96, 96), Image.Resampling.NEAREST)
    x = (idx % cols) * cell; y = (idx // cols) * cell
    d.text((x + 4, y + 2), name.replace('_icon_ui', ''), fill=(220, 220, 220))
    bg = Image.new('RGBA', big.size, (60, 64, 72, 255)); bg.alpha_composite(big); sheet.paste(bg.convert('RGB'), (x + 12, y + 20))
sheet.save(PREV / 'icons-v04.png')

manifest = {'version': 'textures-v0.4', 'targets': len(targets['targets']), 'files': {p.name: {'sha256': sha(p), 'size': list(Image.open(p).size)} for p in PROC.glob('*.png')}}
(ROOT / 'verification/processed.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps({'targets': manifest['targets'], 'files': len(manifest['files'])}))
