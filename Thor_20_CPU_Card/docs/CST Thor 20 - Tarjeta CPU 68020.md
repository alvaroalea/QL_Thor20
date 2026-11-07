# CST Thor 20 - Tarjeta CPU 68020

Nov 7, 2026 · @Aleasoft

## Conclusiones

El esquema actualizado es eléctricamente coherente y, con una corrección pendiente (el pull-up del /OE de la ROM), debería funcionar. No está probado: la lógica de U10 es una reconstrucción mía, validada solo por simulación propia.

**Pendiente o por verificar:**

- **ROM interna del QL:** U10 activa AS\_68K8 también en ciclos de ROM (necesario para habilitar ACK2). Si la decodificación de la ROM de la placa QL usa AS sin DS, habría contención de bus con U9.
- **FPU\_CS sin FPU:** si la CPU ejecuta una instrucción de línea F con cpID 1–7 y no hay FPU montada, la placa se cuelga: nadie contesta con DSACK ni con BERR (A15–A13 no se decodifican). Es el comportamiento actual y se acepta. Mejora futura: un jumper JP1 de 3 pines (U6A pin 13 a FPU\_CS o a +5V) o una resistencia serie de unos 330 Ω entre U10 pin 21 y ese nodo, para que sin FPU se dé bus error y el trap de instrucción F (vector 11).
- **Falta el pull-up en U8A pin 2 / U9 pin 22:** U8A ya invierte R/W hacia el /OE de U9, pero su salida es de colector abierto: con R/W bajo (escritura) queda al aire y /OE flota. Añade una sección libre de RN2 a +5V en ese nodo.
- **Valor sin especificar:** condensador C9 (reset).
- **IPL0 a +5V:** vale para el nivel 2 del QL; los niveles 5 y 7 del 68008 pasan a 4 y 6.

## Explicación de los circuitos

La tarjeta se enchufa en el zócalo del 68008 (U1 es ese conector). La 68020 trabaja con su propio reloj y usa un puerto de 8 bits (solo DSACK0) hacia el QL: datos en D31–D24 de la CPU, que son D0–D7 del QL. El bus del QL se genera con las señales AS\_68K8 y DS\_68K8, sincronizadas con el reloj de 7,5 MHz de la placa QL (CLK\_68K8, que lleva el pull-up R1 de 4,7 kΩ a +5V soldado en el pin 34 del 68008, fuera de la PCB).

| Bloque | Qué hace |
| --- | --- |
| Y1, U5B, U5C, RN1C/D, C7 | Oscilador de cristal con dos inversores LS04, cada uno polarizado con una resistencia de RN1. Genera CLK de 12 MHz para la 68020 y la 68881. |
| U5F + U4A | U5F invierte AS. U4A lo muestrea con el flanco de subida de CLK\_68K8 y se borra de forma asíncrona cuando AS termina. Su salida /Q (AS2, activa baja) significa «ciclo de CPU visto en el reloj del QL». |
| U4B + U5E + D1 | Cuando ACK2 (de la PAL) baja, U5E sube el reloj de U4B, que captura AS activo. Su /Q baja DSACK0 a través del diodo BAT85 y se mantiene hasta que AS termina. DSACK1 nunca se activa (pull-up de RN1), así que la CPU ve un puerto de 8 bits. El diodo aísla esa salida de las de la FPU. |
| U7 (74LS290) | Contador BCD libre sobre CLK\_68K8 (cuenta en flanco de bajada, entradas de reset/set a GND). Q2 es el reloj E del 68000 (4 ciclos alto, 6 bajo) y sale al zócalo. Q0, Q1, Q3 y E van a la PAL para conocer la fase de E. |
| U6B | AND de FC0–FC2: nivel alto = ciclo de espacio de CPU (FC=111). |
| U6A + U5A | BERR = NAND(AVEC, CPU, FPU\_CS). Un ciclo de espacio de CPU que ni la PAL ni la FPU reclaman produce bus error (breakpoint, p. ej.). |
| U6C, U8B–U8F, U5D, RN2A | Decodificación de la ROM. Los inversores de colector abierto U8B–U8F forman un AND cableado sobre el net EPROM, con pull-up RN2A: EPROM está alto cuando A16–A19 son 0 y no se cumple A14·A15, es decir, 0x0000–0xBFFF. U5D lo invierte y da ROM\_CS (/CE de U9). U8A invierte R/W y da el /OE de U9 (activo solo en lecturas). |
| U9 | ROM W27C512 con direcciones y datos permutados (ver sección de la ROM). Su /OE lo da U8A (R/W invertido), así que solo saca datos en lecturas. |
| U3 (68881) | Se conecta a las 32 líneas de datos, con A0 y SIZE a +5V (32 bits estático) y A1–A4 a la CPU. Activa DSACK1 solo (16 bits) o ambos (32 bits) según el registro, así el 68020 cambia dinámicamente de puerto. |
| U10 (PAL20R4) | Genera AS\_68K8, DS\_68K8, ACK2, AVEC y FPU\_CS (ver las secciones de ecuaciones). |

**Tipos de ciclo.** La PAL distingue cuatro casos:

1. **ROM interna:** la PAL activa ACK2 sin esperar al QL. El QL no ve DS.
2. **Ciclo normal del QL:** la PAL activa AS\_68K8 un flanco de CLK\_68K8 después de AS2 y DS\_68K8 con él (lectura) o un flanco más tarde (escritura). Termina cuando llega DTACK\_68K8.
3. **Ciclo VPA (periférico tipo 6800, p. ej. el RTC):** la PAL espera a un pulso completo de E y activa ACK2 justo tras su flanco de bajada.
4. **Espacio de CPU:** AS\_68K8 queda inactivo. Con A19=1 y A17=1 es reconocimiento de interrupción y la PAL activa AVEC (autovector). Con A19=0 y A17=1 es un ciclo de coprocesador y activa FPU\_CS. Cualquier otro caso da BERR.

**Relojes.** La 68020 y la 68881 usan los 12 MHz de Y1; el QL sigue con sus 7,5 MHz (CLK\_68K8) y no nota el cambio. No hay relación fija entre ambos relojes (12 / 7,5 = 1,6), pero la interfaz es asíncrona: U4A y U4B sincronizan los ciclos y la CPU espera por DSACK. La simulación de U10 a 12, 12,5 y 16 MHz no da errores. La 68020 admite desde 8 MHz hasta el máximo de su grado, así que 12 MHz vale para cualquiera.

| Reloj de la 68020 | Chips necesarios | Comentario |
| --- | --- | --- |
| 12 MHz (actual) | 68020 y 68881 de cualquier grado | La 68881 de 12,5 MHz sirve. |
| 16 MHz | 68020 y 68881 de 16 MHz | Simulado sin errores. Cristal fundamental con los inversores LS04 de U5, al límite habitual. |
| 20 MHz o más | 68020 y 68881 de ese grado | No simulado. Los LS04 del oscilador son poco fiables a esa frecuencia (mejor un módulo oscilador), y FPU\_CS y BERR, hechos con puertas LS, pierden margen. Pasar U4, U5, U6 y U8 a 74HCT, 74ACT o 74F y usar una GAL de 7 ns o menos recupera margen. Para 33 MHz hacen falta además 68020 y 68881 de 33 MHz, más desacoplo y cuidar la integridad de señal en el bus del QL. Con el bus de 8 bits la mejora es pequeña. |

El software sí puede notar el cambio: los bucles de espera del sistema operativo dependen de la velocidad de la CPU, y la guía de CST dice que en el Thor 20 hubo que ajustar constantes de tiempo. Hay que comprobarlo en la ROM elegida.

## U10 como PAL20R4

Estas ecuaciones valen para el chip original de la placa (PAL20R4).

Pinout de la 20R4: reloj en el pin 1, /OE de los registros en el 13, registradas 17–20, combinacionales con realimentación 15, 16, 21 y 22, solo entradas 2–11, 14 y 23.

| Pin | Señal | Tipo | Función |
| --- | --- | --- | --- |
| 1 | CLK | reloj | CLK\_68K8 (7,5 MHz) |
| 2 | AS2 | entrada, activa baja | /Q de U4A |
| 3 | DTACK | entrada, activa baja | DTACK\_68K8 |
| 4 | RW | entrada | 1 = lectura |
| 5 | E | entrada | Q2 de U7 |
| 6 | A19 | entrada |  |
| 7 | A17 | entrada |  |
| 8 | EPROM | entrada | 1 = dirección en la ROM |
| 9 | Q3 | entrada | U7 |
| 10 | Q0 | entrada | U7 |
| 11 | Q1 | entrada | U7 |
| 13 | EN2 | /OE | conectado a AS\_68K8 (pin 16) |
| 14 | CPU | entrada | salida de U6B (FC=111) |
| 15 | DSL | combinacional, activa baja | DS\_68K8 → U1.29 |
| 16 | ASL | combinacional, activa baja | AS\_68K8 → U1.28 y EN2 |
| 17 | ST | registro interno | sin conexión externa |
| 18 | VP | registro interno | sin conexión externa |
| 19 | ARM | registro interno | sin conexión externa |
| 20 | ACK2 | registrada, activa baja | → U5E → reloj de U4B |
| 21 | FPUCS | combinacional, activa baja | /CS de la 68881 y U6A |
| 22 | AVEC | combinacional, activa baja | AVEC de la 68020 y U6A |
| 23 | VPA | entrada, activa baja | VPA\_68K8 |

Las ecuaciones están en lógica positiva (1 = señal activa; en la declaración de pines CUPL, las señales activas bajas llevan «!»). `.d` = entrada D del registro. `#` = OR, `&` = AND.

```
ARM.d = AS2 & !CPU
ST.d  = AS2 & ARM
VP.d  = AS2 & ARM & DSL & VPA & (VP # (!Q3 & !E & Q1 & Q0))

ACK2.d = AS2 & !CPU & EPROM
       # AS2 & ARM & ACK2
       # AS2 & ARM & DSL & DTACK & !VPA
       # AS2 & ARM & DSL & VP & Q3 & !E & !Q1 & !Q0

ASL = AS2 & ARM
DSL = AS2 & ARM & !EPROM & RW
    # AS2 & ARM & !EPROM & !RW & ST & !ACK2

AVEC  = CPU & A19 & A17
FPUCS = CPU & !A19 & A17
```

**Cómo funciona.**

- ARM retrasa AS\_68K8 un flanco de CLK\_68K8 respecto a AS2. Entre ciclos, AS\_68K8 queda inactivo al menos un flanco.
- ST retrasa otro flanco el DS de las escrituras, y estas terminan en cuanto hay confirmación, para que el dato de la CPU siga válido. Las lecturas mantienen DS hasta que acaba AS, para dar tiempo a que la CPU lo lea.
- ACK2 se mantiene hasta el final del ciclo (se borra cuando AS2 vuelve a 1), así que baja una sola vez por ciclo y dispara U4B.
- VP se arma en la cuenta 3 de U7, justo antes de que suba E; el ACK de los ciclos VPA llega en la cuenta 8, justo después de que E baje, con DS activo durante todo el pulso de E.
- Como EN2 viene de ASL, ACK2 solo se ve cuando AS\_68K8 está activo; el resto del tiempo es alta impedancia. Por eso ACK2 lleva el pull-up R2 de 4,7 kΩ, soldado en la patilla de U5, fuera de la PCB.

Validación: simulación propia (U4A, U4B, U7, la PAL y modelos de CPU y bus QL) con unos 960 ciclos al azar a 12,5 y 16 MHz, sin errores en conteo de DSACK, forma de DS, VPA ni BERR. No se ha compilado con CUPL ni probado en hardware. El fichero `thor20_u10_pal20r4.pld` entregado antes tiene la misma lógica.

## U10 como GAL22V10 (y GAL20V8)

La GAL22V10 entra en el mismo zócalo de 24 pines y es el chip del símbolo KiCad.

La lógica es la misma que en la PAL20R4. Cambia el uso de los pines:

- El pin 13 es una entrada normal, ya no el /OE de los registros. Puedes dejarlo conectado a AS\_68K8 sin efecto.
- Cada macrocelda tiene su propio habilitador, así que ACK2 puede estar siempre activada. No hace falta pull-up en U5.11: los registros arrancan a 0 y ACK2 queda inactiva fuera de ciclo.
- Los pines 14 (CPU) y 23 (VPA) usan macroceldas de E/S con la salida deshabilitada, es decir, solo como entradas.
- ST, VP y ARM (pines 17–19) siguen siendo registros internos sin conexión externa.

```
Device G22V10;

Pin 1  = CLK;      Pin 2  = !AS2;    Pin 3  = !DTACK;  Pin 4  = RW;
Pin 5  = E;        Pin 6  = A19;     Pin 7  = A17;     Pin 8  = EPROM;
Pin 9  = Q3;       Pin 10 = Q0;      Pin 11 = Q1;      Pin 13 = AS_IN;   /* sin uso */
Pin 14 = CPU;      Pin 23 = !VPA;
Pin 15 = !DSL;     Pin 16 = !ASL;    Pin 20 = !ACK2;
Pin 21 = !FPUCS;   Pin 22 = !AVEC;
Pin 17 = ST;       Pin 18 = VP;      Pin 19 = ARM;

ARM.d = AS2 & !CPU;
ST.d  = AS2 & ARM;
VP.d  = AS2 & ARM & DSL & VPA & (VP # (!Q3 & !E & Q1 & Q0));

ACK2.d = AS2 & !CPU & EPROM
       # AS2 & ARM & ACK2
       # AS2 & ARM & DSL & DTACK & !VPA
       # AS2 & ARM & DSL & VP & Q3 & !E & !Q1 & !Q0;

ASL = AS2 & ARM;
DSL = AS2 & ARM & !EPROM & RW
    # AS2 & ARM & !EPROM & !RW & ST & !ACK2;

AVEC  = CPU & A19 & A17;
FPUCS = CPU & !A19 & A17;
```

En la 22V10 se configura cada macrocelda como registrada (ARM, ST, VP, ACK2) o combinacional (DSL, ASL, FPUCS, AVEC) con la polaridad indicada por «!»; el compilador lo hace al ajustar. Los registros se ponen a 0 al conectar la alimentación.

Igual que antes: estas ecuaciones son mías, validadas solo por simulación; no están compiladas con CUPL.

## ROM U9

U9 (W27C512, 64 KB) responde en 0x0000–0xBFFF, los 48 KB de la ROM del QL, y deja 0xC000–0xFFFF libre para el cartucho. La decodificación (A16–A19 a 0 y no A14·A15) viene de U6C, U8B–U8F y U5D, y U8A se usa aparte, para el /OE (R/W invertido). A20 y superiores no se decodifican, así que la ventana se repite en todo el espacio de direcciones de la CPU.

Las direcciones y los datos están permutados para facilitar el trazado, como era habitual en CST. La imagen que se programa tiene que seguir esa permutación.

| Pin de dirección de U9 | A0 | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Línea de la CPU | A8 | A1 | A2 | A14 | A13 | A5 | A0 | A7 | A6 | A9 | A10 | A11 | A12 | A4 | A3 | A15 |

| Pin de datos de U9 | D0 | D1 | D2 | D3 | D4 | D5 | D6 | D7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Línea de la CPU | D31 | D30 | D29 | D26 | D25 | D27 | D24 | D28 |
| Bit del byte del QL | 7 | 6 | 5 | 2 | 1 | 3 | 0 | 4 |

**Contenido.** Una Minerva estándar para QL es la opción natural: es una imagen de 48 KB que ocupa justo la ventana. El script `rom_image.py` (entregado antes) toma esa imagen tal como la ve la CPU desde 0x0000, aplica ambas permutaciones y genera el fichero de 64 KB para el programador. Lo no usado queda a 0xFF y lo que pase de 0xBFFF se ignora. Su autotest comprueba que decodificar la imagen con el cableado devuelve la imagen original.

No he generado ni incluido ninguna ROM: la imagen de Minerva no está disponible aquí y no he podido probarla.

**Compatibilidad con la 68020.** Se asume que la Minerva elegida soporta la 68020. La guía de CST recuerda que el QDOS del Thor 20 necesitó cambios (caché, modo supervisor, `MOVE SR` y constantes de tiempo).

## Pendientes

- [ ] Mejora futura: JP1 de 3 pines (U6A pin 13 a FPU\_CS o a +5V) o resistencia serie de unos 330 Ω entre U10 pin 21 y ese nodo; ahora no existe en la PCB.
- [ ] Añadir el pull-up a +5V del nodo U8A pin 2 / U9 pin 22 (una sección libre de RN2).
- [ ] Comprobar que la ROM de la placa QL no se habilita solo con AS (sin DS), por la contención con U9.
- [ ] Fijar el valor de C9.
- [ ] Generar la imagen de U9 a partir de la Minerva (se asume que soporta 68020) con `rom_image.py`.
- [ ] Compilar las ecuaciones con CUPL y probarlas con un analizador lógico: ciclo QL, ciclo VPA con el RTC, reconocimiento de interrupción y ciclo de FPU.
