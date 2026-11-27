"""Weld cross-section profile generators.

Each function returns a closed Part.Wire. By default it lies in the XY plane with the joint root
at the origin. Pass `origin`, `u` and `v` to draw it somewhere else: the profile point (x, y)
goes to origin + x * u + y * v. WeldJoint works out those vectors for a bead on an edge.
"""

import Part
import FreeCAD


def _polygon(points, origin, u, v):
    origin = origin if origin is not None else FreeCAD.Vector(0, 0, 0)
    u = u if u is not None else FreeCAD.Vector(1, 0, 0)
    v = v if v is not None else FreeCAD.Vector(0, 1, 0)
    corners = [origin + u * x + v * y for x, y in points]
    return Part.makePolygon(corners + corners[:1])


def fillet_profile(size: float, origin=None, u=None, v=None) -> Part.Wire:
    """Triangle for a fillet weld: legs of `size` mm along `u` and `v` from the root.

    With unit `u` and `v` at right angles this is a right isosceles triangle, and its
    hypotenuse faces outward (away from the joint root).
    """
    return _polygon([(0, 0), (size, 0), (0, size)], origin, u, v)


def butt_profile(gap: float, height: float, origin=None, u=None, v=None) -> Part.Wire:
    """Simple rectangular fill for a square butt weld.

    `gap`    — joint gap width in mm, across `u`, centred on the root
    `height` — weld reinforcement height in mm, along `v`
    """
    return _polygon(
        [(-gap / 2, 0), (gap / 2, 0), (gap / 2, height), (-gap / 2, height)], origin, u, v
    )
