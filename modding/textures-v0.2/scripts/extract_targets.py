#!/usr/bin/env python3
import json, struct, zlib, hashlib
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SWF=Path('/tmp/orion-work/Orion Sandbox Enhanced/Orion.swf')
OUT=ROOT/'input'; OUT.mkdir(parents=True,exist_ok=True)

def sha(b): return hashlib.sha256(b).hexdigest()
def tags(body):
    n=(body[0]>>3)&31; p=(5+4*n+7)//8+4; out=[]
    while p+2<=len(body):
        v=struct.unpack_from('<H',body,p)[0]; code=v>>6; ln=v&63; h=2
        if ln==63: ln=struct.unpack_from('<I',body,p+2)[0]; h=6
        e=p+h+ln; out.append((code,body[p+h:e],p,h)); p=e
        if code==0: break
    return out

def lossless(data):
    fmt=data[2]; w,h=struct.unpack_from('<HH',data,3)
    if fmt!=5: raise ValueError(fmt)
    raw=zlib.decompress(data[7:]); stride=((w*4+3)//4)*4
    im=Image.new('RGBA',(w,h)); px=im.load()
    for y in range(h):
        for x in range(w):
            a,r,g,b=raw[y*stride+x*4:y*stride+x*4+4]
            if a==0: px[x,y]=(0,0,0,0)
            else: px[x,y]=(min(255,round(r*255/a)),min(255,round(g*255/a)),min(255,round(b*255/a)),a)
    return im,raw

swf=SWF.read_bytes(); body=zlib.decompress(swf[8:]); ts=tags(body)
byid={}
for code,data,p,h in ts:
    if code in (20,36) and len(data)>=7:
        cid=struct.unpack_from('<H',data,0)[0]
        byid[cid]=(code,data)
manifest={'source_swf_sha256':sha(swf),'targets':[]}

def save_atlas(cid,xml,name,label):
    code,data=byid[cid]; im,raw=lossless(data)
    import xml.etree.ElementTree as E
    r=E.parse(ROOT.parent.parent/'analysis/binary'/f'binary-{xml}.xml').getroot()
    e=next(e for e in r if e.get('name')==name)
    x,y,w,h=map(int,(e.get('x'),e.get('y'),e.get('width'),e.get('height')))
    crop=im.crop((x,y,x+w,y+h)); path=OUT/f'{label}.png'; crop.save(path)
    alpha=crop.getchannel('A'); manifest['targets'].append({'kind':'atlas_rect','label':label,'atlas_char':cid,'xml_char':xml,'region':name,'x':x,'y':y,'w':w,'h':h,'path':str(path),'sha256':sha(path.read_bytes()),'alpha_extrema':alpha.getextrema()})
    return crop

def save_image(cid,label):
    code,data=byid[cid]; im,raw=lossless(data); path=OUT/f'{label}.png'; im.save(path)
    alpha=im.getchannel('A'); manifest['targets'].append({'kind':'image','label':label,'char':cid,'tag_code':code,'w':im.width,'h':im.height,'path':str(path),'sha256':sha(path.read_bytes()),'alpha_extrema':alpha.getextrema()})
    return im

tiles={}
for name,label in [('block_4','stone_block_4'),('block_14','dirt_block_14'),('block_18','grass_block_18'),('block_19','tallgrass_block_19'),('block_75','cobblestone_block_75')]:
    tiles[label]=save_atlas(1646,1987,name,label)
items={}
for name,label in [('item_259','stone_icon_atlas_259'),('item_269','dirt_icon_atlas_269'),('item_273','grass_icon_atlas_273'),('item_325','cobblestone_icon_atlas_325')]:
    items[label]=save_atlas(1476,2045,name,label)
icons={}
for cid,label in [(1958,'stone_icon_ui_259'),(1143,'dirt_icon_ui_269'),(1207,'grass_icon_ui_273'),(2003,'cobblestone_icon_ui_325')]:
    icons[label]=save_image(cid,label)
effects={}
for name,label in [('hit_dirt','hit_dirt'),('hit_stone','hit_stone'),('hit_plant','hit_plant')]:
    effects[label]=save_atlas(1501,1582,name,label)
# contact sheet
rows=[('STONE',tiles['stone_block_4']),('DIRT',tiles['dirt_block_14']),('GRASS',tiles['grass_block_18']),('TALL GRASS',tiles['tallgrass_block_19']),('COBBLE',tiles['cobblestone_block_75'])]
scale=6; W=max(im.width for _,im in rows)*scale+180; H=sum(im.height*scale+34 for _,im in rows)+20
sheet=Image.new('RGB',(W,H),(22,24,28)); d=ImageDraw.Draw(sheet); y=10
for label,im in rows:
    d.text((8,y+im.height*scale//2),label,fill='white'); big=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST); sheet.paste(big,(170,y),big if big.mode=='RGBA' else None); y+=im.height*scale+34
sheet.save(ROOT/'preview/original-targets.png')
# icons/effects sheet
small=Image.new('RGB',(760,260),(22,24,28)); d=ImageDraw.Draw(small); x=10
for label,im in list(items.items())+list(icons.items())+list(effects.items()):
    s=8 if im.width<=16 else 6; big=im.resize((im.width*s,im.height*s),Image.Resampling.NEAREST); d.text((x,8),label,fill='white'); small.paste(big,(x,30),big if big.mode=='RGBA' else None); x+=big.width+18
small.save(ROOT/'preview/original-icons-effects.png')
(ROOT/'verification/targets.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
