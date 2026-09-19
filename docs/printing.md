# Printing on the Snapmaker U1

Slicer: Snapmaker Orca (open the .stl files; Orca rejects generic 3MF), installed as a Flatpak.

    flatpak run io.github.Snapmaker.Snapmaker_Orca

Printer: Snapmaker U1. Material: PETG. Profile: 0.4 mm nozzle, 0.2 mm layers.

| Part | Orientation | Walls | Infill | Supports |
|---|---|---|---|---|
| coupon_plate, coupon_peg | as exported | 3 | 15 % | none |
| cradle_* | as exported (pocket up) | 3 | 15 % | none |
| divider | as exported | 3 | 100 % | none |
| deck | as exported: flat 8 mm plate on the bed, cradles up | 3 | 15 % | none |
| base | as exported: open top up | 3 | 15 % | none |

The deck is a flat plate at the bed face with the cradles built up from its
top, so it prints with no overhangs and no supports.

The base prints open-top-up. Its only ceilings are the rear escape port, the
LED window in the +X end wall and the four foot recesses in the underside --
all short bridges the printer clears without supports. (The AC cord notch in
the -X end wall is open to the top, so it has no ceiling at all.)

The Roam cradle's plug channel is bridged by the 2.4 mm pocket wall above it;
everything else on the deck is within 45 degrees of vertical.

## Print order and measurement loop

1. **coupon** -- print `coupon_plate`/`coupon_peg` first to verify the fit
   clearances (`CLR_FIT`, `CLR_DEVICE`, `CLR_RAIL`) in `params.py` against the
   real hardware.
2. **set clearances** -- adjust `params.py` from the coupon fit, and fill in
   `src/dock/measurements.py` per `docs/measuring.md`.
3. **cradles** -- print `cradle_roam`, `cradle_ion`, `cradle_trackr` and check
   each device seats and its cable plugs in cleanly.
4. **deck** -- print the full deck once the cradles are confirmed.
5. **base** -- print last, once the deck's footprint and the charger
   measurements are locked in.

Re-run `uv run python scripts/export_all.py` after any parameter change, and
re-run `uv run pytest` before reprinting. Open the refreshed `out/<part>.stl`
in Snapmaker Orca for each iteration of the loop.

## Flatpak note

The Snapmaker Orca Flatpak has no host filesystem access by default, so
`flatpak run ... out/part.stl` opens the app but reports "no geometry data".
Either grant it this folder once:

    flatpak override --user --filesystem=$PWD io.github.Snapmaker.Snapmaker_Orca

or launch it without arguments and use File > Import (the file portal).

The GUI also changes its working directory after launch, so pass ABSOLUTE
paths on the command line (`$PWD/out/part.stl`); relative paths fail with
"no geometry data".

To verify every part loads in Orca without opening the GUI:

    scripts/orca_check.sh

It writes Orca project files to out/orca/<part>.3mf, which File > Open
Project in Orca accepts directly.
