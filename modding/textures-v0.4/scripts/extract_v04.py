#!/usr/bin/env python3
import json, struct, zlib, hashlib, xml.etree.ElementTree as E, re
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
# Carry v0.3 terrain/tree targets by re-extracting originals; processing will copy/override.
for name,label in [('block_4','stone_block_4'),('block_14','dirt_block_14'),('block_18','grass_block_18'),('block_19','tallgrass_block_19'),('block_75','cobblestone_block_75'),('block_16','sand_block_16'),('block_17','clay_block_17'),('block_26','tree_trunk_26'),('block_28','leaves_block_28'),('block_29','wood_block_29')]+[(f'block_{i}',f'tree_branch_{i}') for i in [165,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186]]:
 atlas(1646,1987,name,label)
# New v0.4 blocks/walls
for name,label in [('block_44','workbench_block_44'),('block_45','furnace_off_block_45'),('block_46','furnace_on_block_46'),('block_47','furnace_part_block_47'),('block_50','bed_block_50'),('block_52','ladder_block_52'),('block_53','torch_block_53'),('block_54','small_torch_block_54'),('block_64','chair_block_64'),('block_65','table_block_65'),('block_114','wood_planks_block_114'),('wall_4','wall_stone_4'),('wall_5','wall_dirt_5'),('wall_6','wall_wood_6')]:
 atlas(1646,1987,name,label)
# Item atlas icons
item_map=[('item_259','stone_icon_atlas_259'),('item_269','dirt_icon_atlas_269'),('item_273','grass_icon_atlas_273'),('item_325','cobblestone_icon_atlas_325'),('item_271','sand_icon_atlas_271'),('item_272','clay_icon_atlas_272'),('item_281','leaves_icon_atlas_281'),('item_282','wood_icon_atlas_282'),('item_291','workbench_icon_atlas_291'),('item_292','furnace_icon_atlas_292'),('item_295','bed_icon_atlas_295'),('item_297','ladder_icon_atlas_297'),('item_298','torch_icon_atlas_298'),('item_299','small_torch_icon_atlas_299'),('item_309','chair_icon_atlas_309'),('item_310','table_icon_atlas_310'),('item_363','wood_planks_icon_atlas_363'),('item_4','wall_stone_icon_atlas_4'),('item_5','wall_dirt_icon_atlas_5'),('item_6','wall_wood_icon_atlas_6'),('item_1058','wood_pickaxe_icon_atlas_1058'),('item_1064','cudgel_icon_atlas_1064'),('item_1208','wooden_helmet_icon_atlas_1208'),('item_1209','wooden_chainmail_icon_atlas_1209'),('item_1215','wooden_greaves_icon_atlas_1215')]
for name,label in item_map: atlas(1476,2045,name,label)
# Torch in-hand animation frames (unique rects)
r=E.parse(REPO/'analysis/binary/binary-2045.xml').getroot()
for prefix in ['torch_anim_298','torch_anim_299']:
 seen=set()
 for e in r:
  n=e.get('name','')
  if n.startswith(prefix+'_'):
   key=(e.get('x'),e.get('y'),e.get('width'),e.get('height'))
   if key in seen: continue
   seen.add(key); atlas(1476,2045,n,f'{n}')
# UI icons
ui_map=[(1958,'stone_icon_ui_259'),(1143,'dirt_icon_ui_269'),(1207,'grass_icon_ui_273'),(2003,'cobblestone_icon_ui_325'),(1721,'leaves_icon_ui_281'),(1313,'wood_icon_ui_282'),(1516,'sand_icon_ui_271'),(1739,'clay_icon_ui_272'),(1915,'workbench_icon_ui_291'),(2129,'furnace_icon_ui_292'),(2119,'bed_icon_ui_295'),(2043,'ladder_icon_ui_297'),(1677,'torch_icon_ui_298'),(2097,'small_torch_icon_ui_299'),(1474,'chair_icon_ui_309'),(1674,'table_icon_ui_310'),(1428,'wood_planks_icon_ui_363'),(2091,'wall_stone_icon_ui_4'),(2117,'wall_dirt_icon_ui_5'),(1912,'wall_wood_icon_ui_6'),(1182,'wood_pickaxe_icon_ui_1058'),(1423,'cudgel_icon_ui_1064'),(1284,'wooden_helmet_icon_ui_1208'),(1418,'wooden_chainmail_icon_ui_1209'),(1218,'wooden_greaves_icon_ui_1215')]
for cid,label in ui_map: image(cid,label)
# Worn wooden armor frames in player atlas (unique rects per part)
r=E.parse(REPO/'analysis/binary/binary-2071.xml').getroot()
for prefix in ['male_armor_head_1208','female_armor_head_1208','male_armor_body_1209','female_armor_body_1209','male_armor_hand_1209','female_armor_hand_1209','male_armor_legs_1215','female_armor_legs_1215']:
 seen=set()
 for e in r:
  n=e.get('name','')
  if n.startswith(prefix+'_'):
   key=(e.get('x'),e.get('y'),e.get('width'),e.get('height'))
   if key in seen: continue
   seen.add(key); atlas(1586,2071,n,f'armor_{n}')
# Particles
for name in ['hit_dirt','hit_stone','hit_plant','hit_sand','hit_wood','hit_leaves','hit_clay']:
 atlas(1501,1582,name,name)
(ROOT/'verification/targets.json').write_text(json.dumps(manifest,indent=2))
print('targets',len(manifest['targets']))
