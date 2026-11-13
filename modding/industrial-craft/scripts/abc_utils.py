#!/usr/bin/env python3
"""Small, lossless AVM2 ABC reader and method-body patcher.

Only the structures required by the Orion integration are interpreted. Constant-pool
entries and untouched method bodies are preserved byte-for-byte. The parser is checked
against the complete frame before any patch is written.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import struct

class Reader:
    def __init__(self, data: bytes): self.data=data; self.pos=0
    def u8(self):
        v=self.data[self.pos]; self.pos+=1; return v
    def u30(self):
        result=0
        for shift in range(0,35,7):
            b=self.u8(); result |= (b & 127) << shift
            if not b & 128: return result
        raise ValueError('invalid u30')
    def u32(self):
        v=self.u30();return v & 0xffffffff
    def s32(self):
        v=self.u32();return v-0x100000000 if v>=0x80000000 else v
    def take(self,n):
        v=self.data[self.pos:self.pos+n]
        if len(v)!=n: raise ValueError('truncated ABC')
        self.pos+=n; return v

def u30(n:int)->bytes:
    if n<0 or n>=1<<30: raise ValueError(n)
    out=bytearray()
    while True:
        b=n&127; n>>=7; out.append(b|(128 if n else 0))
        if not n:return bytes(out)

@dataclass
class Trait:
    name:int; kind:int; data:tuple; metadata:list

@dataclass
class Body:
    method:int; max_stack:int; locals:int; init_scope:int; max_scope:int
    code:bytes; exceptions:list; traits:list; start:int; end:int

class ABC:
    def __init__(self,data:bytes):
        self.original=data; r=Reader(data); self.minor,self.major=struct.unpack('<HH',r.take(4))
        self.pools={}; self.pool_ranges={}
        for kind in ('int','uint'):
            start=r.pos; n=r.u30(); vals=[0] if n else []
            for _ in range(max(0,n-1)): vals.append(r.s32() if kind=='int' else r.u32())
            self.pools[kind]=vals; self.pool_ranges[kind]=(start,r.pos)
        start=r.pos; n=r.u30(); vals=[0.0]
        for _ in range(max(0,n-1)): vals.append(struct.unpack('<d',r.take(8))[0])
        self.pools['double']=vals; self.pool_ranges['double']=(start,r.pos)
        start=r.pos; n=r.u30(); vals=['']
        for _ in range(max(0,n-1)): vals.append(r.take(r.u30()).decode('utf-8'))
        self.pools['string']=vals; self.pool_ranges['string']=(start,r.pos)
        start=r.pos; n=r.u30(); vals=[None]
        for _ in range(max(0,n-1)):
            kind=r.u8(); vals.append((kind,r.u30()))
        self.pools['namespace']=vals; self.pool_ranges['namespace']=(start,r.pos)
        start=r.pos; n=r.u30(); vals=[[]]
        for _ in range(max(0,n-1)): vals.append([r.u30() for _ in range(r.u30())])
        self.pools['ns_set']=vals; self.pool_ranges['ns_set']=(start,r.pos)
        start=r.pos; n=r.u30(); vals=[None]
        for _ in range(max(0,n-1)):
            kind=r.u8()
            if kind in (7,13): v=(kind,r.u30(),r.u30())
            elif kind in (15,16): v=(kind,r.u30())
            elif kind in (17,18): v=(kind,)
            elif kind in (9,14): v=(kind,r.u30(),r.u30())
            elif kind in (27,28): v=(kind,r.u30())
            elif kind==29:
                q=r.u30(); v=(kind,q,[r.u30() for _ in range(r.u30())])
            else: raise ValueError(f'multiname kind {kind} at {r.pos}')
            vals.append(v)
        self.pools['multiname']=vals; self.pool_ranges['multiname']=(start,r.pos)
        n=r.u30(); self.methods=[]
        for _ in range(n):
            pc=r.u30(); ret=r.u30(); params=[r.u30() for _ in range(pc)]; name=r.u30(); flags=r.u8(); opts=[]
            if flags&8:
                for _ in range(r.u30()):
                    vi=r.u30(); vk=r.u8(); opts.append((vi,vk))
            if flags&128:
                for _ in range(pc):r.u30()
            self.methods.append({'params':params,'ret':ret,'name':name,'flags':flags,'options':opts})
        n=r.u30(); self.metadata=[]
        for _ in range(n):
            name=r.u30(); items=[]
            for _ in range(r.u30()): items.append((r.u30(),r.u30()))
            self.metadata.append((name,items))
        self.instances=[]; n=r.u30()
        for _ in range(n):
            name=r.u30(); sup=r.u30(); flags=r.u8()
            if flags&8:r.u30()
            interfaces=[r.u30() for _ in range(r.u30())]; iinit=r.u30(); traits=self._traits(r)
            self.instances.append({'name':name,'super':sup,'flags':flags,'interfaces':interfaces,'iinit':iinit,'traits':traits})
        self.classes=[]
        for _ in range(n): self.classes.append({'cinit':r.u30(),'traits':self._traits(r)})
        self.scripts=[]; n=r.u30()
        for _ in range(n): self.scripts.append({'init':r.u30(),'traits':self._traits(r)})
        self.bodies=[]; n=r.u30()
        for _ in range(n):
            start=r.pos; method=r.u30(); mx=r.u30(); lc=r.u30(); isd=r.u30(); msd=r.u30(); code=r.take(r.u30()); ex=[]
            for _ in range(r.u30()):ex.append((r.u30(),r.u30(),r.u30(),r.u30(),r.u30()))
            tr=self._traits(r); self.bodies.append(Body(method,mx,lc,isd,msd,code,ex,tr,start,r.pos))
        if r.pos!=len(data):raise ValueError((r.pos,len(data)))
        self.body_by_method={b.method:b for b in self.bodies}
    def _traits(self,r):
        out=[]
        for _ in range(r.u30()):
            name=r.u30(); kf=r.u8(); kind=kf&15
            if kind in (0,6):
                slot=r.u30(); typ=r.u30(); vi=r.u30(); vk=r.u8() if vi else 0; dat=('slot',slot,typ,vi,vk)
            elif kind in (1,2,3):dat=('method',r.u30(),r.u30())
            elif kind==4:dat=('class',r.u30(),r.u30())
            elif kind==5:dat=('function',r.u30(),r.u30())
            else:raise ValueError(f'trait kind {kind}')
            md=[r.u30() for _ in range(r.u30())] if kf&0x40 else []
            out.append(Trait(name,kind,dat,md))
        return out
    def name(self,index:int):
        v=self.pools['multiname'][index]
        if not v:return '*'
        if v[0] in (7,13):
            ns=self.pools['namespace'][v[1]]; package=self.pools['string'][ns[1]]
            return (package+'.' if package else '')+self.pools['string'][v[2]]
        if v[0] in (15,16):return self.pools['string'][v[1]]
        return str(v)
    def local_name(self,index:int):
        v=self.pools['multiname'][index]
        if v and v[0] in (7,13):return self.pools['string'][v[2]]
        if v and v[0] in (15,16):return self.pools['string'][v[1]]
        return self.name(index)
    def method(self,class_name:str,method_name:str)->int:
        hits=[]
        for inst in self.instances:
            if self.name(inst['name'])==class_name:
                for t in inst['traits']:
                    if t.kind in (1,2,3) and self.local_name(t.name)==method_name:hits.append(t.data[2])
        if len(hits)!=1:raise ValueError((class_name,method_name,hits))
        return hits[0]
    def qname(self,package:str,name:str)->int:
        ns=self.pools['namespace']; si=self.pools['string']
        for i,v in enumerate(ns):
            if v and v[0] in (5,22) and si[v[1]]==package:
                for j,m in enumerate(self.pools['multiname']):
                    if m and m[0]==7 and m[1]==i and si[m[2]]==name:return j
        raise ValueError((package,name))

def encode_tag(code,data):
    return struct.pack('<HI',(code<<6)|63,len(data))+data if len(data)>=63 else struct.pack('<H',(code<<6)|len(data))+data

def parse_tags(body):
    n=(body[0]>>3)&31; p=(5+4*n+7)//8+4; out=[]
    while p+2<=len(body):
        v=struct.unpack_from('<H',body,p)[0]; code=v>>6; ln=v&63; h=2
        if ln==63:ln=struct.unpack_from('<I',body,p+2)[0];h=6
        e=p+h+ln
        if e>len(body):raise ValueError('truncated SWF tag')
        out.append({'offset':p,'code':code,'data':body[p+h:e],'raw':body[p:e]});p=e
        if code==0:break
    return out
