/BLK1 = A19 * A18 * A17 * A16 * A15 * FC0 * /DS

> **Note (2026-11):** pin 7 of U4 (`DS`) is the bus /DS inverted by U2, so it is
> active HIGH and the term must be `DS`, not `/DS`. The complete reconstructed
> equations are in [U4.pld](U4.pld) and explained in
> [GAL_U4_U13.md](GAL_U4_U13.md).
