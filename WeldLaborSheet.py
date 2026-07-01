"""WeldLaborSheet — creates and updates a FreeCAD Spreadsheet with weld labor data.

Finds all WeldBead objects in the active document and writes one row per bead.
Call `update(doc)` after any weld change to keep totals current.
"""

import FreeCAD

_SHEET_NAME = "WeldLabor"

_HEADERS = ["ID", "Type", "Process", "Position", "Size (mm)", "Length (mm)", "Time (min)"]


def _get_or_create_sheet(doc):
    sheet = doc.getObject(_SHEET_NAME)
    if sheet is None:
        sheet = doc.addObject("Spreadsheet::Sheet", _SHEET_NAME)
    return sheet


def _write_headers(sheet):
    for col, header in enumerate(_HEADERS):
        cell = _col_label(col) + "1"
        sheet.set(cell, header)
        sheet.setStyle(cell, "bold")


def _col_label(index: int) -> str:
    label = ""
    while True:
        label = chr(ord("A") + index % 26) + label
        index = index // 26 - 1
        if index < 0:
            break
    return label


def _find_weld_beads(doc):
    return [obj for obj in doc.Objects if hasattr(obj, "Proxy")
            and obj.Proxy.__class__.__name__ == "WeldBead"]


def update(doc=None):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    if doc is None:
        FreeCAD.Console.PrintError("WeldLaborSheet: no active document\n")
        return

    sheet = _get_or_create_sheet(doc)
    sheet.clearAll()
    _write_headers(sheet)

    beads = _find_weld_beads(doc)
    total_time = 0.0

    for row_idx, bead in enumerate(beads, start=2):
        row = str(row_idx)
        sheet.set("A" + row, bead.Label)
        sheet.set("B" + row, bead.WeldType)
        sheet.set("C" + row, bead.Process)
        sheet.set("D" + row, bead.Position)
        sheet.set("E" + row, str(round(bead.Size, 3)))
        sheet.set("F" + row, str(round(bead.LengthMM, 3)))
        sheet.set("G" + row, str(round(bead.TimeMinutes, 3)))
        total_time += bead.TimeMinutes

    total_row = str(len(beads) + 2)
    sheet.set("F" + total_row, "TOTAL")
    sheet.set("G" + total_row, str(round(total_time, 3)))
    sheet.setStyle("F" + total_row, "bold")
    sheet.setStyle("G" + total_row, "bold")

    doc.recompute()
    FreeCAD.Console.PrintMessage(
        f"WeldLaborSheet: {len(beads)} welds, {round(total_time, 2)} min total\n"
    )
