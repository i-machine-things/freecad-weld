"""FreeCAD GUI commands for the Weld workbench."""

import FreeCAD
import FreeCADGui
from PySide2 import QtCore, QtWidgets


class _AddBeadTask:
    """Task panel shown when the user triggers Weld_AddBead."""

    def __init__(self, bead_obj):
        self.bead = bead_obj
        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("Add Weld Bead")
        layout = QtWidgets.QFormLayout(self.form)

        self._type = QtWidgets.QComboBox()
        self._type.addItems(["Fillet", "Butt"])
        layout.addRow("Weld type", self._type)

        self._size = QtWidgets.QDoubleSpinBox()
        self._size.setRange(0.5, 50.0)
        self._size.setSingleStep(0.5)
        self._size.setSuffix(" mm")
        self._size.setValue(5.0)
        layout.addRow("Size", self._size)

        self._process = QtWidgets.QComboBox()
        self._process.addItems(["MIG", "TIG", "SMAW"])
        layout.addRow("Process", self._process)

        self._position = QtWidgets.QComboBox()
        self._position.addItems(["1F", "2F", "3F", "4F"])
        layout.addRow("Position", self._position)

        self._hint = QtWidgets.QLabel(
            "Select an edge in the 3D view, then click OK."
        )
        self._hint.setWordWrap(True)
        layout.addRow(self._hint)

    def accept(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        edge_ref = None
        for s in sel:
            for sub in s.SubElementNames:
                if sub.startswith("Edge"):
                    edge_ref = (s.Object, [sub])
                    break
            if edge_ref:
                break

        if edge_ref is None:
            QtWidgets.QMessageBox.warning(
                None, "Weld", "Please select an edge before clicking OK."
            )
            return False

        doc = FreeCAD.ActiveDocument
        self.bead.SourceEdge = edge_ref
        self.bead.WeldType = self._type.currentText()
        self.bead.Size = self._size.value()
        self.bead.Process = self._process.currentText()
        self.bead.Position = self._position.currentText()

        # Move bead into Welds group, creating it if needed
        group = doc.getObject("Welds")
        if group is None:
            group = doc.addObject("App::DocumentObjectGroup", "Welds")
        group.addObject(self.bead)

        doc.recompute()
        import WeldLaborSheet
        WeldLaborSheet.update(doc)
        FreeCADGui.Control.closeDialog()
        return True

    def reject(self):
        FreeCAD.ActiveDocument.removeObject(self.bead.Name)
        FreeCADGui.Control.closeDialog()


class CmdAddBead:
    def GetResources(self):
        import os
        return {
            "Pixmap": os.path.join(
                os.path.dirname(__file__), "Resources", "icons", "Weld.svg"
            ),
            "MenuText": "Add Weld Bead",
            "ToolTip": "Select an edge and add a weld bead solid",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        import WeldBead as WB
        bead = WB.make_weld_bead()
        FreeCADGui.Control.showDialog(_AddBeadTask(bead))


class CmdLaborSheet:
    def GetResources(self):
        return {
            "MenuText": "Update Labor Sheet",
            "ToolTip": "Refresh the WeldLabor spreadsheet with current weld data",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        import WeldLaborSheet
        WeldLaborSheet.update()


FreeCADGui.addCommand("Weld_AddBead", CmdAddBead())
FreeCADGui.addCommand("Weld_LaborSheet", CmdLaborSheet())
