"""
Tests for the error propagation and error handling of different functions in the 
workbook.
"""

from sheets import Workbook, CellError, CellErrorType


def test_iserr_lit():
    """
    Test ISERROR where the first argument is an error literal (should detect the 
    error and behave accordingly).
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=ISERROR(#REF!)")
    wb.set_cell_contents("sheet1", "A2", "=ISERROR(#ref!)")
    wb.set_cell_contents("sheet1", "b2", "=#DIV/0!")
    wb.set_cell_contents("sheet1", "b3", "=ISERROR(B2)")
    assert wb.get_cell_value("sheet1", "A1") is True
    assert wb.get_cell_value("sheet1", "A2") is True
    assert wb.get_cell_value("sheet1", "B3") is True


def test_iferr_lit():
    """
    Test IFERROR where the first argument is an error literal (should detect the 
    error and behave accordingly).
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A2", "=IFERROR(#REF!, 5)")
    wb.set_cell_contents("sheet1", "A4", "=IFERROR(#ref!, 5)")
    assert wb.get_cell_value("sheet1", "A2") == 5
    assert wb.get_cell_value("sheet1", "A4") == 5
    wb.set_cell_contents("sheet1", "A3", "=IFERROR(#DIV/0!)")
    assert wb.get_cell_value("sheet1", "A3") == ""


def test_choose_prop():
    """
    Tests that the CHOOSE function only propagates errors when the chosen argument
    is an error.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=#DIV/0!")
    wb.set_cell_contents("sheet1", "A2", "=CHOOSE(1, A1, 5, 4)")
    wb.set_cell_contents("sheet1", "A3", "=CHOOSE(1, 5, A1, 4)")
    wb.set_cell_contents("sheet1", "A4", "=CHOOSE(1, 5, #REF!, A1)")
    assert isinstance(wb.get_cell_value("sheet1", "A2"), CellError)
    assert wb.get_cell_value("sheet1", "A2").get_type() == CellErrorType.DIVIDE_BY_ZERO
    assert wb.get_cell_value("sheet1", "A3") == 5
    assert wb.get_cell_value("sheet1", "A4") == 5
    wb.set_cell_contents("sheet1", "A1", "=choose(#ref!, 5, 4)")
    assert isinstance(wb.get_cell_value("sheet1", "A1"), CellError)
    assert wb.get_cell_value("sheet1", "A1").get_type() == CellErrorType.BAD_REFERENCE


def test_indirect_prop():
    """
    Tests that the INDIRECT function correctly propagates errors.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=INDIRECT(#DIV/0!)")
    assert isinstance(wb.get_cell_value("sheet1", "A1"), CellError)
    assert wb.get_cell_value("sheet1", "A1").get_type() == CellErrorType.DIVIDE_BY_ZERO

    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=INDIRECT(#REF!)")
    assert isinstance(wb.get_cell_value("sheet1", "A1"), CellError)
    assert wb.get_cell_value("sheet1", "A1").get_type() == CellErrorType.BAD_REFERENCE

    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=INDIRECT(#ERROR!)")
    assert isinstance(wb.get_cell_value("sheet1", "A1"), CellError)
    assert wb.get_cell_value("sheet1", "A1").get_type() == CellErrorType.PARSE_ERROR

    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=INDIRECT(#CIRCREF!)")
    assert isinstance(wb.get_cell_value("sheet1", "A1"), CellError)
    assert wb.get_cell_value("sheet1", "A1").get_type() == CellErrorType.CIRCULAR_REFERENCE

    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=INDIRECT(#NAME?)")
    assert isinstance(wb.get_cell_value("sheet1", "A1"), CellError)
    assert wb.get_cell_value("sheet1", "A1").get_type() == CellErrorType.BAD_NAME

    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=INDIRECT(#VALUE!)")
    assert isinstance(wb.get_cell_value("sheet1", "A1"), CellError)
    assert wb.get_cell_value("sheet1", "A1").get_type() == CellErrorType.TYPE_ERROR



def test_and_err_prop():
    """
    Tests that the AND function correctly propagates errors.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=#DIV/0!")
    wb.set_cell_contents("sheet1", "A2", "=AND(A1, 5, 4)")
    wb.set_cell_contents("sheet1", "A3", "=AND(5, A1, 4)")
    wb.set_cell_contents("sheet1", "A4", "=AND(5, #REF!, A1)")
    assert isinstance(wb.get_cell_value("sheet1", "A2"), CellError)
    assert wb.get_cell_value("sheet1", "A2").get_type() == CellErrorType.DIVIDE_BY_ZERO
    assert wb.get_cell_value("sheet1", "A3").get_type() == CellErrorType.DIVIDE_BY_ZERO
    assert (wb.get_cell_value("sheet1", "A4").get_type() == CellErrorType.BAD_REFERENCE
            or wb.get_cell_value("sheet1", "A4").get_type() == CellErrorType.DIVIDE_BY_ZERO)


def test_or_err_prop():
    """
    Tests that the OR function correctly propagates errors.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=#DIV/0!")
    wb.set_cell_contents("sheet1", "A2", "=OR(A1, 5, 4)")
    wb.set_cell_contents("sheet1", "A3", "=OR(5, A1, 4)")
    wb.set_cell_contents("sheet1", "A4", "=OR(5, #REF!, A1)")
    assert isinstance(wb.get_cell_value("sheet1", "A2"), CellError)
    assert wb.get_cell_value("sheet1", "A2").get_type() == CellErrorType.DIVIDE_BY_ZERO
    assert wb.get_cell_value("sheet1", "A3").get_type() == CellErrorType.DIVIDE_BY_ZERO
    assert (wb.get_cell_value("sheet1", "A4").get_type() == CellErrorType.BAD_REFERENCE
            or wb.get_cell_value("sheet1", "A4").get_type() == CellErrorType.DIVIDE_BY_ZERO)


def test_xor_err_prop():
    """
    Tests that the XOR function correctly propagates errors.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=#DIV/0!")
    wb.set_cell_contents("sheet1", "A2", "=XOR(A1, 5, 4)")
    wb.set_cell_contents("sheet1", "A3", "=XOR(5, A1, 4)")
    wb.set_cell_contents("sheet1", "A4", "=XOR(5, #REF!, A1)")
    assert isinstance(wb.get_cell_value("sheet1", "A2"), CellError)
    assert wb.get_cell_value("sheet1", "A2").get_type() == CellErrorType.DIVIDE_BY_ZERO
    assert wb.get_cell_value("sheet1", "A3").get_type() == CellErrorType.DIVIDE_BY_ZERO
    assert (wb.get_cell_value("sheet1", "A4").get_type() == CellErrorType.BAD_REFERENCE
            or wb.get_cell_value("sheet1", "A4").get_type() == CellErrorType.DIVIDE_BY_ZERO)


def test_not_err_prop():
    """
    Tests that the NOT function correctly propagates errors.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=#DIV/0!")
    wb.set_cell_contents("sheet1", "A2", "=NOT(A1)")
    wb.set_cell_contents("sheet1", "A3", "=NOT(5)")
    assert wb.get_cell_value("sheet1", "A2").get_type() == CellErrorType.DIVIDE_BY_ZERO
    assert wb.get_cell_value("sheet1", "A3") is False


def test_exact_err_prop():
    """
    Tests that the EXACT function correctly propagates errors.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A1", "=#DIV/0!")
    wb.set_cell_contents("sheet1", "A2", "=EXACT(A1, 5)")
    wb.set_cell_contents("sheet1", "A3", "=EXACT(5, A1)")
    wb.set_cell_contents("sheet1", "A4", "=EXACT(5, #REF!)")
    assert wb.get_cell_value("sheet1", "A2").get_type() == CellErrorType.DIVIDE_BY_ZERO
    assert wb.get_cell_value("sheet1", "A3").get_type() == CellErrorType.DIVIDE_BY_ZERO
    assert (wb.get_cell_value("sheet1", "A4").get_type() == CellErrorType.BAD_REFERENCE
            or wb.get_cell_value("sheet1", "A4").get_type() == CellErrorType.DIVIDE_BY_ZERO)
