# Interfaz SCSI del Thor 20 y driver WIN (ROM 5.22)

Análisis del hardware (hoja "SCSI Interface") y del desensamblado de
`Thor_20_romboard/roms/Thor20SysRom_5_22.bin`. Las direcciones `$4xxx` son
desplazamientos dentro de la ROM.

## 1. Hardware

- Es un **iniciador SASI/SCSI-1 mínimo**, sin controlador dedicado: U12 (74LS638,
  transceptor inversor de colector abierto) para el bus de datos, U15 (74LS245)
  como registro de estado y U13 (GAL) para SEL/ACK y para alargar el ciclo de la
  CPU hasta que llega REQ (handshake "pseudo-DMA" con estados de espera).
- No hay arbitraje, ATN, mensajes ni paridad (DBP en J6.18 sin conectar). Al
  seleccionar, solo se pone el bit del destino, no el ID del iniciador. MSG
  (J6.26) no se lee.
- El conector J6 es de 34 patillas. Las señales de control tienen la numeración
  del conector SCSI de 50 patillas menos 16: J6.20=BSY(36), 22=ACK(38),
  24=RST(40), 26=MSG(42, n.c.), 28=SEL(44), 30=C/D(46), 32=REQ(48), 34=I/O(50).
  Los datos van en 2-16, como en SCSI. Para un disco SCSI estándar hace falta un
  cable adaptador 34→50. ATN debe quedar inactivo (terminado) y TERMPWR lo tiene
  que dar el dispositivo.
- Eléctricamente, SEL y ACK salen por 74LS05 (unos 8 mA) y los datos por un LS638.
  Eso basta para un bus corto terminado solo en el extremo del disco, pero no
  para dos terminaciones estándar de 220/330 Ω.
- Velocidad: el bucle de lectura está desenrollado ×16 (`move.b (a4),(a1)+`, 12
  ciclos + espera). Con el 68008 a 7,5 MHz el máximo teórico es unos 600 KB/s; en
  la práctica, de 300 a 500 KB/s.

## 2. Driver WIN

| Rutina | Función |
|---|---|
| `$4138` | detección: escribe `$00` en `$FF09`, espera y lee b7; si REQ está inactivo instala el driver `WIN` |
| `$41FA` | FORMAT. El nombre tiene que empezar por `*` (`FORMAT win1_*NOMBRE`), como protección |
| `$4F78` / `$4F88` / `$4FA6` / `$4FAE` / `$4FC0` | montan READ(6) `$08`, WRITE(6) `$0A` y FORMAT UNIT `$04` (interleave 3) |
| `$4FD0` | motor común: selección (ID = `$80 rol unidad`, 1000 sondeos × 20 reintentos), envío del CDB (de 10 bytes si el opcode es ≥ `$20`) y fases de datos y estado |
| `$5132` | estado + mensaje. Si hay CHECK CONDITION envía REQUEST SENSE (`$03`, longitud 0 → 4 bytes, estilo SASI). El código `$18` (ECC corregido) se ignora; los demás muestran `winchester error XXXXXXXX` |
| `$51DA` | error de protocolo: `winchester SCSI error` y marca `$44(a3)`. **El driver queda muerto hasta el reset** |

Capacidades:

- **Hasta 8 unidades**: `WIN1`..`WIN8` corresponden a los ID SCSI 0..7, todas en
  LUN 0.
- Bloque fijo de 512 bytes. Comandos: READ(6), WRITE(6), FORMAT UNIT y REQUEST
  SENSE. No usa INQUIRY, READ CAPACITY ni TEST UNIT READY.
- **La geometría está fija en la ROM**:

| Dato | Valor |
|---|---|
| Sectores totales | 41 616 (= 612 cil × 4 cab × 17 sect, unos 20,3 MB, un ST-225) |
| Cluster | 34 sectores = 17 KB (`$22`, `$4400`) |
| Mapa | 1224 entradas × 3 bytes (`$4C7`, `$E96`) |
| Ocupación del disco | LBA 0-7: cabecera `QS20` + nombre + libres/total + mapa. Cluster 1 (LBA 34-67): directorio |
| Entrada de mapa | 12 bits de nº de fichero + 12 bits de bloque del fichero. `$FFx` = libre, `$FE` = reservado. El cluster lo da la posición en el mapa |
| Traducción | LBA = cluster × 34 + (sector del fichero mod 34) |

Al montar se lee `$E6E` bytes desde LBA 0 y se comprueba la firma `QS20`. Nunca
se pregunta la capacidad al disco.

## 3. ¿Funciona otro disco sin tocar la ROM?

**Sí**, si el dispositivo cumple esto:

1. Bloques de 512 bytes y al menos 41 616 bloques. Lo que sobre no se usa.
2. Acepta selección con un solo bit de ID, sin ATN y sin mensaje IDENTIFY. Es
   modo SCSI-1/SASI; la mayoría de discos SCSI-1/2 y emuladores lo aceptan.
3. Paridad desactivada en el disco.
4. Admite READ(6), WRITE(6) y FORMAT UNIT (el byte 4 = 3 se ignora en SCSI).
5. REQUEST SENSE con longitud 0 devuelve 4 bytes (SCSI-1 y SCSI-2 sí; SPC-3 y
   posteriores devuelven 0 bytes). Si no, cualquier CHECK CONDITION acaba en
   "winchester SCSI error" y el driver queda bloqueado hasta el reset. Lo más
   delicado es la **UNIT ATTENTION de arranque** de los discos SCSI-2: en
   SCSI2SD/ZuluSCSI/BlueSCSI hay que desactivarla, o la primera orden fallará.

Un **SCSI2SD/ZuluSCSI/BlueSCSI** en modo SCSI-1, sin paridad, sin Unit Attention
y con imágenes de 41 616 sectores (21 307 392 bytes) en los ID 0..7 da hasta
**8 volúmenes de 20 MB (unos 160 MB) sin parchear nada**. Es la opción más
recomendable.

## 4. Parchear la ROM para unidades mayores

Es factible: el driver es pequeño, independiente de la posición y las constantes
están localizadas. Cuidado con dos cosas:

- La ROM está llena y su suma de palabras de 16 bits tiene que dar 0 (se
  comprueba en `$0072`). Después de parchear hay que compensarlo cambiando una
  palabra sin uso o ajustando un texto.
- Conviene cambiar la firma `QS20` (en `$425E` y `$4F16`) para no montar discos
  con la geometría antigua.

Constantes que intervienen (todas entre `$4138` y `$4F16`):

- Tamaño de cluster `$22`: `$41AA`, `$4244`, `$4250`, `$42CC`, `$4302`, `$472C`,
  `$4764`, `$481E`, `$4872`, `$4C32`, `$4C3C`, `$4CEC`, `$4D2A`, `$4EA8`,
  `$4EB2`.
- Dos clusters `$44`: `$4270`, `$42DC`, `$4328`.
- Bytes por cluster `$4400`: `$42E6`, `$480A`, `$483C`, y `$4043C0` en `$484C`.
- Mapa: `$4C7` en `$4238`; fin del mapa `$E96` en `$4186`, `$4740`, `$4878`,
  `$4CB4` y `$4D40`; lectura `$E6E` en `$4F02`; escritura `$1000` en `$42B4` y
  `$4ED2`; memoria del driver `$1096` en `$4206`.

### Límites encontrados

| Límite | Causa | Valor |
|---|---|---|
| LBA | READ/WRITE(6): 21 bits | **1 GiB por unidad** (2²¹ × 512) |
| Cluster | contador de bytes de 16 bits en `$4F98` y `mulu`/`divu` .w | ≤ 127 sectores (63,5 KB) |
| Índice de cluster | `adda.w` con signo | < 32 768 clusters |
| Mapa | se lee y escribe de una vez (≤ 65 024 bytes) y vive en RAM (3 bytes/cluster por unidad) | ≤ 21 667 entradas |
| Fichero | puntero QDOS bloque:byte de 16:9 bits | 32 MB por fichero |
| Ficheros | nº de fichero de 12 bits | unos 4000 por unidad |
| Informe de FORMAT/DIR | contadores de 16 bits | se satura en 32 767 sectores (solo afecta a lo que se muestra) |

### Opciones

| Parche | Cambios | Tamaño máx. | Coste |
|---|---|---|---|
| A. Solo cluster mayor (mapa de 1224) | constantes de cluster | 64 sect.: 40 MB; 127 sect.: **79,6 MB** | cada fichero ocupa como mínimo 32-63 KB |
| B. Mapa mayor (cluster de 34) | constantes de mapa y memoria; el mapa tiene que caber en el cluster 0 (≤ 5795 entradas) | **unos 100 MB** | 17 KB de RAM por unidad; el recorrido lineal del mapa es más lento |
| C. A+B, p. ej. 64 sect. y 4095 entradas | ambos | **128 MB** | 12 KB de RAM por unidad; mínimo 32 KB por fichero |
| D. Máximo teórico (127 sect., unas 16 500 entradas) | ambos y reservar más clusters para el mapa | **1 GiB** | unos 50 KB de RAM por unidad y un mapa muy lento de recorrer; poco práctico |
| E. Particiones: el nº de unidad va a los bits altos del LBA en lugar de ir al ID | unas pocas instrucciones en `$4FE4` y `$4F78`-`$4FC0` | 8 × 20 MB en **un solo disco** | el más sencillo; el formato no cambia |

Ir más allá de 1 GiB exige pasar a READ(10)/WRITE(10). El código ya envía CDB de
10 bytes, pero habría que reescribir el montaje del CDB, y el límite de 32 MB por
fichero de QDOS sigue ahí.

**Recomendación:** si no se quiere tocar la ROM, usar un emulador SD con varios
ID de 20 MB. Si se parchea, la opción **E** (particiones de 20 MB en un solo
disco) o la **C** (128 MB por unidad) son las que mejor compensan esfuerzo y
riesgo.
