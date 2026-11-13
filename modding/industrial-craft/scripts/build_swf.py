#!/usr/bin/env python3
"""Build IC dev SWF from accepted v0.5 texture base.

Changes: two atlas images, their XML metadata, frame2 ABC hooks, appended mod ABC.
AIR stubs and verification bootstrap are deliberately not included.
"""
from pathlib import Path
import argparse,hashlib,json,struct,zlib,sys
sys.path.insert(0,'/tmp/orionpy')
from PIL import Image
from abc_utils import parse_tags,encode_tag
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def image_tag(tags,cid):
 t=next(t for t in tags if t['code'] in (20,36) and struct.unpack_from('<H',t['data'],0)[0]==cid)
 fmt=t['data'][2];w,h=struct.unpack_from('<HH',t['data'],3)
 if t['code']!=36 or fmt!=5:raise ValueError((cid,t['code'],fmt))
 raw=zlib.decompress(t['data'][7:]);stride=((w*4+3)//4)*4
 return t,raw,w,h,stride
def premul(im):
 out=bytearray()
 for r,g,b,a in im.convert('RGBA').getdata():
  if a==0:out.extend((0,0,0,0))
  elif a==255:out.extend((255,r,g,b))
  else:out.extend((a,(r*a+127)//255,(g*a+127)//255,(b*a+127)//255))
 return bytes(out)
def put(raw,stride,x,y,w,h,data):
 out=bytearray(raw)
 for j in range(h):out[(y+j)*stride+x*4:(y+j)*stride+(x+w)*4]=data[j*w*4:(j+1)*w*4]
 return bytes(out)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',default=str(ROOT.parent/'textures-v0.5/build/Orion.mod.swf'));ap.add_argument('--output',default=str(ROOT/'build/Orion.ic-dev.swf'));args=ap.parse_args()
 src=Path(args.input);out=Path(args.output);swf=src.read_bytes();body=zlib.decompress(swf[8:]);tags=parse_tags(body)
 regions=json.loads((ROOT/'data/atlas-regions.json').read_text())['regions']
 atlas_cid={'items':1476,'tiles':1646};xml_cid={'items':2045,'tiles':1987}
 replacements={};changed=[]
 for atlas,cid in atlas_cid.items():
  t,raw,w,h,stride=image_tag(tags,cid);new=raw;mask=bytearray(len(raw));rs=[r for r in regions if r['atlas']==atlas]
  for r in rs:
   im=Image.open(ROOT/'assets'/r['file']).convert('RGBA')
   if im.size!=(r['w'],r['h']):raise ValueError(r)
   data=premul(im);new=put(new,stride,r['x'],r['y'],r['w'],r['h'],data)
   for j in range(r['h']):
    s=(r['y']+j)*stride+r['x']*4;mask[s:s+r['w']*4]=b'\1'*(r['w']*4)
  if any(a!=b for i,(a,b) in enumerate(zip(raw,new)) if not mask[i]):raise ValueError('pixels outside regions')
  replacements[cid]=encode_tag(t['code'],t['data'][:7]+zlib.compress(new,9));changed.append({'kind':'atlas_image','char':cid,'regions':len(rs)})
  xt=next(t for t in tags if t['code']==87 and struct.unpack_from('<H',t['data'],0)[0]==xml_cid[atlas])
  xml=xt['data'][6:].decode('utf-8')
  for r in rs:
   if f'name="{r["name"]}"' in xml:raise ValueError(('duplicate region',r['name']))
   node=f'    <SubTexture name="{r["name"]}" x="{r["x"]}" y="{r["y"]}" width="{r["w"]}" height="{r["h"]}"/>\n'
   xml=xml.replace('</TextureAtlas>',node+'</TextureAtlas>')
  replacements[xml_cid[atlas]]=encode_tag(87,xt['data'][:6]+xml.encode());changed.append({'kind':'atlas_xml','char':xml_cid[atlas],'added':[r['name'] for r in rs]})
 hooked=(ROOT/'build/frame2-hooked.abc').read_bytes();mod=(ROOT/'build/IndustrialCraft.abc').read_bytes()
 parts=[];last=0;abc_inserted=False
 for t in tags:
  parts.append(body[last:t['offset']]);last=t['offset']+len(t['raw']);cid=struct.unpack_from('<H',t['data'],0)[0] if t['code'] in (20,36,87) and len(t['data'])>=2 else None
  if t['code']==82 and t['data'][4:].split(b'\0',1)[0]==b'frame2':parts.append(encode_tag(82,t['data'][:4]+b'frame2\0'+hooked));changed.append({'kind':'replace_abc','name':'frame2'})
  elif cid is not None and cid in replacements:parts.append(replacements[cid])
  else:parts.append(t['raw'])
  if t['code']==82 and t['data'][4:].split(b'\0',1)[0]==b'frame2' and not abc_inserted:
   parts.append(encode_tag(82,struct.pack('<I',0)+b'industrialcraft\0'+mod));abc_inserted=True;changed.append({'kind':'append_abc_after_frame2','name':'industrialcraft'})
 parts.append(body[last:]);nb=b''.join(parts);result=b'CWS'+swf[3:4]+struct.pack('<I',8+len(nb))+zlib.compress(nb,9);out.write_bytes(result)
 report={'input':str(src),'output':str(out),'input_sha256':sha(swf),'output_sha256':sha(result),'input_size':len(swf),'output_size':len(result),'changes':changed,'air_stubs':False,'test_give':False,'save_hooks':['World.saveAdditional_v1','World.loadAdditional_v1','EarthWorld.saveAdditional_v1','EarthWorld.loadAdditional_v1'],'content_hook':'GameProcess.initStatic'}
 (ROOT/'verification/swf-build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
