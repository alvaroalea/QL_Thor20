#!/usr/bin/env python3
"""Genera la imagen de U9 (W27C512) para la placa Thor 20 segun el cableado
del esquema KiCad actual (7-nov-2026).
Uso: rom_image.py origen.bin salida.bin     (origen = imagen vista por la CPU desde 0x0000)
     rom_image.py --selftest
"""
import sys
# direccion de la ROM (bit i) <- linea de direccion de la CPU
SRC = [8,1,2,14,13,5,0,7,6,9,10,11,12,4,3,15]
# dato de la ROM (pin Dk) <- bit del byte (D24+n) : D31,D30,D29,D26,D25,D27,D24,D28
DMAP = [7,6,5,2,1,3,0,4]
def in_window(a):   # EPROM = !A16..A19 & !(A14&A15)  -> 0x0000-0xBFFF (48 KB); 0xC000-0xFFFF libre (cartucho)
    # (U6C/U8B/U8C-F; U8A NO debe tener A14 en la entrada)
    return ((a>>16)&0xF)==0 and (a & 0xC000)!=0xC000
def rom_index(a): return sum(((a>>SRC[i])&1)<<i for i in range(16))
def scramble(v):  return sum(((v>>DMAP[k])&1)<<k for k in range(8))
def unscramble(r):
    v=0
    for k in range(8): v|=((r>>k)&1)<<DMAP[k]
    return v
def build(src):
    rom=bytearray([0xFF])*0x10000
    for a in range(0x10000):
        if in_window(a) and a<len(src): rom[rom_index(a)]=scramble(src[a])
    return rom
def selftest():
    import random
    src=bytes(random.randrange(256) for _ in range(0xC000))
    rom=build(src)
    for a in range(0xC000):
        if in_window(a): assert unscramble(rom[rom_index(a)])==src[a],hex(a)
    assert len({rom_index(a) for a in range(0x10000) if in_window(a)})==0xC000
    assert not any(in_window(a) for a in range(0xC000,0x10000))
    print("selftest OK: 48 KB utiles (0x0000-0xBFFF), 0xC000-0xFFFF libre")
if __name__=='__main__':
    if sys.argv[1:]==['--selftest']: selftest()
    else:
        out=build(open(sys.argv[1],'rb').read()); open(sys.argv[2],'wb').write(out)
