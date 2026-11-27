"""Where a weld bead sits on its edge.

A bead runs along an edge where two faces meet: face A and face B. At the start of the edge,
`joint_at` finds the joint root and the direction of each face away from the edge, so a profile
can be drawn there and swept along the edge.

- A concave edge (an inside corner) has a fillet in the corner, with a leg along each face.
- A convex edge (an outside corner, such as the bottom edge of a plate standing on another part)
  has a fillet against face A, sitting on the extension of face B beyond the edge. A butt bead
  sits on face A, centred on the edge. `Flip` swaps faces A and B.

`guess_flip` picks the faces for a new bead: face B is the one touching another part.
"""

import FreeCAD
import Part

# How far from the edge to probe the faces, in mm: small next to any weld, large next to
# OpenCASCADE's tolerances.
_PROBE = 0.01


class JointError(Exception):
    """The edge cannot carry a weld bead."""


class Joint:
    """The joint at the start of an edge: its root, and for each face, the direction from the edge
    into the face (`along_a`, `along_b`) and the face's outward normal (`normal_a`, `normal_b`)."""

    def __init__(self, root, along_a, along_b, normal_a, normal_b):
        self.root = root
        self.along_a = along_a
        self.along_b = along_b
        self.normal_a = normal_a
        self.normal_b = normal_b

    @property
    def concave(self) -> bool:
        """True for an inside corner: face B rises out of face A instead of falling away from it."""
        return self.along_b.dot(self.normal_a) > 0


def adjacent_faces(shape, edge):
    """The faces of `shape` that meet at `edge`, without repeats."""
    faces = []
    for face in shape.ancestorsOfType(edge, Part.Face):
        if not any(face.isSame(f) for f in faces):
            faces.append(face)
    return faces


def _normal(face, point):
    u, v = face.Surface.parameter(point)
    normal = face.normalAt(u, v)
    normal.normalize()
    return normal


def _into_face_sign(face, edge) -> float:
    """+1 if tangent x normal points from the edge into the face, -1 if it points out of it.

    Probed in the middle of the edge, where the face is sure to lie on one side only (at an end,
    a probe can fall on the face's next edge or off a pointed corner). The sign is the same all
    along the edge. The probe is classified in the face's own (u, v) domain, from its exact
    boundary: a 3D distance check can be thrown off by the mesh FreeCAD makes to display a face.
    """
    param = (edge.FirstParameter + edge.LastParameter) / 2
    point = edge.valueAt(param)
    direction = edge.tangentAt(param).cross(_normal(face, point))
    if direction.Length < 1e-9:
        raise JointError("the edge runs along the normal of one of its faces")
    direction.normalize()
    for sign in (1.0, -1.0):
        u, v = face.Surface.parameter(point + direction * (sign * _PROBE))
        if face.isPartOfDomain(u, v):
            return sign
    raise JointError("could not tell which side of the edge a face is on")


def joint_at(shape, edge, flip=False) -> Joint:
    """The joint at the start of `edge`, an edge of `shape`."""
    faces = adjacent_faces(shape, edge)
    if len(faces) != 2:
        raise JointError(
            f"a weld bead needs an edge where two faces meet, and this edge has {len(faces)}"
        )
    face_a, face_b = reversed(faces) if flip else faces
    root = edge.valueAt(edge.FirstParameter)
    tangent = edge.tangentAt(edge.FirstParameter)
    normal_a = _normal(face_a, root)
    normal_b = _normal(face_b, root)
    along_a = tangent.cross(normal_a) * _into_face_sign(face_a, edge)
    along_b = tangent.cross(normal_b) * _into_face_sign(face_b, edge)
    along_a.normalize()
    along_b.normalize()
    if abs(along_b.dot(normal_a)) < 1e-6 and along_a.dot(along_b) < 0:
        raise JointError("the two faces meet smoothly at this edge, so there is no corner to weld")
    return Joint(root, along_a, along_b, normal_a, normal_b)


def _touches_another_part(face, edge, others) -> bool:
    """Whether a point just outside `face`, beside the middle of `edge`, is inside one of `others`."""
    param = (edge.FirstParameter + edge.LastParameter) / 2
    point = edge.valueAt(param)
    normal = _normal(face, point)
    into_face = edge.tangentAt(param).cross(normal) * _into_face_sign(face, edge)
    into_face.normalize()
    probe = point + normal * _PROBE + into_face * _PROBE
    return any(solid.isInside(probe, _PROBE / 10, True) for solid in others)


def guess_flip(shape, edge, others) -> bool:
    """The Flip that makes face B the face touching one of `others` (solids around the joint).

    In a T joint, the plate standing on the other part touches it with face B, so the fillet goes
    against face A, on the other part. In a butt joint, the end face touches the other plate, so
    the bead goes on top. False if neither face, or both, touch another part.
    """
    faces = adjacent_faces(shape, edge)
    if len(faces) != 2:
        return False
    touch_a, touch_b = (_touches_another_part(f, edge, others) for f in faces)
    return touch_a and not touch_b
