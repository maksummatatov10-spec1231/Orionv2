#!/usr/bin/env python3
import json, struct, zlib, hashlib, xml.etree.ElementTree as E
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]; REPO=ROOT.parents[1]
SWF=Path('/tmp/orion-work/Orion Sandbox Enhanced/Orion.swf')
OUT=ROOT/'input'; OUT.mkdir(exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
def tags(body):
 n=(body[0]>>3)&31; p=(5+4*n+7)//8+4; out=[]
 while p+2<=len(body):
  v=struct.unpack_from('<H',body,p)[0]; code=v>>6; ln=v&63; h=2
  if ln==63: ln=struct.unpack_from('<I',body,p+2)[0]; h=6
  e=p+h+ln; out.append((code,body[p+h:e])); p=e
  if code==0: break
 return out
def lossless(data):
 fmt=data[2]; w,h=struct.unpack_from('<HH',data,3); assert fmt==5
 raw=zlib.decompress(data[7:]); stride=((w*4+3)//4)*4
 im=Image.new('RGBA',(w,h)); px=im.load()
 for y in range(h):
  for x in range(w):
   a,r,g,b=raw[y*stride+x*4:y*stride+x*4+4]
   px[x,y]=(0,0,0,0) if a==0 else (min(255,round(r*255/a)),min(255,round(g*255/a)),min(255,round(b*255/a)),a)
 return im
swf=SWF.read_bytes(); ts=tags(zlib.decompress(swf[8:])); byid={}
for code,data in ts:
 if code in (20,36) and len(data)>=7: byid[struct.unpack_from('<H',data,0)[0]]=(code,data)
manifest={'source_swf_sha256':sha(swf),'targets':[]}
def atlas(cid,xml,name,label):
 im=lossless(byid[cid][1]); r=E.parse(REPO/'analysis/binary'/f'binary-{xml}.xml').getroot()
 e=next(e for e in r if e.get('name')==name); x,y,w,h=map(int,(e.get('x'),e.get('y'),e.get('width'),e.get('height')))
 c=im.crop((x,y,x+w,y+h)); p=OUT/f'{label}.png'; c.save(p)
 manifest['targets'].append({'kind':'atlas_rect','label':label,'atlas_char':cid,'xml_char':xml,'region':name,'x':x,'y':y,'w':w,'h':h,'path':str(p),'sha256':sha(p.read_bytes()),'alpha_extrema':c.getchannel('A').getextrema()})
 return c
def image(cid,label):
 im=lossless(byid[cid][1]); p=OUT/f'{label}.png'; im.save(p)
 manifest['targets'].append({'kind':'image','label':label,'char':cid,'tag_code':byid[cid][0],'w':im.width,'h':im.height,'path':str(p),'sha256':sha(p.read_bytes()),'alpha_extrema':im.getchannel('A').getextrema()})
 return im
# core terrain
for name,label in [('block_4','stone_block_4'),('block_14','dirt_block_14'),('block_18','grass_block_18'),('block_19','tallgrass_block_19'),('block_75','cobblestone_block_75'),('block_16','sand_block_16'),('block_167','red_granite_block_167')]: atlas(1646,1987,name,label)
# tree parts
for name,label in [('block_26','tree_trunk_26'),('block_28','leaves_block_28'),('block_29','wood_block_29')]+[(f'block_{i}',f'tree_branch_{i}') for i in [165,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186]]: atlas(1646,1987,name,label)
# item atlas icons
for name,label in [('item_259','stone_icon_atlas_259'),('item_269','dirt_icon_atlas_269'),('item_273','grass_icon_atlas_273'),('item_325','cobblestone_icon_atlas_325'),('item_271','sand_icon_atlas_271'),('item_421','red_granite_icon_atlas_421'),('item_281','leaves_icon_atlas_281'),('item_282','wood_icon_atlas_282')]: atlas(1476,2045,name,label)
# UI icons
for cid,label in [(1958,'stone_icon_ui_259'),(1143,'dirt_icon_ui_269'),(1207,'grass_icon_ui_273'),(2003,'cobblestone_icon_ui_325'),(1198,'seedling_icon_ui_280'),(1721,'leaves_icon_ui_281'),(1313,'wood_icon_ui_282'),(1289,'red_granite_icon_ui_421')]: image(cid,label)
# sand UI char discovered by grep fallback
import re
for itemid,label in [(271,'sand_icon_ui_271')]:
 f=REPO/'analysis/as3/assets'/f'Images_ITEM_{itemid}_CLASS.as'
 if f.exists():
  m=re.search(r'/(\d+)_assets',f.read_text())
  if m: image(int(m.group(1)),label)
# effects
for name in ['hit_dirt','hit_stone','hit_plant','hit_sand','hit_wood','hit_leaves','hit_bronze']:
 try: atlas(1501,1582,name,name)
 except StopIteration: pass
(ROOT/'verification/targets.json').write_text(json.dumps(manifest,indent=2))
# preview terrain candidates
rows=[('STONE','stone_block_4'),('DIRT','dirt_block_14'),('SAND','sand_block_16'),('RED GRANITE / BRONZE ORE','red_granite_block_167'),('LEAVES','leaves_block_28'),('WOOD','wood_block_29')]
scale=6; W=131*scale+160; H=len(rows)*(32*scale+30)+10
sheet=Image.new('RGB',(W,H),(22,24,28)); d=ImageDraw.Draw(sheet); y=10
for label,name in rows:
 im=Image.open(OUT/f'{name}.png').convert('RGBA'); big=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
 d.text((8,y+80),label,fill='white'); sheet.paste(big,(150,y),big); y+=32*scale+30
sheet.save(ROOT/'preview/original-terrain-candidates.png')
# tree trunk/branch preview
tr=Image.open(OUT/'tree_trunk_26.png').convert('RGBA'); tr.resize((tr.width*4,tr.height*4),Image.Resampling.NEAREST).save(ROOT/'preview/original-tree-trunk.png')
for n in [168,170,171,172]:
 im=Image.open(OUT/f'tree_branch_{n}.png').convert('RGBA'); im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST).save(ROOT/'preview'/f'original-tree-branch-{n}.png')
print('targets',len(manifest['targets']))
for t in manifest['targets']: print(t['label'],t.get('w'),t.get('h'),t.get('alpha_extrema'))
