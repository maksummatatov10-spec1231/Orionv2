#!/usr/bin/env python3
import argparse, hashlib, json, struct, zlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def sha(b): return hashlib.sha256(b).hexdigest()
def parse_tags(body):
    n=(body[0]>>3)&31; p=(5+4*n+7)//8+4; out=[]
    while p+2<=len(body):
        v=struct.unpack_from('<H',body,p)[0]; code=v>>6; ln=v&63; h=2
        if ln==63: ln=struct.unpack_from('<I',body,p+2)[0]; h=6
        e=p+h+ln
        if e>len(body): raise ValueError('truncated tag')
        out.append({'offset':p,'header_len':h,'code':code,'length':ln,'data':body[p+h:e],'raw':body[p:e]})
        if code==0: break
        p=e
    return out

def image_tag(tags,cid):
    hits=[t for t in tags if t['code'] in (20,36) and len(t['data'])>=7 and struct.unpack_from('<H',t['data'],0)[0]==cid]
    if len(hits)!=1: raise ValueError((cid,len(hits)))
    t=hits[0]; fmt=t['data'][2]; w,h=struct.unpack_from('<HH',t['data'],3)
    if t['code']!=36 or fmt!=5: raise ValueError((cid,t['code'],fmt))
    raw=zlib.decompress(t['data'][7:]); stride=((w*4+3)//4)*4
    if len(raw)!=stride*h: raise ValueError((cid,len(raw),stride*h))
    return t,raw,w,h,stride

def premul_rgba(im):
    im=im.convert('RGBA'); out=bytearray()
    for r,g,b,a in im.getdata():
        if a==0: out.extend((0,0,0,0))
        elif a==255: out.extend((255,r,g,b))
        else: out.extend((a,(r*a+127)//255,(g*a+127)//255,(b*a+127)//255))
    return bytes(out)

def rect(raw,stride,x,y,w,h):
    return b''.join(raw[(y+j)*stride+x*4:(y+j)*stride+(x+w)*4] for j in range(h))

def put_rect(raw,stride,x,y,w,h,data):
    if len(data)!=w*h*4: raise ValueError('rect data size')
    out=bytearray(raw)
    for j in range(h):
        d=(y+j)*stride+x*4; s=j*w*4; out[d:d+w*4]=data[s:s+w*4]
    return bytes(out)

def encode_tag(code,data):
    if len(data)>=63: return struct.pack('<HI',(code<<6)|63,len(data))+data
    return struct.pack('<H',(code<<6)|len(data))+data

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--output',required=True); args=ap.parse_args()
    inp=Path(args.input); out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    swf=inp.read_bytes()
    if swf[:3]!=b'CWS': raise ValueError('expected CWS')
    body=zlib.decompress(swf[8:])
    if struct.unpack_from('<I',swf,4)[0]!=8+len(body): raise ValueError('bad length')
    tags=parse_tags(body)
    targets=json.loads((ROOT/'verification/targets.json').read_text())['targets']
    # group atlas rects
    atlases={}
    images=[]
    for t in targets:
        proc=ROOT/'processed'/f"{t['label']}.png"
        if not proc.exists(): raise ValueError(proc)
        if t['kind']=='atlas_rect':
            atlases.setdefault(t['atlas_char'],[]).append((t,proc))
        elif t['kind']=='image': images.append((t,proc))
        else: raise ValueError(t['kind'])
    new_tags={}; reports=[]; masks={}
    for cid,items in atlases.items():
        tag,raw,w,h,stride=image_tag(tags,cid); mask=bytearray(len(raw)); new=raw
        for t,proc in items:
            im=Image.open(proc).convert('RGBA')
            if im.size!=(t['w'],t['h']): raise ValueError((proc,im.size,t['w'],t['h']))
            data=premul_rgba(im)
            new=put_rect(new,stride,t['x'],t['y'],t['w'],t['h'],data)
            for j in range(t['h']):
                s=(t['y']+j)*stride+t['x']*4; mask[s:s+t['w']*4]=b'\x01'*(t['w']*4)
            reports.append({'label':t['label'],'kind':'atlas_rect','atlas_char':cid,'region':t['region'],'x':t['x'],'y':t['y'],'w':t['w'],'h':t['h'],'processed_sha256':sha(proc.read_bytes()),'alpha_extrema':im.getchannel('A').getextrema()})
        changed=sum(1 for i,(a,b) in enumerate(zip(raw,new)) if a!=b and not mask[i])
        if changed: raise ValueError((cid,'changed outside targets',changed))
        masks[cid]=(raw,new,mask)
        new_tags[cid]=encode_tag(tag['code'],tag['data'][:7]+zlib.compress(new,9))
    for t,proc in images:
        cid=t['char']; tag,raw,w,h,stride=image_tag(tags,cid)
        im=Image.open(proc).convert('RGBA')
        if im.size!=(w,h): raise ValueError((proc,im.size,w,h))
        new=premul_rgba(im)
        if len(new)!=len(raw): raise ValueError((cid,len(new),len(raw)))
        new_tags[cid]=encode_tag(tag['code'],tag['data'][:7]+zlib.compress(new,9))
        reports.append({'label':t['label'],'kind':'image','char':cid,'w':w,'h':h,'processed_sha256':sha(proc.read_bytes()),'alpha_extrema':im.getchannel('A').getextrema()})
    # rebuild body
    parts=[]; last=0; replaced=0
    for tag in tags:
        parts.append(body[last:tag['offset']]); last=tag['offset']+len(tag['raw'])
        cid=struct.unpack_from('<H',tag['data'],0)[0] if tag['code'] in (20,36) and len(tag['data'])>=2 else None
        if cid in new_tags: parts.append(new_tags[cid]); replaced+=1
        else: parts.append(tag['raw'])
    parts.append(body[last:]); newbody=b''.join(parts)
    newswf=b'CWS'+swf[3:4]+struct.pack('<I',8+len(newbody))+zlib.compress(newbody,9)
    out.write_bytes(newswf)
    # verify output
    ob=zlib.decompress(newswf[8:]); ot=parse_tags(ob)
    if len(ot)!=len(tags): raise ValueError('tag count changed')
    changed_ids=set(new_tags)
    other_identical=True
    for a,b in zip(tags,ot):
        cid=struct.unpack_from('<H',a['data'],0)[0] if a['code'] in (20,36) and len(a['data'])>=2 else None
        if cid in changed_ids:
            if a['code']!=b['code']: other_identical=False
        elif a['raw']!=b['raw']: other_identical=False
    exact=[]
    for cid,(old,new,mask) in masks.items():
        tag,oraw,w,h,stride=image_tag(ot,cid)
        outside=all(a==b for i,(a,b) in enumerate(zip(old,oraw)) if not mask[i])
        if not outside: raise ValueError((cid,'outside changed in output'))
        for t,proc in atlases[cid]:
            want=premul_rgba(Image.open(proc)); got=rect(oraw,stride,t['x'],t['y'],t['w'],t['h'])
            exact.append({'label':t['label'],'premultiplied_exact':got==want})
            if got!=want: raise ValueError((t['label'],'output rect mismatch'))
    for t,proc in images:
        tag,oraw,w,h,stride=image_tag(ot,t['char'])
        want=premul_rgba(Image.open(proc))
        exact.append({'label':t['label'],'premultiplied_exact':oraw==want})
        if oraw!=want: raise ValueError((t['label'],'output image mismatch'))
    report={'input':str(inp),'output':str(out),'input_sha256':sha(swf),'output_sha256':sha(newswf),'input_size':len(swf),'output_size':len(newswf),'tag_count':len(tags),'replaced_image_tags':replaced,'all_other_tags_identical':other_identical,'targets':reports,'output_exact':exact,'method':'direct DefineBitsLossless2 format-5 replacement; opaque and premultiplied-alpha exact; no FFDec re-encode'}
    if not other_identical: raise ValueError('other tags changed')
    (ROOT/'verification/swf-build.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
