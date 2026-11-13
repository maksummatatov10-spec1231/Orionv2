import ctypes,sys
X=ctypes.CDLL('/tmp/orion-tools/poppler/lib/linux/poppler-24.08-xvfb/lib/libX11.so.6')
X.XOpenDisplay.restype=ctypes.c_void_p;X.XOpenDisplay.argtypes=[ctypes.c_char_p]
X.XDefaultRootWindow.restype=ctypes.c_ulong;X.XDefaultRootWindow.argtypes=[ctypes.c_void_p]
X.XQueryTree.restype=ctypes.c_int;X.XQueryTree.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(ctypes.c_ulong),ctypes.POINTER(ctypes.c_ulong),ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)),ctypes.POINTER(ctypes.c_uint)]
X.XFetchName.restype=ctypes.c_int;X.XFetchName.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(ctypes.c_char_p)]
X.XMoveResizeWindow.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_int,ctypes.c_uint,ctypes.c_uint]
X.XFlush.argtypes=[ctypes.c_void_p]
d=X.XOpenDisplay(b':99');root=X.XDefaultRootWindow(d)
r=ctypes.c_ulong();p=ctypes.c_ulong();kids=ctypes.POINTER(ctypes.c_ulong)();n=ctypes.c_uint()
X.XQueryTree(d,root,ctypes.byref(r),ctypes.byref(p),ctypes.byref(kids),ctypes.byref(n))
for i in range(n.value):
 w=kids[i];name=ctypes.c_char_p();X.XFetchName(d,w,ctypes.byref(name));s=name.value.decode(errors='replace') if name.value else ''
 if 'Flash' in s or 'Adobe' in s:
  X.XMoveResizeWindow(d,w,0,0,1280,800);print('resized',w,s)
X.XFlush(d)
