# Printing on the Snapmaker U1

Slicer: Snapmaker Orca (open the .stl files; Orca rejects generic 3MF), installed as a Flatpak.

    flatpak run io.github.Snapmaker.Snapmaker_Orca

Printer: Snapmaker U1. Material: PETG for the final set (fit-checking in PLA
is fine). Profile: 0.4 mm nozzle, 0.2 mm layers; 0.28 mm Extra Draft is an
option for the base and lid, see below.

| Part | Orientation | Walls | Infill | Supports |
|---|---|---|---|---|
| coupon_plate, coupon_peg | as exported | 3 | 15 % | none |
| hinge_coupon_base | as exported | 3 | 15 % | under the socket blocks and lip risers |
| hinge_coupon_lid | as exported: leaf up | 3 | 15 % | under the pins if needed |
| tray | as exported: plate on the bed, bays up | 3 | 15 % | none |
| base | as exported: open top up | 3 | 15 % | none |
| lid | as exported: top face down, hinge leaves up | 3 | 15 % | under the leaf pins if needed (paint-on) |

There are no dividers to print: the tray's dividers are fixed and print with it.

## Efficiency

`uv run python scripts/slice_report.py` slices the exported base, tray and
lid headlessly with these settings and prints time and grams next to the v1
prototype (`--layer 0.28` for the draft profile). Last measured
2026-09-24 (concealed leaf hinge), 0.20 mm PETG: v1 set 14 h 00 m / 582 g,
this set 9 h 35 m / 411 g (time -32 %, filament -30 %). Re-run it after any
change to params.py and before a reprint.

`uv run python scripts/orca_project.py` builds `out/orca/dock_plates.3mf`,
one Orca project with each part on its own named plate (Base, Tray, Lid,
Hinge coupon, Clearance coupon) on the same U1 / 0.20 / PETG profiles. Run
it after `export_all.py` (and `slice_report.py` once, which writes the
profiles it loads), then open the project in Orca. Supports, the base's
colour change and the prime tower are set in the GUI.

The base and lid can also print at 0.28 mm Extra Draft for a little more
time saved; the tray's cable cutouts and fillets look better at 0.20.

## Two-tone base

The base is two colours like the Trek CHRGtime: a dark foot band and a light
body. The colour line is the V groove round the foot at `BAND_H` (8 mm);
it is 1.2 mm tall, so any layer inside it works at 0.20 or 0.28:

1. In Orca, load the dark filament in one toolhead and the light in another,
   and set the base's object filament to the dark one.
2. Add a filament change to the light filament at the first layer above
   8.0 mm -- 8.2 mm at 0.20 -- on the layer slider ("+" or right-click,
   "Change filament"). 8.0 mm is also the charger fence's top, so the whole
   fence prints dark, and 8.2 is still inside the groove.
3. Turn the prime/wipe tower off for this plate (Others > Prime tower): one
   change on a toolchanger does not need it, and the tower would cost more
   than the whole change.

Print the lid and the tray in the dark colour.

## Geometry notes

Every outer face leans 15 degrees (the CHRGtime's angle), from the lid top
down to the foot; the corners run from R30 at the rim to about R8 at the
bed. The base walls lean outward as they rise, well inside 45 degrees, so
the shell prints unsupported. Every cable hole -- the AC cord port, the two
escape ports and the tray's cutouts -- is an oval, so the ports' flat heads
(10 mm at most) and the foot recesses are short bridges. The only supports
are under the hinge's four socket blocks and their stop-lip risers, inside
the back wall (paint them on).

The charger (Anker A2154) stands in a U fence backed onto the -X end wall;
its arms run into the leaning end wall and fuse with it, its top is the
colour line, and the pocket floor is filleted along its two side walls to
follow the charger's rounded bottom edges (`CHARGER.edge_r`). The
mains cord plugs in from outside through the cord port, sized for a
figure-8 (C7) end; if your cord's moulding is square-cornered, measure it
(docs/measuring.md) before printing the base. Two oval escape
ports, one each side of the charger in the same wall, let a cable out to
charge something outside the dock.

The tray rests on a ledge ring 0.3 mm below the rim, so the lid lands on the
base. Lift it out by its walls. The cable
cutouts at the bays' outer ends drop past the leaning base wall: the cable
falls clear for at least 15 mm, then follows the wall down.

## Hinge

A concealed leaf hinge, after the Trek CHRGtime's, at two stations on the
+Y long side. At each, a leaf on the lid hangs into a notch in the base's
back wall, flush with it, and Ø6 pins on the leaf's ends sit in sockets in
blocks on the inside of the wall. From behind, a closed dock shows only the
two leaves in their notches and a 1.5 mm gap along the back seam (the
lid's back is raised off the rim so it can turn about a pivot inside the
wall line).

To fit the lid: set it closed on the rim with the leaves over their notches
and press the back edge down until the pins snap into their sockets; to
take it off, lift the back edge straight up. The snap is deliberately
light. Opened fully it stops at about 101 degrees, the leaves' ends resting
on small lips on the socket blocks.

Print the hinge coupon first: it is one station cut from the real base and
lid. If the pins will not snap in, or pop out, change `SNAP` in
`src/dock/hinge.py`; if the hinge binds, raise `BORE_CLR`; check it stops
at about 100 degrees and the lips hold. Then re-export.

## Print order and measurement cycle

1. **coupons** -- the clearance coupon and the hinge coupon, in the final
   material. Set `CLR_FIT` (params.py) and `SNAP` / `BORE_CLR` (hinge.py).
2. **measurements** -- fill in `src/dock/measurements.py` per
   `docs/measuring.md`; `CHARGER.edge_r` is new.
3. **tray** -- check each device seats in its bay and its cable plugs in
   cleanly through the cutout.
4. **base** -- check the charger drops into the fence and the tray seats on
   the ledge.
5. **lid** -- check it snaps into its sockets, stays on resting fully open,
   swings shut flush with the
   rim, and clears every device.

Re-run `uv run python scripts/export_all.py` after any parameter change, and
`uv run pytest` before reprinting.

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
