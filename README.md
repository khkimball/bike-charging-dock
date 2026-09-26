# Bike charging dock

A 3D-printed desk dock for cycling electronics. A multi-port USB charger is
hidden inside, cables run up through the tray to each device, and a hinged lid
closes over them. The shell tapers at 15 degrees on every side and prints in
two colours, a dark foot band and a light body.

![The dock, open](docs/images/dock_open.png)

| Closed | Tray from above | Base from behind |
|---|---|---|
| ![Closed](docs/images/dock_closed.png) | ![Tray](docs/images/tray_top.png) | ![Base](docs/images/base_back.png) |

- About 250 x 184 x 88 mm closed. The largest part, the lid, is 249.5 x 184.3 mm, so it needs a bed at least 250 mm across.
- Bays are sized for a Wahoo Elemnt Roam 3, a Bontrager Ion headlight and a Wahoo Trackr radar, plus one open bay.
- The charger is an Anker A2154 six-port desktop charger. It stands in a fence in the base, and its mains cord comes in through a port in the end wall.
- Two escape ports beside the charger let a cable out to charge something outside the dock.
- The lid uses a concealed leaf hinge with no hardware. Its printed pins snap into the base, and the lid opens to about 100 degrees and stops there.
- All of it is fully parametric [build123d](https://github.com/gumyr/build123d) code. The tests check the fit, the swing of the lid and printability (no overhang past 45 degrees).

The shape is inspired by the Trek CHRGtime charging station. This project is
not affiliated with or endorsed by Trek.

## What you need

- **Charger:** [Anker Desktop Charger, 112W Max, 6 ports](https://www.amazon.com/dp/B0CM6WDH6S), model A2154 (3 USB-C and 3 USB-A, 77 x 82 x 33 mm). The base's fence and ports are sized for it; check the model number on the label if you buy it elsewhere. Any other charger needs its size entered in `src/dock/measurements.py` (see [Adapt it](#adapt-it)).
- **Cables:** one USB charging cable per device; the charger comes with its mains cord but no USB cables.

## Print it

Ready-made STL, STEP and an Orca Slicer project are on the
[releases page](../../releases). The design was printed and tested on a
Snapmaker U1 in PETG; PLA works as well.

| Part | Orientation | Supports |
|---|---|---|
| hinge_test_base, hinge_test_lid | as exported | none (pins: only if they droop) |
| fit_test_plate, fit_test_peg | as exported | none |
| tray | plate down | none |
| base | open top up | **off**, or auto supports will fill the ports |
| lid | top face down | under the leaf pins only if needed |

Settings: 0.4 mm nozzle, 0.2 mm layers, 3 walls, 15 % infill.

- **Print the two test pieces first.** The hinge test is one hinge station cut from the real base and lid. It shows whether the pins snap in and turn freely on your printer before you commit to the big parts. The fit test (a plate of graded holes and a peg) checks the general clearance.
- **Two-tone base:** start in the dark filament and change to the light one at the first layer above 8.0 mm (8.2 mm at 0.2 mm layers). The groove round the foot hides the seam, and the charger fence prints fully dark. With a single-change toolchanger, turn the prime tower off.
- **Fit the lid:** set it on the rim with the leaves over their notches and press the back edge down until the pins snap in. Lift the back edge straight up to take it off.

There is more detail in [docs/printing.md](docs/printing.md).

## Adapt it

Everything is driven by a few files:

- `src/dock/measurements.py` holds your devices, charger and plugs. Measure them with calipers as described in [docs/measuring.md](docs/measuring.md).
- `src/dock/layout.py` sets where the bays go.
- `src/dock/params.py` holds the design rules: wall thickness, clearances, draft angle, colour band.
- `src/dock/hinge.py` sets the hinge fit (`SNAP`, `BORE_CLR`). Tune it with the hinge test.

Then rebuild:

    uv venv --python 3.12 && uv pip install -e ".[dev]"
    uv run pytest                              # fit, swing and printability checks
    uv run python scripts/export_all.py        # out/*.stl and *.step
    uv run python scripts/orca_project.py      # out/orca/dock_plates.3mf, one part per plate
    uv run python scripts/render.py            # docs/images/*.png
    uv run python -m ocp_vscode                # optional viewer at http://localhost:3939

build123d needs Python 3.12. The design history is in
[docs/superpowers/](docs/superpowers/): the specs and plans for each version.

## Parts

- **tray**: a flat plate with four device bays and fixed, filleted dividers. Each bay has an oval cable cutout at its outer end.
- **base**: the tapered, two-tone lower shell. It hides the charger and the cable slack, and carries the tray on a ledge.
- **lid**: a tapered cap whose hinge leaves hang into notches in the base's back wall.
- **test prints**: the fit test (a plate and a peg) and the hinge test.

## License

- Models and images: [CC BY 4.0](LICENSE-models.md).
- Code: [MIT](LICENSE).
