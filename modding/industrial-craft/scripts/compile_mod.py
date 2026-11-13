#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,shutil
ROOT=Path(__file__).resolve().parents[1];BUILD=ROOT/'build';BUILD.mkdir(exist_ok=True)
java='/tmp/orionjdk/jdk4py/java-runtime/bin/java';asc='/tmp/orion-tools/asc/asc.jar'
args=[java,'-jar',asc,'-AS3','-md','-strict']
for p in sorted(Path('/tmp/orion-tools/asc').glob('playerglobal_*.abc')):args+=['-import',str(p)]
args+=['-import','/tmp/ic-stage0/frame2.abc']
files=sorted((ROOT/'src').rglob('*.as'))
# asc compiles one public class per invocation reliably; compile together via -in syntax.
for f in files:args+=['-in',str(f)]
args.append(str(BUILD/'IndustrialCraft.as'))
out=BUILD/'IndustrialCraft.abc'
if out.exists():out.unlink()
r=subprocess.run(args,cwd=BUILD,capture_output=True,text=True)
print(r.stdout);print(r.stderr,file=sys.stderr)
if r.returncode or 'error found' in r.stdout.lower() or '[Compiler] Error' in r.stdout:sys.exit(1)
if not out.exists():print('missing',out);sys.exit(1)
print(out,out.stat().st_size)
