# CST Thor - ROM Board.

(C) 2023 Alvaro Alea Fernandez

License under: CERN Open Hardware Licence Version 2 - Strongly Reciprocal

https://ohwr.org/cern_ohl_s_v2.txt

This board has been reverse engineered from pictures freely available on internet.

THIS BOARD HAS NOT BEEN TESTED!! Use at your own risk.

This is a fast hack, not real dimension or position or tracks.

![My image](Thor_20_romboard_comp.png)

## Technical Details

The board has space for 6 IC Eprom Memories.
The schematic depend on 2 lines of selection, one is A15 or /A15, and the other come from IC5  and decode the A16,A17 lines, that mean that is targeted for the 6 32Kb IC, (type 27C256) and will use the 0xB0000 to 0xF8FFF leaving the 0xA0000 to 0xAFFFF empty to be used by the expansion slot on the back of the computer. in any case 0xF9000 to 0xFFFFF (last 24kb of memory) is reserved for I/O

Complete decode of the memory space depend of pin 13 of IC4 (BLK0) a programable GAL, so it's unknow.

It's not clear the contents of each chip, but I see on internet two kind of pictures.
- IC1 is not alwais populated, but when does, it has sticker with "1". This is probably the PSION Suite
- IC2 is not alwais populated, but when does, it has sticker with "2". This is probably the PSION Suite
- IC3 a 27C256, it has sticker with "3" or "Int ROM 0952" This is probable the hardware drivers, named InterLogicExt (2.10 cann be found in thor820roms.zip on Dilwin pages)
- IC4 a 27C256, it has sticker with "Speed Screen (C) 1988 CST" (4.23 can be found in thor820roms.zip on Dilwin pages)
- IC5 a 27C256, it has stickers with a version number, Thor20Sysrom (from 4.11 to 5.22 can be found on Dilwin pages)
- IC6 a 27C64, it has sticker with "Thor" and a date, "Pascal" rom?
