import ctypes,time,sys
xlib='/tmp/orion-tools/poppler/lib/linux/poppler-24.08-xvfb/lib/libX11.so.6'; tst='/tmp/orion-tools/poppler/lib/linux/poppler-24.08-xvfb/lib/libXtst.so.6'
X=ctypes.CDLL(xlib); T=ctypes.CDLL(tst)
X.XOpenDisplay.restype=ctypes.c_void_p; X.XOpenDisplay.argtypes=[ctypes.c_char_p]; X.XFlush.argtypes=[ctypes.c_void_p]
T.XTestFakeMotionEvent.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ulong]
T.XTestFakeButtonEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
d=X.XOpenDisplay(b':99'); assert d
x=int(sys.argv[1]);y=int(sys.argv[2]);btn=int(sys.argv[3]) if len(sys.argv)>3 else 1
T.XTestFakeMotionEvent(d,-1,x,y,0);X.XFlush(d);time.sleep(.12)
T.XTestFakeButtonEvent(d,btn,1,0);X.XFlush(d);time.sleep(.08);T.XTestFakeButtonEvent(d,btn,0,0);X.XFlush(d)
print('clicked',x,y,btn)
