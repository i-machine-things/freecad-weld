# Weld

A FreeCAD workbench for parametric weld beads and fabrication labor tracking. Work in progress.

## Commands

- **Add Weld Bead** adds a weld bead to the active document. In the task panel, pick the joint type (fillet or butt), the size, the process (MIG, TIG or SMAW) and the position (1F to 4F). Select an edge in the 3D view and click OK. The bead is swept along that edge and goes in a `Welds` group.
- **Update Labor Sheet** writes one row per weld bead to a `WeldLabor` spreadsheet: type, process, position, size, length and estimated weld time. Adding a bead updates it too.

A bead's weld time is its length divided by a deposition rate for its process and position, from 60 to 300 mm a minute. The rates are approximate mid-range figures.

## Installing

Install it with FreeCAD's Addon Manager, from the catalog at <https://i-machine-things.github.io/freecad-addons/>. You can also add `https://github.com/i-machine-things/freecad-weld` with branch `master` as a custom repository in the Addon Manager's settings. Restart FreeCAD and pick **Weld** in the workbench selector.

## License

LGPL-2.1-or-later. See [LICENSE](LICENSE).
