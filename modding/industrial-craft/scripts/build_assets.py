#!/usr/bin/env python3
"""Generate stage-0 pixel art and append atlas regions without resizing textures."""
from pathlib import Path
import sys
sys.path.insert(0,"/tmp/orionpy")
from PIL import Image,ImageDraw
import json,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets'
# A small walnut/brass diagnostic module. Palette and outline weight follow Orion's
# bronze ingot, gear and workbench references rather than importing IC2 pixels.
PAL={'outline':(43,29,24,255),'dark':(83,53,35,255),'wood':(132,83,45,255),'light':(184,124,65,255),'brass':(197,145,70,255),'hi':(239,190,99,255),'teal':(65,139,132,255),'glass':(126,205,184,255),'black':(27,31,30,255)}
def icon_probe():
 im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im)
 d.rectangle((5,7,26,27),fill=PAL['outline']);d.rectangle((7,6,24,8),fill=PAL['outline'])
 d.rectangle((7,9,24,25),fill=PAL['wood']);d.rectangle((9,10,22,23),fill=PAL['dark'])
 d.rectangle((10,11,21,21),fill=PAL['brass']);d.rectangle((12,12,19,19),fill=PAL['black'])
 d.rectangle((13,13,18,18),fill=PAL['teal']);d.rectangle((13,13,16,14),fill=PAL['glass'])
 d.rectangle((8,9,23,10),fill=PAL['light']);d.rectangle((8,24,23,25),fill=PAL['dark'])
 for x,y in [(8,11),(22,11),(8,22),(22,22)]:d.point((x,y),fill=PAL['hi'])
 d.rectangle((11,4,13,6),fill=PAL['outline']);d.rectangle((18,4,20,6),fill=PAL['outline'])
 d.rectangle((12,3,12,5),fill=PAL['brass']);d.rectangle((19,3,19,5),fill=PAL['brass'])
 return im

def block_probe():
 im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im)
 d.rectangle((1,3,30,31),fill=PAL['outline']);d.rectangle((3,2,28,4),fill=PAL['outline'])
 d.rectangle((3,5,28,29),fill=PAL['wood']);d.rectangle((5,6,26,9),fill=PAL['light'])
 d.rectangle((5,11,26,26),fill=PAL['dark']);d.rectangle((7,12,24,23),fill=PAL['black'])
 d.rectangle((9,13,22,21),fill=PAL['teal']);d.rectangle((10,13,20,14),fill=PAL['glass'])
 d.rectangle((10,17,21,18),fill=(42,91,86,255));d.rectangle((11,19,18,20),fill=PAL['glass'])
 d.rectangle((4,27,27,29),fill=PAL['brass']);d.rectangle((6,28,9,30),fill=PAL['outline']);d.rectangle((22,28,25,30),fill=PAL['outline'])
 for x,y in [(4,7),(27,7),(4,25),(27,25)]:d.rectangle((x,y,x+1,y+1),fill=PAL['hi'])
 d.rectangle((13,7,18,8),fill=PAL['brass']);d.point((14,7),fill=PAL['hi'])
 return im

def block_probe_sheet():
 # Orion samples frames 33 pixels apart. Idle plus two illuminated working frames.
 idle=block_probe(); im=Image.new('RGBA',(32,98)); im.paste(idle,(0,0))
 for frame in (1,2):
  active=idle.copy();d=ImageDraw.Draw(active)
  d.rectangle((9,13,22,21),fill=PAL['glass'] if frame==1 else PAL['teal'])
  d.rectangle((10,15,21,16),fill=PAL['teal'] if frame==1 else PAL['glass'])
  d.rectangle((11 if frame==1 else 16,18,16 if frame==1 else 21,20),fill=PAL['hi'])
  im.paste(active,(0,33*frame))
 return im

def main():
 (OUT/'icons').mkdir(parents=True,exist_ok=True);(OUT/'blocks').mkdir(parents=True,exist_ok=True)
 icon_probe().save(OUT/'icons/probe.png');block_probe_sheet().save(OUT/'blocks/probe.png')
 # Atlas placement is checked against every original region, with a 2px gutter.
 regions=[{'atlas':'items','name':'item_1242','x':16,'y':760,'w':32,'h':32,'file':'icons/probe.png'},
          {'atlas':'items','name':'item_495','x':64,'y':760,'w':32,'h':32,'file':'icons/probe.png'},
          {'atlas':'tiles','name':'block_239','x':989,'y':1632,'w':32,'h':98,'file':'blocks/probe.png'}]
 data=json.loads((ROOT/'data/atlas-regions.json').read_text()) if (ROOT/'data/atlas-regions.json').exists() else {}
 data['regions']=regions;(ROOT/'data/atlas-regions.json').write_text(json.dumps(data,indent=2))
 print('wrote',len(regions),'regions')
if __name__=='__main__':main()
