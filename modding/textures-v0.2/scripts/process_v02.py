#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import json, hashlib, random, math
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'input'; GEN=ROOT/'generated'; PROC=ROOT/'processed'; PREV=ROOT/'preview'
PROC.mkdir(exist_ok=True); PREV.mkdir(exist_ok=True)
OFFS=(0,33,66,99); GUT=(32,65,98)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def native(master, colors=28, sat=1.06, con=1.06):
    im=Image.open(master).convert('RGB').resize((32,32),Image.Resampling.LANCZOS)
    im=ImageEnhance.Color(im).enhance(sat); im=ImageEnhance.Contrast(im).enhance(con)
    im=im.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
    return im

def bevel(im, strength=0.16, highlight=5):
    out=im.copy(); px=out.load()
    for y in range(32):
        for x in range(32):
            d=min(x,y,31-x,31-y)
            f=1.0
            if d==0: f=1-strength
            elif d==1: f=1-strength*0.45
            r,g,b=px[x,y]
            if x+y<5: r+=highlight; g+=highlight; b+=highlight
            if x>26 and y>26: r-=4; g-=4; b-=4
            px[x,y]=(max(0,min(255,round(r*f))),max(0,min(255,round(g*f))),max(0,min(255,round(b*f))))
    return out

def variant(base, i, kind):
    im=base.copy()
    if kind in ('dirt','stone','cobble'):
        if i in (1,3): im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if i in (2,3): im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    else:
        if i%2: im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    rnd=random.Random(20261112+i*97+hash(kind)%1000)
    px=im.load()
    for _ in range(10):
        x=rnd.randrange(2,30); y=rnd.randrange(7 if kind=='grass' else 2,30)
        r,g,b=px[x,y]
        if kind=='grass' and y<7 and g>r*1.1: continue
        d=rnd.choice((-8,-4,4,8))
        px[x,y]=(max(0,min(255,r+d)),max(0,min(255,g+d)),max(0,min(255,b+d)))
    if i==2: im=ImageEnhance.Brightness(im).enhance(1.03)
    if i==3: im=ImageEnhance.Brightness(im).enhance(0.98)
    return im

def strip(name, base, kind):
    orig=Image.open(IN/f'{name}.png').convert('RGBA')
    out=orig.copy()
    for x in GUT:
        for y in range(32): out.putpixel((x,y),orig.getpixel((x,y)))
    vars=[]
    for i,off in enumerate(OFFS):
        v=variant(base,i,kind); vars.append(v); out.paste(v.convert('RGBA'),(off,0))
    path=PROC/f'{name}.png'; out.save(path)
    out.resize((131*8,32*8),Image.Resampling.NEAREST).save(PREV/f'{name}-8x.png')
    return path,vars

def key_magenta(path):
    im=Image.open(path).convert('RGB')
    rgba=Image.new('RGBA',im.size); src=im.load(); dst=rgba.load()
    for y in range(im.height):
        for x in range(im.width):
            r,g,b=src[x,y]
            # pure magenta and magenta-dominant blend pixels are background
            if r>140 and b>140 and g<120 and r>g*1.25 and b>g*1.25:
                dst[x,y]=(0,0,0,0)
            else:
                # despill magenta on edge pixels
                if r>g and b>g:
                    r=g; b=g
                elif b>g*0.65 and r>g*0.65:
                    b=min(b,g//2); r=min(r,g)
                dst[x,y]=(r,g,b,255)
    # downsample premultiplied to avoid halos
    prem=Image.new('RGBA',im.size); ps=rgba.load(); pd=prem.load()
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a=ps[x,y]; pd[x,y]=(r*a//255,g*a//255,b*a//255,a)
    small=prem.resize((32,32),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(32,32)); os_=small.load(); od=out.load()
    for y in range(32):
        for x in range(32):
            r,g,b,a=os_[x,y]
            if a==0: od[x,y]=(0,0,0,0)
            else: od[x,y]=(min(255,round(r*255/a)),min(255,round(g*255/a)),min(255,round(b*255/a)),a)
    # keep alpha crisp-ish, remove tiny isolated fog
    a=out.getchannel('A').point(lambda v: 0 if v<24 else v)
    out.putalpha(a)
    return out

def tallgrass_strip():
    orig=Image.open(IN/'tallgrass_block_19.png').convert('RGBA')
    master=key_magenta(GEN/'tallgrass_master_v2.png')
    # fit into a 32x32 tile, bottom aligned, max visible height 20px
    bbox=master.getbbox()
    if bbox:
        crop=master.crop(bbox)
        max_h=20; max_w=28
        scale=min(max_w/crop.width, max_h/crop.height, 1.0)
        nw=max(1,round(crop.width*scale)); nh=max(1,round(crop.height*scale))
        crop=crop.resize((nw,nh),Image.Resampling.NEAREST)
        tile=Image.new('RGBA',(32,32),(0,0,0,0)); tile.paste(crop,((32-nw)//2,32-nh),crop)
    else: tile=master
    out=orig.copy()
    # Tall-grass gutters are not sampled by the game; keep them clean/transparent.
    for x in GUT:
        for y in range(32): out.putpixel((x,y),(0,0,0,0))
    vars=[]
    for i,off in enumerate(OFFS):
        v=tile.copy()
        if i%2: v=v.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if i==2: v=ImageEnhance.Brightness(v).enhance(1.05)
        if i==3: v=ImageEnhance.Brightness(v).enhance(0.96)
        vars.append(v); out.paste(v,(off,0))
    path=PROC/'tallgrass_block_19.png'; out.save(path)
    # preview on dirt background
    bg=Image.new('RGBA',(131,32),(0,0,0,0)); dirt=Image.open(PROC/'dirt_block_14.png').convert('RGBA') if (PROC/'dirt_block_14.png').exists() else Image.open(IN/'dirt_block_14.png').convert('RGBA')
    bg.alpha_composite(dirt); bg.alpha_composite(out)
    bg.convert('RGB').resize((131*8,32*8),Image.Resampling.NEAREST).save(PREV/'tallgrass_block_19-8x.png')
    return path,vars

dirt_base=bevel(native(GEN/'dirt_master_v3.png',30,1.07,1.07),0.14,4)
grass_base=bevel(native(GEN/'grass_master_v4.png',30,1.08,1.06),0.12,3)
stone_base=bevel(native(GEN/'stone_master_v2.png',26,1.03,1.08),0.15,4)
cobble_base=bevel(native(GEN/'cobblestone_master_v2.png',26,1.02,1.06),0.14,3)
# tone grass top line slightly less neon, keep sunlit
px=grass_base.load()
for x in range(32):
    r,g,b=px[x,0]
    if g>200 and r>150: px[x,0]=(min(r,120),min(g,235),min(b,40))

paths={}
paths['dirt'],dirt_vars=strip('dirt_block_14',dirt_base,'dirt')
paths['grass'],grass_vars=strip('grass_block_18',grass_base,'grass')
paths['stone'],stone_vars=strip('stone_block_4',stone_base,'stone')
paths['cobble'],cobble_vars=strip('cobblestone_block_75',cobble_base,'cobble')
paths['tallgrass'],tall_vars=tallgrass_strip()

# icons: atlas 16x16 opaque from variant0; UI 32x32 preserve original alpha/bbox
icon_map=[('dirt','dirt_block_14','dirt_icon_atlas_269','dirt_icon_ui_269'),
          ('grass','grass_block_18','grass_icon_atlas_273','grass_icon_ui_273'),
          ('stone','stone_block_4','stone_icon_atlas_259','stone_icon_ui_259'),
          ('cobble','cobblestone_block_75','cobblestone_icon_atlas_325','cobblestone_icon_ui_325')]
for key,block,atlas_name,ui_name in icon_map:
    tile=Image.open(PROC/f'{block}.png').convert('RGBA').crop((0,0,32,32))
    atlas=tile.resize((16,16),Image.Resampling.LANCZOS).convert('RGB')
    atlas.save(PROC/f'{atlas_name}.png')
    ui_orig=Image.open(IN/f'{ui_name}.png').convert('RGBA'); alpha=ui_orig.getchannel('A'); bbox=alpha.getbbox()
    ui=Image.new('RGBA',(32,32),(0,0,0,0))
    if bbox:
        w=bbox[2]-bbox[0]; h=bbox[3]-bbox[1]
        content=tile.resize((w,h),Image.Resampling.LANCZOS)
        ui.paste(content,(bbox[0],bbox[1]))
    ui.putalpha(alpha)
    ui.save(PROC/f'{ui_name}.png')

# particles: preserve original alpha exactly, recolor with material palette
def palette(im):
    small=im.convert('RGB').resize((16,16))
    q=small.quantize(colors=12,dither=Image.Dither.NONE).convert('RGB')
    return sorted(set(q.getdata()))
def particle(name, pal, seed):
    orig=Image.open(IN/f'{name}.png').convert('RGBA'); out=orig.copy(); px=out.load(); rnd=random.Random(seed)
    for y in range(orig.height):
        for x in range(orig.width):
            a=orig.getpixel((x,y))[3]
            if a==0: px[x,y]=(0,0,0,0); continue
            c=pal[rnd.randrange(len(pal))]
            if x+y<4: c=tuple(min(255,v+28) for v in c)
            if x>orig.width-3 and y>orig.height-3: c=tuple(max(0,v-24) for v in c)
            px[x,y]=(*c,a)
    out.save(PROC/f'{name}.png'); return out
particle('hit_dirt',palette(dirt_base),14)
particle('hit_stone',palette(stone_base),4)
plant_pal=[c for c in palette(grass_base) if c[1]>c[0]*1.10 and c[1]>c[2]*1.10]
if len(plant_pal)<4:
    plant_pal=[(0,120,24),(0,170,36),(24,205,52),(140,225,70),(0,86,20),(70,235,90)]
particle('hit_plant',plant_pal,19)

# preview sheet: original / v0.1 / v0.2 native strips 6x
rows=[('STONE','stone_block_4'),('DIRT','dirt_block_14'),('GRASS','grass_block_18'),('TALL GRASS','tallgrass_block_19'),('COBBLE','cobblestone_block_75')]
scale=6; w=131*scale; h=32*scale; gap=24; label=22
sheet=Image.new('RGB',(w*3+gap*2,(h+label)*len(rows)+gap*(len(rows)-1)+20),(18,20,24)); d=ImageDraw.Draw(sheet)
v01=ROOT.parent/'textures-v0.1/processed'
for row,(title,name) in enumerate(rows):
    y=row*(h+label+gap)+label+10
    imgs=[IN/f'{name}.png', v01/f'{name}.png' if (v01/f'{name}.png').exists() else IN/f'{name}.png', PROC/f'{name}.png']
    for col,p in enumerate(imgs):
        x=col*(w+gap)
        im=Image.open(p).convert('RGBA')
        if name=='tallgrass_block_19':
            bg=Image.new('RGBA',im.size,(40,32,20,255)); bg.alpha_composite(im); im=bg
        im=im.convert('RGB').resize((w,h),Image.Resampling.NEAREST)
        d.text((x,y-18),f'{title} '+['ORIGINAL','v0.1','v0.2'][col],fill=(220,220,220) if col<2 else (140,255,170))
        sheet.paste(im,(x,y))
sheet.save(PREV/'before-after-v02.png')
# icons/particles preview
small=Image.new('RGB',(900,320),(18,20,24)); d=ImageDraw.Draw(small); x=10
for label in ['dirt_icon_atlas_269','grass_icon_atlas_273','stone_icon_atlas_259','cobblestone_icon_atlas_325','dirt_icon_ui_269','grass_icon_ui_273','stone_icon_ui_259','cobblestone_icon_ui_325','hit_dirt','hit_stone','hit_plant']:
    im=Image.open(PROC/f'{label}.png').convert('RGBA'); s=8 if im.width<=16 else 6
    big=im.resize((im.width*s,im.height*s),Image.Resampling.NEAREST)
    d.text((x,8),label,fill='white'); small.paste(big,(x,30),big); x+=big.width+18
small.save(PREV/'icons-particles-v02.png')
manifest={'version':'textures-v0.2','files':{p.name:{'sha256':sha(p),'size':list(Image.open(p).size)} for p in PROC.glob('*.png')}}
(ROOT/'verification/processed.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
