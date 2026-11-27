"""WeldBead — FeaturePython document object.

Stores weld parameters, computes the bead solid, and updates the
labor time estimate whenever any input changes.
"""

import FreeCAD
import Part
import WeldJoint
from profiles import fillet_profile, butt_profile

# Deposition rates: mm of weld per minute, keyed by (process, position).
# Values are approximate mid-range figures; override via preference in future.
_DEPOSITION_RATE = {
    ("MIG", "1F"): 300, ("MIG", "2F"): 250, ("MIG", "3F"): 200, ("MIG", "4F"): 180,
    ("TIG", "1F"): 150, ("TIG", "2F"): 120, ("TIG", "3F"): 100, ("TIG", "4F"):  90,
    ("SMAW","1F"): 120, ("SMAW","2F"):  90, ("SMAW","3F"):  70, ("SMAW","4F"):  60,
}

WELD_TYPES = ["Fillet", "Butt"]
PROCESSES   = ["MIG", "TIG", "SMAW"]
POSITIONS   = ["1F", "2F", "3F", "4F"]


class SourceError(Exception):
    """The bead's SourceEdge does not name an edge that exists."""


def source_shape(link, sub):
    """The edge `sub` of `link`, and the whole shape it is an edge of.

    `sub` can be a path through containers and links, such as "Part.Body.Edge3", as the 3D view
    selects it. Both shapes come back placed where they are in the document, so a bead lines up
    with an edge inside an assembly, a part container or a link.
    """
    path, _, element = sub.rpartition(".")
    shape = Part.getShape(link, path + "." if path else "")
    if shape.isNull():
        raise SourceError(f"{link.Label} has no shape at {path or link.Name}")
    try:
        edge = shape.getElement(element)
    except (ValueError, IndexError, Part.OCCError) as e:
        raise SourceError(f"{link.Label} has no {element}: {e}") from e
    if edge.ShapeType != "Edge":
        raise SourceError(f"{element} of {link.Label} is not an edge")
    return shape, edge


def source_of(obj):
    """(shape, edge) for the bead's SourceEdge, or None when no edge is set."""
    if not obj.SourceEdge:
        return None
    link, subs = obj.SourceEdge
    if not subs:
        return None
    return source_shape(link, subs[0])


def is_weld_bead(obj) -> bool:
    return getattr(obj, "Proxy", None).__class__.__name__ == "WeldBead"


def _other_solids(doc, bead):
    """The visible solids in the document, other than weld beads, placed where they are."""
    solids = []
    for obj in doc.Objects:
        if obj is bead or is_weld_bead(obj) or obj.isDerivedFrom("App::DocumentObjectGroup"):
            continue
        if obj.getParentGeoFeatureGroup() is not None:
            continue  # inside a part container or body, whose shape includes it
        if not getattr(obj, "Visibility", True):
            continue
        solids.extend(Part.getShape(obj).Solids)
    return solids


def guess_flip(obj) -> bool:
    """The Flip for a new bead on obj.SourceEdge: face B is the face touching another part."""
    try:
        source = source_of(obj)
        if source is None:
            return False
        shape, edge = source
        return WeldJoint.guess_flip(shape, edge, _other_solids(obj.Document, obj))
    except (SourceError, WeldJoint.JointError, Part.OCCError):
        return False  # execute() reports what is wrong with the edge


def bead_profile(weld_type, size, joint):
    """The bead's cross-section, drawn at the joint root."""
    if weld_type == "Fillet":
        # Inside a corner, the second leg runs along face B. On an outside corner it runs along
        # the extension of face B beyond the edge.
        leg_b = joint.along_b if joint.concave else joint.along_b * -1
        return fillet_profile(size, joint.root, joint.along_a, leg_b)
    return butt_profile(size, size * 0.5, joint.root, joint.along_a, joint.normal_a)


def sweep(profile, edge):
    """Sweep the closed `profile` along `edge` into a solid."""
    solid = Part.Wire([edge]).makePipeShell([profile], True, False)
    if solid.ShapeType != "Solid":
        solid = Part.Solid(solid)
    if solid.Volume < 0:
        solid.reverse()
    return solid


class WeldBead:
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSub", "SourceEdge", "Weld",
                        "Edge along which the weld bead is swept")
        obj.addProperty("App::PropertyEnumeration", "WeldType", "Weld",
                        "Joint type").WeldType = WELD_TYPES
        obj.addProperty("App::PropertyFloat", "Size", "Weld",
                        "Weld leg / gap size (mm)").Size = 5.0
        self._add_flip(obj)
        obj.addProperty("App::PropertyEnumeration", "Process", "Labor",
                        "Welding process").Process = PROCESSES
        obj.addProperty("App::PropertyEnumeration", "Position", "Labor",
                        "Weld position").Position = POSITIONS
        obj.addProperty("App::PropertyFloat", "LengthMM", "Labor",
                        "Bead length (mm), auto-computed").LengthMM = 0.0
        obj.addProperty("App::PropertyFloat", "TimeMinutes", "Labor",
                        "Estimated weld time (min), auto-computed").TimeMinutes = 0.0
        obj.setEditorMode("LengthMM", 1)
        obj.setEditorMode("TimeMinutes", 1)
        obj.Proxy = self

    @staticmethod
    def _add_flip(obj):
        obj.addProperty("App::PropertyBool", "Flip", "Weld",
                        "Put the bead against the edge's other face")

    def onDocumentRestored(self, obj):
        if not hasattr(obj, "Flip"):  # a bead saved before Flip existed
            self._add_flip(obj)

    def execute(self, obj):
        try:
            source = source_of(obj)
        except SourceError as e:
            obj.Shape = Part.Shape()
            FreeCAD.Console.PrintError(f"{obj.Label}: {e}\n")
            return
        if source is None:
            return
        shape, edge = source

        length = edge.Length
        obj.LengthMM = length
        rate = _DEPOSITION_RATE.get((obj.Process, obj.Position), 150)
        obj.TimeMinutes = round(length / rate, 3)

        try:
            joint = WeldJoint.joint_at(shape, edge, obj.Flip)
            obj.Shape = sweep(bead_profile(obj.WeldType, obj.Size, joint), edge)
        except (WeldJoint.JointError, Part.OCCError) as e:
            obj.Shape = Part.Shape()
            FreeCAD.Console.PrintError(f"{obj.Label}: could not make the bead: {e}\n")

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def __getstate__(self):  # used by FreeCAD versions without dumps/loads
        return None

    def __setstate__(self, state):
        return None


class WeldBeadViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        import os
        return os.path.join(os.path.dirname(__file__), "Resources", "icons", "Weld.svg")

    def attach(self, vobj):
        self.vobj = vobj

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


def make_weld_bead(name="WeldBead"):
    doc = FreeCAD.ActiveDocument
    obj = doc.addObject("Part::FeaturePython", name)
    WeldBead(obj)
    if FreeCAD.GuiUp:
        WeldBeadViewProvider(obj.ViewObject)
    return obj
