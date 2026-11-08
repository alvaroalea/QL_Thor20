# Ecuaciones de U4 y U13 (GAL16V8)

Fuentes en formato galasm/galette: [U4.pld](U4.pld) y [U13.pld](U13.pld).
**No son los fusibles originales**: son ecuaciones reconstruidas para que el
hardware del esquema funcione con lo que hace la ROM `Thor20SysRom_5_22.bin`.
No se han compilado a JEDEC ni probado en placa.

## 1. Lo que dice la ROM (mapa de E/S)

El driver accede a la E/S con direccionamiento absoluto corto (`$FFxx.w`).
En el 68008 eso se extiende a `$FFFFFFxx` y queda en `$FFFxx`. Con A8-A14 sin
decodificar, el bloque se repite en todo `$F8000-$FFFFF`.

| Dirección | A7 A6 | Dispositivo | Uso en la ROM |
|---|---|---|---|
| `$FF00` | 00, A4=0, A3=0 | SCSI datos (U12) | `move.b (a4),(a1)+` sin sondeo: el handshake lo hace el hardware |
| `$FF08` | 00, A4=0, A3=1 | SCSI selección (escritura) / estado (lectura, U15) | escribe el bit de ID; lee b7=REQ, b1=C/D, b0=I/O |
| `$FF10-$FF13` | 00, A4=1 | WD1772 | `$FF10` cmd/estado, `$FF11` sector, `$FF12` pista, `$FF13` datos (A0/A1 del WD van cruzados con A1/A0 de la CPU, como en el esquema) |
| `$FF40-$FF4C` | 01, A5=0, A4=0 | 6821 (RS0=A2, RS1=A3) | ratón e impresora |
| `$FF50`, `$FF58` | 01, A4=1 | 6850 (RS=A3) | red/serie |
| `$FF80` / `$FFC0` | 10 / 11 | MC146818 DS / AS | reloj |

Eso confirma: `BLK1` es la E/S, el 74LS139 (U5B) separa por A7/A6 y
**U13 separa SCSI (A4=0) de la disquetera (A4=1)**.

El test de suma de la ROM se hace con lecturas relativas al PC (espacio de
programa). Al terminar su inicialización la ROM pone `a3 = $FC000` para que el
barrido de ROMs del QL se pare antes de `$F8000`, la zona de E/S. Es coherente
con que la ROM del sistema esté en `$F0000` y que a la E/S se acceda por datos
(FC0=1).

## 2. U4: decodificación de memoria y DRAM

Entradas: A0, FC0, A15-A19, `DS` (patilla 7), PSEL, RAM.

- **`DS` en la patilla 7 es activa a nivel alto**: es el /DS del bus invertido
  por U2 (patillas 5→6). La ecuación anterior de `PAL_U4.md`
  (`... * /DS`) tiene la polaridad al revés. Con `/DS` los strobes del RTC
  (AS/DS) y los de la placa de ROM saldrían fuera del ciclo.
- U3A/U3B forman la secuencia RAS→MUX→CAS: PSEL=1 en reposo (fila), pasa a 0 en
  el primer flanco de bajada de CLK tras DS (columna) y RAM sube medio ciclo
  después (CAS).
- Los 74LS257 multiplexan A1-A16 en RA0-RA6 y RA8. RA7 lo genera U4 a partir de
  A17 (fila) y A0 (columna). En total son 18 bits por banco (256 KB) y 2 bancos:
  512 KB en `$40000-$BFFFF` (640 KB contando los 128 KB del QL).
- **Refresco**: la placa no tiene contador de refresco, así que se usa
  CAS-antes-de-RAS (el MB81256 lo admite). En cada ciclo fuera de
  `$C0000-$FFFFF`, el banco que no se accede recibe /CAS con DS y /RAS con RAM.
  Se excluye la zona ROM/E/S para no dejar RAS bajo durante las esperas largas
  del SCSI. Limitación: si la CPU pasa más de unos ms trabajando solo dentro de
  un banco, ese banco no se refresca. En la práctica, las interrupciones de 50 Hz
  y las traps de QDOS (que se ejecutan en la ROM del QL) lo evitan, pero no hay
  garantía. En escrituras el banco que se refresca ve /WE bajo (ciclo WCBR):
  no supone un problema en DRAM de 256K, pero conviene saberlo.
- `EN = A19 + A18`: la placa toma todo `$40000-$FFFFF`. NS0 (`$C0000-$CFFFF`)
  queda para una tarjeta en J2. Riesgo: los ciclos de reconocimiento de
  interrupción (FC=111, dirección `$FFFFx`) también activan EN y BLK1, porque U4
  no tiene FC1/FC2. Si el VPA de autovector del QL dependiera de DSMC, habría que
  revisarlo.

## 3. U13: SCSI y selección de la FDC

Sin SCSI, U13 no existe, y `DISC_DIS` tampoco, la activacion del WD1772 viene determinada
solo por `DISC`. Así respondería en todo `$FF00-$FF3F`

Con SCSI U13 `DISC_DIS` se pone a cero en las direcciones `$FF00-$FF08` permitiendo usar esta para
el interfaz SCSI. Con U13 puesta, la patilla 19 manda sobre
R1 y deja la FDC solo en A4=1.

La nota de la hoja ("IC11, IC12, IC13 e IC15 van en zócalo, ampliación 1F/2F")
lo explica.

### Funcionamiento

- **Selección** (escritura en `$FF08`): U12 pone el ID en el bus (inversor
  74LS638, de colector abierto en el lado SCSI) y se activa SEL. HOLD retiene
  DTACK hasta que el disco activa BSY. Entonces SEL baja y termina el ciclo. Si
  nadie responde, R2/C1 (≈0,3 ms) activan `SELTO`, se libera el ciclo y la ROM
  reintenta (20 veces). La ROM detecta la tarjeta escribiendo `$00` en `$FF09`
  (no selecciona a nadie: espera el timeout) y luego mirando b7 (REQ inactivo =
  hay interfaz).
- **Datos** (`$FF00`): el ciclo de CPU espera a REQ.
  - Escritura: se activa ACK y el ciclo se mantiene (con el dato en el bus) hasta
    que el disco retira REQ.
  - Lectura: se da DTACK con REQ. ACK se activa al terminar el ciclo (cuando la
    CPU ya ha capturado el dato) y baja cuando el disco retira REQ.
  - `GO` (patilla 17) y `RDP` (patilla 18) son nodos internos con
    realimentación. Esas patillas no están conectadas en el PCB, lo que encaja
    con este uso.
- Estado (lectura en `$FF08`): U15 con b7=REQ, b1=C/D, b0=I/O, todos a nivel
  crudo (0 = activo). Fases: 1=comando, 2=datos entrada, 3=datos salida,
  0=estado/mensaje.
- `EN` (patilla 1) no hace falta.

He comprobado el handshake con una simulación asíncrona de las ecuaciones frente
a un modelo de target: selección, lectura de 4 bytes, escritura de un CDB de 6
bytes y timeout de selección. No hay bloqueos ni bytes repetidos.

### Tiempos a vigilar

HOLD tiene que llegar a ACK_HOLD antes de que U8 dé DTACK (Q de U3A más un
estado). El camino es U4 → '139 → '04 → U13 → '05. Hay que usar GAL de 15 ns o
más rápidas.

## 4. Otras incoherencias del esquema (fuera de U4/U13)

1. **ACK_HOLD / DSMC de J2**: R11 sube `DSMC` de J2 a +5V y U40 (13→12) lo
   invierte sobre `ACK_HOLD`. Sin tarjeta en J2, ACK_HOLD queda siempre bajo y
   **nunca habría DTACK**. Falta algo: o R11 es pull-down, o la señal entra por
   otro sitio.
2. **VPA**: U8 (9,10→8) tiene la patilla 10 a +5V, así que VPA = Q de U9A, un
   divisor de E sin ninguna dirección. VPA se activaría en la mitad de todos los
   ciclos. Debería depender de `68XX` / BLK1.
3. `SCSI_REQ → U10F → U11A → EXTINT`: REQ genera interrupción externa. La ROM
   sube la máscara a nivel 2 (`ori #$200,sr`) mientras usa el SCSI, así que es
   coherente, pero entre comandos REQ debe estar inactivo.
4. RST del SCSI (J6.24) es directamente el RESET del sistema, así que un
   dispositivo que active RST resetea el Thor.

## 5. Mapa de la placa de ROM (BLK0)

U5A (74LS139, E=/BLK0, A0=A16, A1=A17) da NS0..NS3 en bloques de 64 KB, y
A15/`A15'` (U6) eligen una de las dos EPROM de cada NS. Con BLK0 ocupando
`$C0000-$FFFFF`:

| Señal | Rango | Contenido deducido |
|---|---|---|
| NS0 (O0, no conectado) | `$C0000-$CFFFF` | libre: queda para una tarjeta en J2 |
| NS1, A15=0 / 1 | `$D0000` / `$D8000` | EPROM 27C256 de usuario |
| NS2, A15=0 / 1 | `$E0000` / `$E8000` | EPROM 27C256 de usuario |
| NS3, A15=0 | `$F0000-$F7FFF` | ROM del sistema de 32K (`Thor20SysRom`) |
| NS3, A15=1 | `$F8000-$FFFFF` solo con FC0=0 | EPROM 27C64 de 8K, repetida; solo se lee como espacio de programa porque los accesos de datos a esa zona son E/S (BLK1) |

Salen así los 6 zócalos (5 × 27C256 y 1 × 27C64). La ROM del sistema en
`$F0000` encaja con que su rutina de inicialización devuelva `a3 = $FC000`, que
detiene el barrido de ROMs del QL antes de llegar a la E/S. El código de la
EPROM de 8K puede leer sus propias tablas con direccionamiento relativo al PC,
que también es espacio de programa. No se sabe qué zócalo físico (IC1..IC6)
corresponde a cada NS.

Esto corrige la hipótesis de `Thor_20_romboard/README.md`, que situaba las ROM
en `$B0000-$F8FFF`. Con las entradas de U4, BLK0 solo puede cubrir bloques de
256 KB alineados (A18/A19), así que `$B0000` es imposible.

## 6. Bus de datos, DTACK y habilitaciones

- **Conectores**: J1 va al QL; su símbolo tiene las patillas al revés, porque
  los nombres de red no coinciden con los de las patillas. J2 es el conector de
  paso para otra tarjeta y es el que tiene los nombres correctos. Las líneas de
  dirección y control son comunes a los dos; solo cambian los datos y DSMC.
- **Datos**: el bus local `LD0-7` (periféricos, U12, U14, U15, J3) se une a
  `D'0-7` (J2) mediante RN1, 8 resistencias de 150 Ω en serie, sin buffer. U1
  (74LS245) une `D'` con `D` (J1, CPU) con `/CE = /EN` y `DIR = /RW`, así que solo
  conecta cuando la placa toma el ciclo.
- **DSMC del QL**: EN → Q1 (seguidor de emisor) → `QL_DSMC` en J1. Al ponerlo
  alto se inhibe la decodificación interna del QL.
- **RAM_EN** (/CE de U14, buffer de la DRAM) `= /(BLK0 · BLK1)` (U7 + U6): está
  habilitado en cualquier ciclo que no sea ROM ni E/S, incluso los que no son
  de la placa. No hace daño porque U1 aísla el bus de la CPU, pero ensucia LD/D'.
  `DIR = RW`.
- **DTACK** (U8, colector abierto) `= EN · Q(U3A) · ACK_HOLD · RN2F`, con
  `RN2F = /(BLK1 activo · DISC inactivo)`. Con esto se da DTACK para la RAM, la
  ROM y la zona DISC (FDC/SCSI), con las esperas que pide U13 mediante
  ACK_HOLD. El resto de la E/S (6821, 6850, RTC) queda sin DTACK y debería usar
  VPA (ver el punto 2 de la sección 4).
- **E/S de BLK1** (U5B, A0=A6, A1=A7): O0 = `/DISC`, O1 → U6 → `68XX` (CS0 del
  6821 y del 6850), O2 → U10 → `RTC_DS`, O3 → U10 → `RTC_AS`.
  `STROBE` de impresora = `/(68XX · A5)`. CS1/CS2 del 6821/6850 salen de U9
  (74LS113), sincronizados con E.
- **Inversores de control**: `XXX_RW = RAM_RW = RW` (doble inversión en U2).
  `DS = /DS'` (U2). `CLK_B` = CLKCPU sin invertir y `U3A-C` = CLKCPU invertido.

## 7. Ficheros relacionados

- [U4.pld](U4.pld), [U13.pld](U13.pld): fuentes galasm/galette (sin compilar).
- [sim_u13.py](sim_u13.py): simulación asíncrona de U13 frente a un modelo de
  target SCSI (`python3 sim_u13.py`).
- [SCSI.md](SCSI.md): análisis de la interfaz SCSI y del driver WIN.
- [PAL_U4.md](PAL_U4.md): ecuación de un análisis anterior (polaridad de DS
  incorrecta, ver sección 2).
- `../../Thor_20_romboard/doc/Thor20SysRom_5_22.lst`: desensamblaje de la ROM
  y `dis68k.py`, el script que lo genera.
