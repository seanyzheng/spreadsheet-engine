"""
Tests for all different kinds of cycle detection in the graph.
"""

import sheets

def test_single_ref():
    """
    Tests the case of a single cell referencing itself with different casing and 
    sheet reference formats.
    """
    wb = sheets.Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "=$A$1")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    wb.set_cell_contents("Sheet1", "a1", "=$a$1")
    assert isinstance(wb.get_cell_value("Sheet1", "a1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "a1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    wb.set_cell_contents("sheet1", "A1", "=sHeEt1!$a$1")
    assert isinstance(wb.get_cell_value("sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "A1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    wb.set_cell_contents("Sheet1", "A1", "='Sheet1'!$a$1")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)

def test_simple_loop():
    """
    Tests the case of a simple loop of cells referencing each other.
    """
    wb = sheets.Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "=$a$2")
    wb.set_cell_contents("Sheet1", "A2", "=$a$1")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("SheeT1", "a2"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A2").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    wb.set_cell_contents("Sheet1", "A1", "=sheet1!$A$3")
    wb.set_cell_contents("Sheet1", "A2", "='sHeEt1'!$A$1")
    wb.set_cell_contents("Sheet1", "A3", "=$a$2")
    assert isinstance(wb.get_cell_value("ShEet1", "a1"), sheets.CellError)
    assert (wb.get_cell_value("ShEEt1", "a1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A2").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "A3"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A3").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)


def test_multi_loop():
    """
    Tests the case where there are multiple loops in the same sheet, and some
    non-cycle cells.
    """
    wb = sheets.Workbook()
    wb.new_sheet("Sheet1")
    # Loop 1
    wb.set_cell_contents("Sheet1", "A1", "=$a$2")
    wb.set_cell_contents("Sheet1", "a2", "=$A$3")
    wb.set_cell_contents("Sheet1", "A3", "=$a$1")

    # Loop 2
    wb.set_cell_contents("Sheet1", "A4", "=sheet1!$a$5")
    wb.set_cell_contents("Sheet1", "a5", "='sheet1'!$a$6")
    wb.set_cell_contents("Sheet1", "a6", "=ShEeT1!$a$7")
    wb.set_cell_contents("Sheet1", "A7", "=$a$4")

    # Non-cycle cells
    wb.set_cell_contents("Sheet1", "A8", "=$a$9")
    wb.set_cell_contents("Sheet1", "A9", "=$a$10")
    wb.set_cell_contents("Sheet1", "A10", "=10")

    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A2").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "A3"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A3").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "A4"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A4").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "A5"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A5").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "A6"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A6").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "A7"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A7").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert wb.get_cell_value("Sheet1", "A8") == 10
    assert wb.get_cell_value("Sheet1", "A9") == 10
    assert wb.get_cell_value("Sheet1", "A10") == 10


def test_multi_sheet_loop():
    """
    Ensures that a loop spanning multiple sheets is caught.
    """
    wb = sheets.Workbook()
    wb.new_sheet("Sheet1")
    wb.new_sheet("Sheet2")
    wb.set_cell_contents("Sheet1", "A1", "=Sheet2!$a$1")
    wb.set_cell_contents("Sheet2", "A1", "=Sheet1!$a$1")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet2", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet2", "A1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)


def test_point_to_cycle():
    """
    Tests the case where a cell is not within the cycle but points to a cell
    which does participate in the cycle.
    """
    wb = sheets.Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "=a2")
    wb.set_cell_contents("Sheet1", "A2", "='sheet1'!A3")
    wb.set_cell_contents("Sheet1", "A3", "=a4")
    wb.set_cell_contents("Sheet1", "A4", "=A5")
    wb.set_cell_contents("Sheet1", "A5", "=SheEt1!a1")
    wb.set_cell_contents("Sheet1", "A6", "=shEEt1!a1")
    assert isinstance(wb.get_cell_value("Sheet1", "A6"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A6").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    wb.set_cell_contents("Sheet1", "A6", "=a2")
    assert isinstance(wb.get_cell_value("Sheet1", "A6"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A6").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    wb.set_cell_contents("Sheet1", "A6", "=a3")
    assert isinstance(wb.get_cell_value("Sheet1", "A6"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A6").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    wb.set_cell_contents("Sheet1", "A6", "=$a$4")
    assert isinstance(wb.get_cell_value("Sheet1", "A6"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A6").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    wb.set_cell_contents("Sheet1", "A6", "=a5")
    assert isinstance(wb.get_cell_value("Sheet1", "A6"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A6").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    wb.set_cell_contents("Sheet1", "A6", "=a6")
    assert isinstance(wb.get_cell_value("Sheet1", "A6"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A6").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)


def test_copy_cycle_edge_case():
    """
    A copied spreadsheet might have a bad name error that references a future
    copy. When this copy is made it could cause a circular reference error.
    """
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=Sheet1_1!A1")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.BAD_REFERENCE)
    wb.copy_sheet("Sheet1")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1_1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1_1", "A1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)
