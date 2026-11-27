import os
import FreeCADGui


class WeldWorkbench(FreeCADGui.Workbench):
    MenuText = "Weld"
    ToolTip = "Add weld beads and track fabrication labor"

    def __init__(self):
        # FreeCAD runs this file without __file__, so find the addon folder through a module in it
        import WeldLocator

        self.__class__.Icon = os.path.join(
            os.path.dirname(WeldLocator.__file__), "Resources", "icons", "Weld.svg"
        )

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
