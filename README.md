# THOR PC Computer (Compatible with Sinclair Ql)
A reverse engineering exercice using the Sinclair QL compatible Thor-20 Computer as target

Licensed under Cern OHL-S - https://ohwr.org/cern_ohl_s_v2.txt

## WARNING: DO NOT USE THIS PROJECT IS NOT TESTED AND MISSING THINGS
This is not a functional item, it's only a exercice of reverse engineering to reinforce my skills in Kicad EDA Software.

## History

With the end of the comercial life of the Sinclair QL, other companies fill the gap, CST create several models of the Thor computer.

The subject of this project is a interesting one, using old stock of original QL boards, and a re-edition of several of the previous expansion board together with a fancy desktop case to make a enhaced QL Computer, so the Thor consist of:

- The Original QL Board
- The RAM + ROM expansion board board (512Kb of RAM)
- The CST Floppy Disk Interface with 1 or 2 3 1/2" floppy drivers
- The CST SCSI Disk Interface
- The mICE mouse + desktop software solution
- A RTC implementation
- A fancy box
- A upgraded in-box power supply
- Standar PC XT Interface

This was called Thor PC, Thor 1 or Thor 8, depend of the sources of information, there are 3 version available, 1F, 2F, 2WF depend on the number of floppys and Winchister hard disc or not, 1F,2F do not incorporate the IC of the SCSI interface, but can be upgraded later.

Later, CST upgrade it and made the Thor 20 and Thor 21, this was Thor 1 with a CPU-Addon card, that include a 68020 CPU at 12 or 16Mhz, and a 68881 FPU math coprocesor.

Unfortunately, the use of the original QL board, and the RAM in 8bits, cause this board to be only twice the speed of the original QL, while a Gold Card provide the same with twice the ram, and the Super Gold Card provide 4 times the speed of the QL, 4Mb of RAM using the same microprocessor.

## The Project

I will try to recreate all the hardware, and document in a proper way everything I can get of the Thor Computer, up to day there is only some low resolution pictures, a bad scanned service manual, and a dump of some of the ROMs of the computer.

## Technical Information

### Power Supply
The thor 20 come with a IEC C13 socket in the back, and a secondary C14 (for the monitor) a switch shall power on/off both the computer and monitor.

Internally a power supply rated to 30W is used for the system. it provide:
- +5Vdc probably at 3A (for everything)
- +12Vdc probably at 1A (for QL, hard disc and floppy)
- -12Vdc probably at 250mA (for the serial ports of the QL)

a MeanWell PT-45A is probably the good replacement ( https://www.meanwell-web.com/en-gb/ac-dc-triple-output-open-frame-power-supply-output-pt--45a ).

### SCSI Upgrade Kit
To upgrade the Thor 1F or 2F to 2WF a kit of IC11,IC12,IC13 and IC15 can be installed to enable the SCSI interface.

### Memory Mapping

- 0000-0048 Sinclair QL ROM
- 0049-0064 Free for ROM Cartridge Slot
- 0065-0096 Internal 32Kb I/O
- 0097-0128 Free but reserved for I/O
- 0129-0256 Internal QL 128K RAM including Video ram
- 0257-0768 CST 512 Kb Expansion RAM
- 0769-0832 Free 64Kb for external expansion interfaces
- 0833-0999 5x32Kb + 1x8Kb expasion ROM
- 1000-1024 CST Expansion I/O


