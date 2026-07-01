"""Weld cross-section profile generators.

Each function returns a Part.Wire in the XY plane, centered at the origin,
ready to be positioned and swept along an edge.
"""

import math
import Part
import FreeCAD


def fillet_profile(size: float) -> Part.Wire:
    """Right isosceles triangle for a fillet weld.

    Hypotenuse faces outward (away from the joint root).
    `size` is the weld leg length in mm.
    """
    p0 = FreeCAD.Vector(0, 0, 0)
    p1 = FreeCAD.Vector(size, 0, 0)
    p2 = FreeCAD.Vector(0, size, 0)
    edges = [
        Part.makeLine(p0, p1),
        Part.makeLine(p1, p2),
        Part.makeLine(p2, p0),
    ]
    return Part.Wire(edges)


def butt_profile(gap: float, height: float) -> Part.Wire:
    """Simple rectangular fill for a square butt weld.

    `gap`    — joint gap width in mm
    `height` — weld reinforcement height in mm
    """
    p0 = FreeCAD.Vector(-gap / 2, 0, 0)
    p1 = FreeCAD.Vector(gap / 2, 0, 0)
    p2 = FreeCAD.Vector(gap / 2, height, 0)
    p3 = FreeCAD.Vector(-gap / 2, height, 0)
    edges = [
        Part.makeLine(p0, p1),
        Part.makeLine(p1, p2),
        Part.makeLine(p2, p3),
        Part.makeLine(p3, p0),
    ]
    return Part.Wire(edges)
