from pathlib import Path
import mmap,struct,ctypes,zlib
root=Path(__file__).resolve().parent
lib=ctypes.CDLL(str(root/'decode.dylib'))
lib.decode.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_size_t]
out=root/'setup'; out.mkdir(exist_ok=True)
with open(Path.home()/'Downloads/codesys.exe','rb') as f:
 m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
 pos=m.find(b'ISSetupStream\0',1300000); count,typ=struct.unpack_from('<HI',m,pos+14); pos+=46
 for i in range(count):
  nl,flags,length,compressed=struct.unpack_from('<II2xI8xH',m,pos); pos+=48 if typ==4 else 24
  name=m[pos:pos+nl].decode('utf-16le').rstrip('\0'); pos+=nl
  target=out/name.replace('\\','/'); assert target.resolve().is_relative_to(out)
  target.parent.mkdir(parents=True,exist_ok=True)
  seed=name.encode(); key=bytes(c^b'\x13\x35\x86\x07'[j%4] for j,c in enumerate(seed))
  print(name,length,flags,compressed,flush=True)
  z=zlib.decompressobj() if compressed else None
  with target.open('wb') as dest:
   for off in range(0,length,1048576):
    data=ctypes.create_string_buffer(m[pos+off:pos+min(off+1048576,length)])
    n=len(data)-1
    if flags&4: lib.decode(data,n,key,len(key))
    dest.write(z.decompress(data.raw[:n]) if z else data.raw[:n])
   if z: dest.write(z.flush()); assert z.eof
  pos+=length
