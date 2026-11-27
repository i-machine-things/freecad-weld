# Coding Best Practices & Reminders

> **Style rule:** Notes must be clear and concise — 300 characters or less each. Group by topic, not by date. Whenever a PR review (CodeRabbit or human) catches a mistake, add or amend a note here right away so it isn't repeated.

## Addon Manager metadata

- `package.xml`'s `readme` URL takes the raw Markdown (`.../raw/<branch>/README.md`), not the `blob` page: the Addon Manager fetches and renders the Markdown itself, logs that it expects raw, and rewrites `/blob/` to `/raw/` anyway.
- Only link URLs in docs that already resolve. A link to a site published in the same change (e.g. the catalog on GitHub Pages) reads as a 404 to a reviewer until it goes live; publish first, or say it is coming.

## FreeCAD geometry

- `wire.makePipeShell(profiles, solid, frenet)` sweeps the profiles along `wire`: the wire it is called on is the spine. Draw each profile at the spine's start, in the plane normal to it, before sweeping.
- To find which side of an edge a face lies on, classify a probe point in the face's (u, v) domain with `face.isPartOfDomain`. `distToShape` next to a curved boundary goes wrong once the GUI has meshed the shape for display.
- Read an edge picked in the 3D view with `getSelectionEx("", 0)` and place it with `Part.getShape(top, "path.")`. The resolved object's `.Shape` leaves out the placement of any container or link around it.
- Any geometry call can raise `Part.OCCError` (`Surface.parameter`, `normalAt`, `isInside`, sweeps). Code that runs from a task panel's OK catches it next to its own errors, so the panel can show its warning instead of stopping mid-way (CodeRabbit, PR #6).

## FreeCAD documents

- FreeCAD calls a proxy's `onChanged` while it restores a document (State includes `Restore`). Do not recompute from `onChanged`: a property change already marks the object for recompute.
- `sheet.set(cell, value)` parses the value, so "1F" becomes 1 farad. Prefix text with `'` to store it as text.
- `FreeCADCmd script.py` runs the script with `__name__` set to the file's stem, not `"__main__"`.
