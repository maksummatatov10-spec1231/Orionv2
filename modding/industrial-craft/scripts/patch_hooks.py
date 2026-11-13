#!/usr/bin/env python3
"""Patch three empty Orion extension hooks; preserve every other ABC byte.

World and EarthWorld saveAdditional_v1/loadAdditional_v1 cover full and partial saves.
EarthWorld overrides the base hooks, so appending only to World would never persist IC.
GameProcess.initStatic is the safe content-registration point: atlases and localization
are ready, but no world or saved ItemStack has been loaded yet.
"""
from pathlib import Path
import argparse,json,struct
from abc_utils import ABC,u30,encode_tag

def add_qname(a,package,name):
    si=a.pools['string']; ns=a.pools['namespace']
    if name not in si:si.append(name)
    ni=si.index(name)
    if package not in [si[v[1]] for v in ns if v]:
        ns.append((22,si.index(package) if package in si else len(si)))
        if package not in si:si.append(package);ns[-1]=(22,si.index(package))
    pi=next(i for i,v in enumerate(ns) if v and v[0]==22 and si[v[1]]==package)
    for i,m in enumerate(a.pools['multiname']):
        if m and m[0]==7 and m[1]==pi and m[2]==ni:return i
    a.pools['multiname'].append((7,pi,ni));return len(a.pools['multiname'])-1

def u32enc(n):
    n &= 0xffffffff;out=bytearray()
    while True:
        b=n&127;n>>=7;out.append(b|(128 if n else 0))
        if not n:return bytes(out)

def encode_pool(a,kind):
    vals=a.pools[kind];out=bytearray(u30(len(vals)))
    for v in (vals[1:] if vals else []):
        if kind in ('int','uint'):out+=u32enc(v)
        elif kind=='double':out+=struct.pack('<d',v)
        elif kind=='string':
            b=v.encode();out+=u30(len(b))+b
        elif kind=='namespace':out+=bytes([v[0]])+u30(v[1])
        elif kind=='ns_set':
            out+=u30(len(v))
            for x in v:out+=u30(x)
        elif kind=='multiname':
            out+=bytes([v[0]])
            if v[0] in (7,13,9,14):out+=u30(v[1])+u30(v[2])
            elif v[0] in (15,16,27,28):out+=u30(v[1])
            elif v[0] in (17,18):pass
            elif v[0]==29:
                out+=u30(v[1])+u30(len(v[2]))
                for x in v[2]:out+=u30(x)
    return bytes(out)

def patch(data:bytes, mod_abc:bytes):
    a=ABC(data); mod=ABC(mod_abc); edits=[]; report=[]
    specs=[('orion.worlds.World','saveAdditional_v1','saveWorld',2,'replace_empty'),
           ('orion.worlds.World','loadAdditional_v1','loadWorld',2,'replace_empty'),
           ('orion.worlds.earth.EarthWorld','saveAdditional_v1','saveWorld',2,'append'),
           ('orion.worlds.earth.EarthWorld','loadAdditional_v1','loadWorld',2,'append'),
           ('orion.GameProcess','initStatic','install',0,'append')]
    # ASC emits public static methods in the default (empty) package namespace.
    mod.qname('industrialcraft','IndustrialCraftBootstrap')
    for name in ('saveWorld','loadWorld','install'): mod.qname('',name)
    for cls,method,static_method,args,mode in specs:
        mi=a.method(cls,method); body=a.body_by_method[mi]
        if mode=='replace_empty' and body.code!=bytes.fromhex('d03047'):
            raise ValueError((cls,method,'expected empty hook',body.code.hex()))
        if mode=='append' and not body.code.endswith(b'\x47'):
            raise ValueError((cls,method,'unexpected original body',body.code.hex()))
        target=add_qname(a,'',static_method)
        # findpropstrict Bootstrap; getlocal0/getlocal1; callpropvoid static_method
        code=bytearray(b'\x30') # pushscope is already represented by original d030 below
        prefix=bytes.fromhex('d030')
        call=bytes([0x60])+u30(add_qname(a,'industrialcraft','IndustrialCraftBootstrap'))
        if args:call+=bytes.fromhex('d0d1')
        call+=bytes([0x4f])+u30(target)+u30(args)+bytes.fromhex('47')
        newcode=prefix+call
        if mode=='append':
            # Preserve every original instruction, including EarthWorld's five integers.
            newcode=body.code[:-1]+call
        newbody=(u30(body.method)+u30(max(body.max_stack,3 if mode=='replace_empty' else body.max_stack+1))+u30(body.locals)+
                 u30(body.init_scope)+u30(body.max_scope)+u30(len(newcode))+newcode+u30(len(body.exceptions))+u30(len(body.traits)))
        if body.exceptions or body.traits:raise ValueError('hook has unexpected exceptions/traits')
        edits.append((body.start,body.end,newbody))
        report.append({'class':cls,'method':method,'calls':'industrialcraft.IndustrialCraftBootstrap.'+static_method,
                       'original_code_sha256':__import__('hashlib').sha256(body.code).hexdigest(),
                       'patched_code_sha256':__import__('hashlib').sha256(newcode).hexdigest(),
                       'original_body_size':body.end-body.start,'patched_body_size':len(newbody),'mode':mode})
    base=bytearray(data)
    for kind in reversed(['int','uint','double','string','namespace','ns_set','multiname']):
        start,end=a.pool_ranges[kind];base[start:end]=encode_pool(a,kind)
    cur=bytearray(base)
    for cls,method,_,_,_ in specs:
        aa=ABC(bytes(cur)); nb=aa.body_by_method[aa.method(cls,method)]
        new=next(n for (st,en,n),sp in zip(edits,specs) if sp[0]==cls and sp[1]==method)
        cur[nb.start:nb.end]=new
    out=bytes(cur)
    result=bytes(out); ABC(result) # full structural round-trip check
    # Only the selected method bodies may differ; all pools and other bodies are exact.
    b=ABC(result)
    changed=[]
    for old in a.bodies:
        new=b.body_by_method[old.method]
        if old.code!=new.code:changed.append(old.method)
    if set(changed)!={a.method(c,m) for c,m,_,_,_ in specs}:raise ValueError(('changed bodies',changed))

    return result,report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--mod-abc',required=True);ap.add_argument('--report');args=ap.parse_args()
    data=Path(args.input).read_bytes();out,report=patch(data,Path(args.mod_abc).read_bytes());Path(args.output).write_bytes(out)
    if args.report:Path(args.report).write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
