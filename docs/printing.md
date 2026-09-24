# Printing on the Snapmaker U1

Slicer: Snapmaker Orca (open the .stl files; Orca rejects generic 3MF), installed as a Flatpak.

    flatpak run io.github.Snapmaker.Snapmaker_Orca

Printer: Snapmaker U1. Material: PETG for the final set (fit-checking in PLA
is fine). Profile: 0.4 mm nozzle, 0.2 mm layers; 0.28 mm Extra Draft is an
option for the base and lid, see below.

| Part | Orientation | Walls | Infill | Supports |
|---|---|---|---|---|
| coupon_plate, coupon_peg | as exported | 3 | 15 % | none |
| hinge_coupon_base, hinge_coupon_lid | as exported | 3 | 15 % | none |
| tray | as exported: plate on the bed, bays up | 3 | 15 % | none |
| base | as exported: open top up | 3 | 15 % | the cord port ceiling only (26 mm); paint-on or "support on build plate only" |
| lid | as exported: top face down, hinge hooks up | 3 | 15 % | none |

There are no dividers to print: the tray's dividers are fixed and print with it.

## Efficiency

`uv run python scripts/slice_report.py` slices the exported base, tray and
lid headlessly with these settings and prints time and grams next to the v1
prototype (`--layer 0.28` for the draft profile). Measured when the design
was planned, 0.20 mm PETG: v1 set 14 h 00 m / 582 g, this set 9 h 53 m /
412 g (-29 %). Re-run it after any change to params.py and before a
reprint. At 0.28 mm Extra Draft, this set measures 9 h 34 m / 418 g (time
-32 %, filament -28 %).

The base and lid can also print at 0.28 mm Extra Draft for a little more
time saved; the tray's cable cutouts and fillets look better at 0.20.

## Two-tone base

The base is two colours like the Trek CHRGtime: a dark foot band and a light
body. The colour line is the V groove round the foot at `BAND_H` (8 mm);
it is 1.2 mm tall, so any layer inside it works at 0.20 or 0.28:

1. In Orca, load the dark filament in one toolhead and the light in another,
   and set the base's object filament to the dark one.
2. Add a filament change at a layer inside the groove -- 8.0 mm at 0.20 --
   to the light filament (right-click the layer slider, "Change filament").
3. Turn the prime/wipe tower off for this plate (Others > Prime tower): one
   change on a toolchanger does not need it, and the tower would cost more
   than the whole change.

Print the lid and the tray in the dark colour.

## Geometry notes

Every outer face leans 15 degrees (the CHRGtime's angle), from the lid top
down to the foot; the corners run from R30 at the rim to about R8 at the
bed. The base walls lean outward as they rise, well inside 45 degrees, so
the whole shell prints unsupported; the only supported ceiling is the AC
cord port's flat top (`base.SUPPORTED_CEILINGS`). The escape ports' heads,
the foot recesses and the hinge pins' 3 mm flats are short bridges.

The charger (Anker A2154) stands in a U fence backed onto the -X end wall;
its corners follow the charger's rounded edges (`CHARGER.corner_r`). The
mains cord plugs in from outside through the cord port. Two oval escape
ports, one each side of the charger in the same wall, let a cable out to
charge something outside the dock.

The tray rests on a ledge ring 0.3 mm below the rim, so the lid lands on the
base. Lift it out by the finger slot in the centre partition. The cable
cutouts at the bays' outer ends drop past the leaning base wall: the cable
falls clear for at least 15 mm, then follows the wall down.

## Hinge

The lid hinges on the +Y long side at two stations. The base carries the
pins, the lid the hooks. To fit the lid: open it to full (about 110
degrees, where the heel tab in the middle rests on the base's back wall),
line the hooks up over the pins, and push it down along the wall until the
hooks snap on. To take it off, open it fully and pull it up along the wall.
A closed lid lifted straight up stays on.

Print the hinge coupon first: it is one station on a short stretch of wall
and lid. If the hook will not snap on, or falls off, change `SNAP` in
`src/dock/hinge.py`; if the hinge binds, raise `BORE_CLR`. Then re-export.

## Print order and measurement cycle

1. **coupons** -- the clearance coupon and the hinge coupon, in the final
   material. Set `CLR_FIT` (params.py) and `SNAP` / `BORE_CLR` (hinge.py).
2. **measurements** -- fill in `src/dock/measurements.py` per
   `docs/measuring.md`; `CHARGER.corner_r` is new.
3. **tray** -- check each device seats in its bay and its cable plugs in
   cleanly through the cutout.
4. **base** -- check the charger drops into the fence and the tray seats on
   the ledge.
5. **lid** -- check it snaps on at full open, swings shut flush with the
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
