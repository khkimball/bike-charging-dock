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
| base | as exported: open top up | 3 | 15 % | yes, for the cord port ceiling only (26 mm bridge); paint-on/"support only the cord port" or normal supports -- the rest of the part is self-supporting |
| lid | as exported: top face down, skirt up | 3 | 15 % | none |

The tray is a flat plate at the bed face with its bay walls built up from its
top, so it prints with no overhangs and no supports. The Roam sits against
the +Y (back) wall of its bay, clear of its cable cutout at the -Y end; the
Ion and Trackr sit against the partition wall, clear of their cutouts at the
+X end.

The base is built round the Anker A2154 (77 x 82 x 33 mm, six ports in one
row, no status LED): change `measurements.CHARGER` and the fence and the
port room both follow from it. The charger stands with its
back against the -X end wall, the way the Trek CHRGtime manual shows its
own supply: the fence is a U (two side walls and a front wall, 8 mm tall)
and the cavity's end wall is the fourth side, a fit clearance behind the
charger's inlet face.

The base prints open-top-up. The AC cord port in the -X end wall is sized
from the moulded C7 cord end, which makes it a plain 26 x 16 mm rectangular
opening too wide to bridge: it is the one ceiling in the part that prints
with supports under it (`base.SUPPORTED_CEILINGS`), rather than the 45
degree peaked roof an earlier design used to dodge the bridge. Directly
above it in the same wall -- where the Trek CHRGtime puts its own -- sits
the device cable escape port, a closed hole that clears the cord port's
flat top by 1 mm and stops well below the rebate ledge. The other ceilings
that do bridge, all self-supporting, are that escape port (16 mm) and the
four foot recesses in the underside -- short bridges the printer clears
without supports. There is no LED window in the +X end wall: the A2154 has
no status LED, so that wall is blind. Both -X wall ports are closed holes
rather than notches, so the rim and the rebate ledge stay continuous all
the way round.

The mains cord plugs in from outside: push the moulded C7 end through the
cord port and it goes straight into the inlet, which sits right behind the
wall. Nothing about the cord is inside the dock but the last few
millimetres of it. Everything from the charger's port face to the +X cavity
wall -- 138 mm as the parts stand -- is free floor for the plugs and their
cables. There are 2 mm of free floor behind the charger's back face, room
for an inlet shroud or a label boss to stand proud of it.

The Anker A2154 ships with its own silicone cable-management block, so the
base prints nothing to route the device cables: each one runs from its
charger port straight across the cavity floor to whichever bay's cutout it
belongs to, and the charger's own block gathers the run. The tie-down grid
covers that floor -- from the fence's +X wall out to the +X cavity wall,
including the strip right in front of the port face where the plugs stand
-- and takes a cable tie for anything that will not stay put on its own.

The Roam sits in the -X column of the tray, over the charger's own end of
the cavity, so its cable runs out of its charger port, back along the -Y
side of the charger past the fence, and straight up through its cutout --
which clears the charger in Y, so the cable drops to the cavity floor
beside it rather than over its top.

The tray sits flush with the base's rim, so each end of the rim carries a
finger notch (40 mm wide, 15 mm down from the rim, corners rounded R5):
that is what you lift the tray out by. They cut the rim only -- the rebate
ledge the tray lands on is continuous all the way round -- and the lid's
skirt covers only the top 8 mm of them.

The lid prints top-face-down with its skirt standing up, so its only
downward faces are the bed face and its 45 degree chamfer -- no overhang, no
bridge, no supports.

## Print order and measurement cycle

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
in Snapmaker Orca for each pass through this cycle.

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
