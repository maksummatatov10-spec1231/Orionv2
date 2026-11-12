import struct,zlib,sys
from pathlib import Path
def tags(d):
 n=(d[0]>>3)&31;p=(5+4*n+7)//8+4;out=[]
 while p+2<=len(d):
  v=struct.unpack_from('<H',d,p)[0];c=v>>6;l=v&63;h=2
  if l==63:l=struct.unpack_from('<I',d,p+2)[0];h=6
  out.append((p,h,c,d[p+h:p+h+l]));p+=h+l
  if c==0:break
 return out
def enc(c,d):
 if len(d)>=63:return struct.pack('<HI',(c<<6)|63,len(d))+d
 return struct.pack('<H',(c<<6)|len(d))+d
def doabc(name,abc,flags=0): return enc(82,struct.pack('<I',flags)+name.encode()+b'\0'+abc)
src=Path(sys.argv[1]);dst=Path(sys.argv[2])
b=src.read_bytes();d=zlib.decompress(b[8:]);ts=tags(d)
stub=Path('/tmp/orion-tools/asc/airstub/output.abc').read_bytes()
verify=Path('/tmp/orion-tools/asc/verify/output.abc').read_bytes()
lib=Path('/tmp/orion-runtime-v04/FRESteamWorks-library.swf').read_bytes();ld=zlib.decompress(lib[8:])
abc_tags=[doabc('airstub',stub),doabc('verifybootstrap',verify)]+[enc(82,t[3]) for t in tags(ld) if t[2]==82]
idx=next(i for i,t in enumerate(ts) if t[2]==76);pos=ts[idx][0]
nd=d[:pos]+b''.join(abc_tags)+d[pos:]
dst.write_bytes(b'CWS'+b[3:4]+struct.pack('<I',8+len(nd))+zlib.compress(nd,9))
print(dst,len(abc_tags),'ABC tags inserted')
