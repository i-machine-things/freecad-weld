import os
import FreeCADGui


class WeldWorkbench(FreeCADGui.Workbench):
    MenuText = "Weld"
    ToolTip = "Add weld beads and track fabrication labor"
    Icon = os.path.join(os.path.dirname(__file__), "Resources", "icons", "Weld.svg")

    def Initialize(self):
        import WeldCommands
        tools = ["Weld_AddBead", "Weld_LaborSheet"]
        self.appendToolbar("Weld", tools)
        self.appendMenu("Weld", tools)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(WeldWorkbench())
