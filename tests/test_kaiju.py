from sheets import Workbook, CellError, CellErrorType, version


# Edge cases
def test_demo():
    """
    Ensures that a function that does not exist returns an error.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "a1", "=A2+5")
    wb.set_cell_contents("sheet1", "a2", "=5")
    assert wb.get_cell_value("sheet1", "a1") == 10

    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "a1", "=A2+5")
    wb.set_cell_contents("sheet1", "a2", "=a1+5")
    assert isinstance(wb.get_cell_value("sheet1", "a1"), CellError)
    assert wb.get_cell_value("sheet1", "a1").get_type() == CellErrorType.CIRCULAR_REFERENCE

    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "a1", "=IFERROR(B1,A2)")
    wb.set_cell_contents("sheet1", "b1", "=A1+")
    wb.set_cell_contents("sheet1", "a2", "=5")
    assert wb.get_cell_value("sheet1", "a1") == 5