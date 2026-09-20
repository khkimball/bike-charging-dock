# Printing on the Snapmaker U1

Slicer: Snapmaker Orca (open the .stl files; Orca rejects generic 3MF), installed as a Flatpak.

    flatpak run io.github.Snapmaker.Snapmaker_Orca

Printer: Snapmaker U1. Material: fit-checking in PLA; the final set is
printed in PETG. Profile: 0.4 mm nozzle, 0.2 mm layers.

| Part | Orientation | Walls | Infill | Supports |
|---|---|---|---|---|
| coupon_plate, coupon_peg | as exported | 3 | 15 % | none |
| divider (print two) | as exported: stands on its long bottom edge, the two end rails acting as feet -- use a brim | 3 | 100 % | none |
| tray | as exported: flat plate on the bed, bays up | 3 | 15 % | none |
| base | as exported: open top up | 3 | 15 % | none |
| lid | as exported: top face down, skirt up | 3 | 15 % | none |

The tray is a flat plate at the bed face with its bay walls built up from its
top, so it prints with no overhangs and no supports. The Roam sits against
the +Y (back) wall of its bay, clear of its cable cutout at the -Y end; the
Ion and Trackr sit against the partition wall, clear of their cutouts at the
+X end.

The base prints open-top-up. The AC cord port in the -X end wall is sized
from the moulded C7 cord end, which makes it too wide to bridge, so it is
roofed with a 45 degree peak instead: it needs no support. The only real
ceilings left are the rear escape port (19 mm bridge), the LED window in the
+X end wall (4 mm) and the four foot recesses in the underside -- all short
bridges the printer clears without supports. The escape port lets a spare
device cable leave through the rear wall; the AC cord port is a closed hole,
not a notch, so the mains cord is the only thing that leaves through the -X
wall.

The tray sits flush with the base's rim, so each end of the rim carries a
finger notch (40 mm wide, 15 mm down from the rim, corners rounded R5):
that is what you lift the tray out by. They cut the rim only -- the rebate
ledge the tray lands on is continuous all the way round -- and the lid's
skirt covers only the top 8 mm of them.

The lid prints top-face-down with its skirt standing up, so its only
downward faces are the bed face and its 45 degree chamfer -- no overhang, no
bridge, no supports.

## Print order and measurement loop

1. **coupon** -- print `coupon_plate`/`coupon_peg` first, in PLA, to verify
   the fit clearances (`CLR_FIT`, `CLR_RAIL`) in `params.py` against the real
   hardware.
2. **set clearances** -- adjust `params.py` from the coupon fit, and fill in
   `src/dock/measurements.py` per `docs/measuring.md`.
3. **tray + dividers** -- print the tray and two `divider`s (they are half a
   millimetre shorter than the bays are deep, so the lid lands on the tray
   rim and never on a divider that has not quite seated); check each
   device seats in its bay, its cable plugs in cleanly through the cutout,
   and both dividers drop into their rail slots.
4. **base** -- print once the tray's footprint and the charger measurements
   are locked in; check the tray seats flush in the rebate.
5. **lid** -- print last, once the base and seated tray are confirmed to
   fit; check it drops over the base and clears every device.

Re-run `uv run python scripts/export_all.py` after any parameter change, and
re-run `uv run pytest` before reprinting. Open the refreshed `out/<part>.stl`
in Snapmaker Orca for each iteration of the loop.

Before printing the final set in PETG, reprint the coupon in PETG and
re-check `CLR_FIT`/`CLR_RAIL` against it -- the clearances in `params.py`
were set from a PLA coupon, and PETG's shrinkage differs from PLA's.

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
