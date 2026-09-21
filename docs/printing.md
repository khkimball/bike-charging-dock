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

The base is built round the Anker A2154 (77 x 82 x 33 mm, six ports in one
row, no status LED): change `measurements.CHARGER` and the fence, the port
room and the cable loops all follow from it. The charger stands with its
back against the -X end wall, the way the Trek CHRGtime manual shows its
own supply: the fence is a U (two side walls and a front wall, 8 mm tall)
and the cavity's end wall is the fourth side, a fit clearance behind the
charger's inlet face.

The base prints open-top-up. The AC cord port in the -X end wall is sized
from the moulded C7 cord end, which makes it too wide to bridge, so it is
roofed with a 45 degree peak instead: it needs no support. Directly above it
in the same wall -- where the Trek CHRGtime puts its own -- sits the device
cable escape port, a closed 16 x 8 mm hole that clears the peak of the cord
roof by 1 mm and stops well below the rebate ledge. The ceilings that do
bridge are that escape port (16 mm), the crown of each cable loop (10 mm)
and the four foot recesses in the underside -- all short bridges the printer
clears without supports. There is no LED window in the +X end wall: the
A2154 has no status LED, so that wall is blind. Both -X wall ports are
closed holes rather than notches, so the rim and the rebate ledge stay
continuous all the way round.

The mains cord plugs in from outside: push the moulded C7 end through the
cord port and it goes straight into the inlet, which sits right behind the
wall. Nothing about the cord is inside the dock but the last few
millimetres of it. Everything from the charger's port face to the +X cavity
wall -- 138 mm as the parts stand -- is free floor for the plugs and their
cables. There are 2 mm of free floor behind the charger's back face, room
for an inlet shroud or a label boss to stand proud of it.

Inside the cavity, a row of six inverted-U cable loops stands on the floor
clear of the plugs in front of the charger -- 24 mm out from the fence wall,
about 5 mm past the end of a USB-A overmold -- one over each charger port and
on the same 12.5 mm port pitch. With the charger at the end wall the row
lands near the middle of the cavity. They are the CHRGtime's under-tray
cable bar, printed in place: each has a 10 mm wide by 12 mm tall window and
the row rises 15 mm off the cavity floor, against a rebate ledge that sits
`BASE_H - REBATE_D` above the bed -- 49.6 mm as the parts stand -- so the
seated tray is nowhere near them. Nothing about them needs support. A loop
is 16 mm wide and the pitch is 12.5, so the row prints as one continuous
bar, with a window over each port and a 2.5 mm post between windows.

Take each device cable out of its charger port toward the middle of the
cavity and through its loop: that is all the loops are for, holding the six
cables in a row where they leave the plugs instead of letting them knot up
together. Past the row they fan out across the floor to whichever bay's
cutout they belong to. The tie-down grid runs down both sides of the row --
including the strip between the fence and the loops, where the plugs stand
-- and takes a cable tie for anything that will not stay put.

There are six loops for six charger ports, but not every bay feeds one from
above. The Roam sits in the -X column of the tray, over the charger's own
end of the cavity, so its cable runs the other way: out of its charger port,
back along the -Y side of the charger past the fence, and straight up
through its cutout -- which clears the charger in Y, so the cable drops to
the cavity floor beside it rather than over its top. It never passes under a
loop.

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
