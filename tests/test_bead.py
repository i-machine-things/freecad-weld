"""Headless tests for the weld bead's geometry.

Run them with FreeCAD's command-line interpreter, from the repository root:

    FreeCADCmd tests/test_bead.py

Prints a unittest report, and exits with status 1 if any test fails.
"""

import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import FreeCAD  # noqa: E402
import Part  # noqa: E402
import WeldBead  # noqa: E402
import WeldJoint  # noqa: E402

V = FreeCAD.Vector
TOL = 1e-6


def straight_edge(shape, start, end):
    """The name of the straight edge of `shape` between `start` and `end`, in either direction."""
    for i, edge in enumerate(shape.Edges, 1):
        ends = [v.Point for v in edge.Vertexes]
        if len(ends) == 2 and {_key(p) for p in ends} == {_key(start), _key(end)}:
            return f"Edge{i}"
    raise AssertionError(f"no edge from {start} to {end}")


def circle_edge(shape, z):
    for i, edge in enumerate(shape.Edges, 1):
        if isinstance(edge.Curve, Part.Circle) and abs(edge.Curve.Center.z - z) < TOL:
            return f"Edge{i}"
    raise AssertionError(f"no circle at z={z}")


def _key(p):
    return (round(p.x, 6), round(p.y, 6), round(p.z, 6))


class BeadTest(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("WeldTest")
        FreeCAD.setActiveDocument(self.doc.Name)

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def box(self, name, length, width, height, at=(0, 0, 0)):
        obj = self.doc.addObject("Part::Box", name)
        obj.Length, obj.Width, obj.Height = length, width, height
        obj.Placement.Base = V(*at)
        self.doc.recompute()
        return obj

    def bead(self, link, sub, weld_type="Fillet", size=5.0, flip=None):
        bead = WeldBead.make_weld_bead()
        bead.SourceEdge = (link, [sub])
        bead.WeldType = weld_type
        bead.Size = size
        bead.Flip = WeldBead.guess_flip(bead) if flip is None else flip
        self.doc.recompute()
        return bead

    def assertBead(self, bead, volume, box=None, apart_from=()):
        """A valid solid of `volume`, inside `box` (xmin, ymin, zmin, xmax, ymax, zmax) and not
        overlapping any of `apart_from`."""
        shape = bead.Shape
        self.assertFalse(shape.isNull(), "the bead has no shape")
        self.assertEqual(shape.ShapeType, "Solid")
        self.assertTrue(shape.isValid(), "the bead is not a valid solid")
        self.assertAlmostEqual(shape.Volume, volume, places=3)
        if box is not None:
            bb = shape.BoundBox
            got = (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)
            for g, want in zip(got, box):
                # Loose, because OpenCASCADE's bounding box of a curved solid is approximate
                self.assertAlmostEqual(g, want, delta=0.05, msg=f"bounding box {got}, expected {box}")
        for other in apart_from:
            overlap = shape.common(Part.getShape(other)).Volume
            self.assertLess(abs(overlap), 1e-6, f"the bead overlaps {other.Label} by {overlap} mm3")

    def test_outside_corner_of_a_lone_box(self):
        box = self.box("Box", 10, 20, 30)
        sub = straight_edge(box.Shape, V(0, 0, 0), V(0, 0, 30))
        one = self.bead(box, sub, flip=False)
        other = self.bead(box, sub, flip=True)
        self.assertBead(one, 0.5 * 5 * 5 * 30, apart_from=[box])
        self.assertBead(other, 0.5 * 5 * 5 * 30, apart_from=[box])
        boxes = sorted(
            (round(b.Shape.BoundBox.XMin, 6), round(b.Shape.BoundBox.YMin, 6)) for b in (one, other)
        )
        self.assertEqual(boxes, [(-5, 0), (0, -5)], "Flip should move the bead to the other face")

    def test_t_joint(self):
        base = self.box("Base", 100, 100, 10)
        web = self.box("Web", 10, 100, 50, at=(45, 0, 10))
        left = straight_edge(web.Shape, V(45, 0, 10), V(45, 100, 10))
        right = straight_edge(web.Shape, V(55, 0, 10), V(55, 100, 10))
        area = 0.5 * 5 * 5
        self.assertBead(self.bead(web, left), area * 100, (40, 0, 10, 45, 100, 15), [base, web])
        self.assertBead(self.bead(web, right), area * 100, (55, 0, 10, 60, 100, 15), [base, web])

    def test_inside_corner(self):
        upright = Part.makeBox(100, 10, 50)
        foot = Part.makeBox(100, 50, 10)
        angle = self.doc.addObject("Part::Feature", "Angle")
        angle.Shape = upright.fuse(foot).removeSplitter()
        self.doc.recompute()
        sub = straight_edge(angle.Shape, V(0, 10, 10), V(100, 10, 10))
        joint = WeldJoint.joint_at(angle.Shape, angle.Shape.getElement(sub))
        self.assertTrue(joint.concave)
        for flip in (False, True):
            self.assertBead(
                self.bead(angle, sub, flip=flip), 0.5 * 25 * 100, (0, 10, 10, 100, 15, 15), [angle]
            )

    def test_butt_joint(self):
        first = self.box("First", 100, 50, 10)
        second = self.box("Second", 100, 50, 10, at=(100, 0, 0))
        top = straight_edge(first.Shape, V(100, 0, 10), V(100, 50, 10))
        bead = self.bead(first, top, weld_type="Butt")
        self.assertBead(bead, 5 * 2.5 * 50, (97.5, 0, 10, 102.5, 50, 12.5), [first, second])

    def test_round_edge(self):
        plate = self.box("Plate", 100, 100, 10)
        tube = self.doc.addObject("Part::Cylinder", "Tube")
        tube.Radius, tube.Height = 10, 40
        tube.Placement.Base = V(50, 50, 10)
        self.doc.recompute()
        bead = self.bead(tube, circle_edge(tube.Shape, 10))
        ring = 0.5 * 25 * 2 * 3.141592653589793 * (10 + 5 / 3)  # Pappus: area x centroid path
        self.assertBead(bead, ring, (35, 35, 10, 65, 65, 15), [plate, tube])

    def test_edge_inside_a_part_container(self):
        part = self.doc.addObject("App::Part", "Part")
        part.Placement.Base = V(200, 0, 0)
        box = self.doc.addObject("Part::Box", "Box")
        box.Length, box.Width, box.Height = 10, 20, 30
        part.addObject(box)
        self.doc.recompute()
        sub = "Box." + straight_edge(box.Shape, V(0, 0, 0), V(0, 0, 30))
        bead = self.bead(part, sub, flip=False)
        self.assertGreaterEqual(bead.Shape.BoundBox.XMin, 195 - TOL, "the bead ignores the container")
        self.assertBead(bead, 0.5 * 25 * 30)
        box.Height = 60
        self.doc.recompute()
        self.assertBead(bead, 0.5 * 25 * 60)
        self.assertAlmostEqual(bead.LengthMM, 60, places=6)

    def test_edge_of_a_link(self):
        box = self.box("Box", 10, 20, 30)
        box.Visibility = False
        link = self.doc.addObject("App::Link", "Link")
        link.LinkedObject = box
        link.Placement.Base = V(0, 300, 0)
        self.doc.recompute()
        sub = straight_edge(box.Shape, V(0, 0, 0), V(0, 0, 30))
        bead = self.bead(link, sub, flip=False)
        self.assertBead(bead, 0.5 * 25 * 30)
        self.assertGreaterEqual(bead.Shape.BoundBox.YMin, 295 - TOL, "the bead ignores the link")

    def test_labor_values(self):
        base = self.box("Base", 100, 100, 10)
        web = self.box("Web", 10, 100, 50, at=(45, 0, 10))
        bead = self.bead(web, straight_edge(web.Shape, V(45, 0, 10), V(45, 100, 10)))
        self.assertAlmostEqual(bead.LengthMM, 100, places=6)
        self.assertAlmostEqual(bead.TimeMinutes, round(100 / 300, 3), places=6)
        self.assertIsNotNone(base)

    def test_labor_sheet(self):
        import WeldLaborSheet

        self.box("Base", 100, 100, 10)
        web = self.box("Web", 10, 100, 50, at=(45, 0, 10))
        bead = self.bead(web, straight_edge(web.Shape, V(45, 0, 10), V(45, 100, 10)))
        bead.Position = "2F"
        self.doc.recompute()
        WeldLaborSheet.update(self.doc)
        sheet = self.doc.getObject("WeldLabor")
        self.assertEqual(
            [sheet.get(c + "2") for c in "ABCD"], [bead.Label, "Fillet", "MIG", "2F"]
        )
        self.assertAlmostEqual(sheet.get("F2"), 100, places=6)
        self.assertEqual(sheet.get("F3"), "TOTAL")
        self.assertAlmostEqual(sheet.get("G3"), round(100 / 250, 3), places=6)

    def test_save_and_reopen_a_bead_without_flip(self):
        self.box("Base", 100, 100, 10)
        web = self.box("Web", 10, 100, 50, at=(45, 0, 10))
        bead = self.bead(web, straight_edge(web.Shape, V(45, 0, 10), V(45, 100, 10)))
        self.assertFalse(bead.Flip)
        bead.removeProperty("Flip")  # as saved before Flip existed
        name = bead.Name
        path = os.path.join(tempfile.mkdtemp(), "weld.FCStd")
        self.doc.saveAs(path)
        FreeCAD.closeDocument(self.doc.Name)
        self.doc = FreeCAD.openDocument(path)
        bead = self.doc.getObject(name)
        self.assertTrue(hasattr(bead, "Flip"))
        bead.touch()
        self.doc.recompute()
        self.assertBead(bead, 0.5 * 25 * 100, (40, 0, 10, 45, 100, 15))

    def test_edge_without_two_faces(self):
        wire = self.doc.addObject("Part::Feature", "Line")
        wire.Shape = Part.makeLine(V(0, 0, 0), V(10, 0, 0))
        self.doc.recompute()
        bead = self.bead(wire, "Edge1", flip=False)
        self.assertTrue(bead.Shape.isNull())

    def test_missing_edge(self):
        box = self.box("Box", 10, 20, 30)
        bead = self.bead(box, "Edge99", flip=False)
        self.assertTrue(bead.Shape.isNull())


if __name__ in ("__main__", "test_bead"):
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(BeadTest)
    )
    sys.stdout.flush()
    os._exit(0 if result.wasSuccessful() else 1)
