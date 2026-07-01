"""WeldBead — FeaturePython document object.

Stores weld parameters, computes the bead solid, and updates the
labor time estimate whenever any input changes.
"""

import FreeCAD
import Part
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


class WeldBead:
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSub", "SourceEdge", "Weld",
                        "Edge along which the weld bead is swept")
        obj.addProperty("App::PropertyEnumeration", "WeldType", "Weld",
                        "Joint type").WeldType = WELD_TYPES
        obj.addProperty("App::PropertyFloat", "Size", "Weld",
                        "Weld leg / gap size (mm)").Size = 5.0
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

    def _get_edge(self, obj):
        if not obj.SourceEdge:
            return None
        link, subs = obj.SourceEdge
        if not subs:
            return None
        shape = link.Shape
        return shape.getElement(subs[0])

    def _compute_shape(self, obj, edge):
        if obj.WeldType == "Fillet":
            profile = fillet_profile(obj.Size)
        else:
            profile = butt_profile(obj.Size, obj.Size * 0.5)

        path = Part.Wire([edge])
        try:
            shell = profile.makePipeShell([path], True, False)
            return Part.Solid(shell)
        except Part.OCCError as e:
            FreeCAD.Console.PrintError(f"WeldBead: sweep failed — {e}\n")
            return None

    def execute(self, obj):
        edge = self._get_edge(obj)
        if edge is None:
            return

        solid = self._compute_shape(obj, edge)
        if solid:
            obj.Shape = solid

        length = edge.Length
        obj.LengthMM = length
        rate = _DEPOSITION_RATE.get((obj.Process, obj.Position), 150)
        obj.TimeMinutes = round(length / rate, 3)

    def onChanged(self, obj, prop):
        if prop in ("SourceEdge", "WeldType", "Size", "Process", "Position"):
            obj.recompute()


class WeldBeadViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        import os
        return os.path.join(os.path.dirname(__file__), "Resources", "icons", "Weld.svg")

    def attach(self, vobj):
        self.vobj = vobj

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


def make_weld_bead(name="WeldBead"):
    doc = FreeCAD.ActiveDocument
    obj = doc.addObject("Part::FeaturePython", name)
    WeldBead(obj)
    WeldBeadViewProvider(obj.ViewObject)
    return obj
