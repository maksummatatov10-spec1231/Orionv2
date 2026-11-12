import ctypes,time,sys
xlib='/tmp/orion-tools/poppler/lib/linux/poppler-24.08-xvfb/lib/libX11.so.6'
tst='/tmp/orion-tools/poppler/lib/linux/poppler-24.08-xvfb/lib/libXtst.so.6'
X=ctypes.CDLL(xlib); T=ctypes.CDLL(tst)
X.XOpenDisplay.restype=ctypes.c_void_p; X.XOpenDisplay.argtypes=[ctypes.c_char_p]
X.XFlush.argtypes=[ctypes.c_void_p]
X.XKeysymToKeycode.restype=ctypes.c_uint; X.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
T.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]; T.XTestFakeKeyEvent.restype=ctypes.c_int
d=X.XOpenDisplay(b':99'); assert d
key=sys.argv[1]; hold=float(sys.argv[2]) if len(sys.argv)>2 else .12
keysym={'e':0x65,'i':0x69,'tab':0xff09,'esc':0xff1b,'space':0x20,'w':0x77,'a':0x61,'s':0x73,'d':0x64,'enter':0xff0d}.get(key.lower(),ord(key[0]))
kc=X.XKeysymToKeycode(d,keysym); print('keycode',kc)
T.XTestFakeKeyEvent(d,kc,1,0); X.XFlush(d); time.sleep(hold); T.XTestFakeKeyEvent(d,kc,0,0); X.XFlush(d)
