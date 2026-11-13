#!/usr/bin/env python3
"""Compile a test-only Stage0Probe mode and append it to an AIR-stubbed IC SWF.
The production Orion.ic-dev.swf is never modified by this script.
"""
from pathlib import Path
import argparse,struct,subprocess,sys,zlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from abc_utils import parse_tags,encode_tag
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['setup','reload','resin'],required=True);ap.add_argument('--java',default='/tmp/orionjdk/jdk4py/java-runtime/bin/java');ap.add_argument('--asc',default='/tmp/orion-tools/asc/asc.jar');ap.add_argument('--game-abc',default='/tmp/ic-stage0/frame2.abc');args=ap.parse_args()
 test=ROOT/'build/test';test.mkdir(parents=True,exist_ok=True)
 src=test/'Stage0Probe.as';src.write_text((ROOT/'verification/Stage0Probe.as').read_text().replace('__MODE__',args.mode))
 cmd=[args.java,'-jar',args.asc,'-AS3','-md','-strict']
 for p in sorted(Path('/tmp/orion-tools/asc').glob('playerglobal_*.abc')):cmd+=['-import',str(p)]
 cmd+=['-import',args.game_abc,'-import',str(ROOT/'build/IndustrialCraft.abc'),str(src)]
 abc=test/'Stage0Probe.abc'
 if abc.exists():abc.unlink()
 r=subprocess.run(cmd,cwd=test,capture_output=True,text=True);print(r.stdout);print(r.stderr,file=sys.stderr)
 if r.returncode or '[Compiler] Error' in r.stdout or 'error found' in r.stdout.lower():sys.exit(1)
 if not abc.exists():sys.exit('missing probe abc')
 stub=ROOT/'build/Orion.ic-test.swf'
 subprocess.run([sys.executable,str(ROOT.parent/'textures-v0.5/runtime/append_air_stub.py'),str(ROOT/'build/Orion.ic-dev.swf'),str(stub)],check=True)
 b=stub.read_bytes();d=zlib.decompress(b[8:]);ts=parse_tags(d)
 # AIR stubs must precede frame1's SymbolClass, but the probe references game
 # classes from frame2. Put it before the LAST SymbolClass, after frame2 + mod.
 pos=ts[max(i for i,t in enumerate(ts) if t['code']==76)]['offset']
 nd=d[:pos]+encode_tag(82,struct.pack('<I',0)+b'icstage0probe\0'+abc.read_bytes())+d[pos:]
 out=ROOT/f'build/Orion.ic-{args.mode}.swf';out.write_bytes(b'CWS'+b[3:4]+struct.pack('<I',8+len(nd))+zlib.compress(nd,9));print(out)
if __name__=='__main__':main()
