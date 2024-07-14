"""
This module contains tests for the sorting funcitonality incorporated in project
5.
"""

from decimal import Decimal
from sheets.workbook import Workbook, CellError, CellErrorType

def test_sort_region_basic():
    """
    Tests basic sorting functionality with numeric values.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    # Populate cells in reverse order
    wb.set_cell_contents("Sheet1", "A1", "3")
    wb.set_cell_contents("Sheet1", "A2", "1")
    wb.set_cell_contents("Sheet1", "A3", "2")

    # Sort the region A1:A3 in ascending order based on the first column
    wb.sort_region("Sheet1", "A1", "A3", [1])

    assert wb.get_cell_value("Sheet1", "A1") == Decimal(1)
    assert wb.get_cell_value("Sheet1", "A2") == Decimal(2)
    assert wb.get_cell_value("Sheet1", "A3") == Decimal(3)

def test_sort_region_strings():
    """
    Tests sorting functionality with string values.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    # Populate cells with strings
    wb.set_cell_contents("Sheet1", "A1", "Charlie")
    wb.set_cell_contents("Sheet1", "A2", "Alice")
    wb.set_cell_contents("Sheet1", "A3", "Bob")

    # Sort the region A1:A3 in ascending order
    wb.sort_region("Sheet1", "A1", "A3", [1])

    assert wb.get_cell_value("Sheet1", "A1") == "Alice"
    assert wb.get_cell_value("Sheet1", "A2") == "Bob"
    assert wb.get_cell_value("Sheet1", "A3") == "Charlie"

def test_sort_region_descending():
    """
    Tests sorting functionality in descending order.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    # Populate cells
    wb.set_cell_contents("Sheet1", "A1", "1")
    wb.set_cell_contents("Sheet1", "A2", "3")
    wb.set_cell_contents("Sheet1", "A3", "2")

    # Sort the region A1:A3 in descending order
    wb.sort_region("Sheet1", "A1", "A3", [-1])

    assert wb.get_cell_value("Sheet1", "A1") == Decimal(3)
    assert wb.get_cell_value("Sheet1", "A2") == Decimal(2)
    assert wb.get_cell_value("Sheet1", "A3") == Decimal(1)

def test_sort_region_multiple_columns():
    """
    Tests sorting functionality based on multiple columns.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    # Populate cells in a way that sorting by the first column alone would be
    # insufficient
    wb.set_cell_contents("Sheet1", "A1", "Alice")
    wb.set_cell_contents("Sheet1", "B1", "2")
    wb.set_cell_contents("Sheet1", "A2", "Alice")
    wb.set_cell_contents("Sheet1", "B2", "1")
    wb.set_cell_contents("Sheet1", "A3", "Bob")
    wb.set_cell_contents("Sheet1", "B3", "3")

    # Sort the region A1:B3 based on the first column in ascending order, and
    # then the second column in ascending order
    wb.sort_region("Sheet1", "A1", "B3", [1, 2])

    # The expected order is Alice-1, Alice-2, Bob-3
    assert (wb.get_cell_value("Sheet1", "A1") == "Alice" and
            wb.get_cell_value("Sheet1", "B1") == Decimal(1))
    assert (wb.get_cell_value("Sheet1", "A2") == "Alice" and
            wb.get_cell_value("Sheet1", "B2") == Decimal(2))
    assert (wb.get_cell_value("Sheet1", "A3") == "Bob" and
            wb.get_cell_value("Sheet1", "B3") == Decimal(3))

def test_sort_region_with_formulas():
    """
    Tests sorting functionality when the region contains formulas.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    # Populate cells with formulas that reference other cells
    wb.set_cell_contents("Sheet1", "A1", "=B3")
    wb.set_cell_contents("Sheet1", "A2", "=B1")
    wb.set_cell_contents("Sheet1", "A3", "=B2")
    wb.set_cell_contents("Sheet1", "B1", "3")
    wb.set_cell_contents("Sheet1", "B2", "1")
    wb.set_cell_contents("Sheet1", "B3", "2")

    # Sort the region A1:A3 in ascending order based on the formula results
    wb.sort_region("Sheet1", "A1", "A3", [1])

    assert wb.get_cell_value("Sheet1", "A1") == Decimal(1)
    assert wb.get_cell_value("Sheet1", "A2") == Decimal(2)
    assert wb.get_cell_value("Sheet1", "A3") == Decimal(3)



def test_sort_region_with_nested_formulas():
    """
    Tests sorting functionality when the region contains nested formulas,
    and the sorting order is determined by the result of these formulas.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    # Populate cells with nested formulas that reference other cells
    wb.set_cell_contents("Sheet1", "A1", "=B3 * C1")
    wb.set_cell_contents("Sheet1", "A2", "=B1 + C2")
    wb.set_cell_contents("Sheet1", "A3", "=B2 - C3")
    # Values for the formulas to reference
    wb.set_cell_contents("Sheet1", "B1", "5")  # Used in A2
    wb.set_cell_contents("Sheet1", "B2", "3")  # Used in A3
    wb.set_cell_contents("Sheet1", "B3", "2")  # Used in A1
    wb.set_cell_contents("Sheet1", "C1", "2")  # Multiplier for A1
    wb.set_cell_contents("Sheet1", "C2", "1")  # Additive for A2
    wb.set_cell_contents("Sheet1", "C3", "2")  # Subtractive for A3

    # Expected before sorting: A1=4 (2*2), A2=6 (5+1), A3=1 (3-2)

    # Sort the region A1:A3 in ascending order based on the formula results
    wb.sort_region("Sheet1", "A1", "A3", [1])

    # Validate the cells have been sorted correctly based on their formula
    # evaluations
    assert wb.get_cell_value("Sheet1", "A1") == Decimal(1)
    assert wb.get_cell_value("Sheet1", "A2") == Decimal(4)
    assert wb.get_cell_value("Sheet1", "A3") == Decimal(6)

def test_sort_with_complex_nested_formulas_ascending():
    """
    Test sorting a region with complex nested formulas in ascending order.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    # Setup complex nested formulas
    wb.set_cell_contents("Sheet1", "A1", "=B1+C1*D1")
    wb.set_cell_contents("Sheet1", "A2", "=B2+C2*D2")
    wb.set_cell_contents("Sheet1", "A3", "=B3+C3*D3")

    # Setup values
    wb.set_cell_contents("Sheet1", "B1", "1")
    wb.set_cell_contents("Sheet1", "C1", "2")
    wb.set_cell_contents("Sheet1", "D1", "3")  # A1 = 1 + 2*3 = 7

    wb.set_cell_contents("Sheet1", "B2", "2")
    wb.set_cell_contents("Sheet1", "C2", "3")
    wb.set_cell_contents("Sheet1", "D2", "4")  # A2 = 2 + 3*4 = 14

    wb.set_cell_contents("Sheet1", "B3", "3")
    wb.set_cell_contents("Sheet1", "C3", "4")
    wb.set_cell_contents("Sheet1", "D3", "1")  # A3 = 3 + 4*1 = 7

    # Sort A1:A3 based on formula results
    wb.sort_region("Sheet1", "A1", "A3", [1])

    # Check the order after sorting (expect A1 and A3 to be swapped due to same
    # results and stability)
    assert wb.get_cell_value("Sheet1", "A1") == Decimal(7)
    assert wb.get_cell_value("Sheet1", "A2") == Decimal(7)
    assert wb.get_cell_value("Sheet1", "A3") == Decimal(14)


def test_sort_with_nested_formulas_multiple_columns():
    """
    Test sorting a region based on multiple columns where one includes nested
    formulas.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")

    wb.set_cell_contents("Sheet1", "A1", "Charlie")
    wb.set_cell_contents("Sheet1", "B1", "30")
    wb.set_cell_contents("Sheet1", "C1", "=B1*2")

    wb.set_cell_contents("Sheet1", "A2", "Alice")
    wb.set_cell_contents("Sheet1", "B2", "20")
    wb.set_cell_contents("Sheet1", "C2", "=B2*2")

    wb.set_cell_contents("Sheet1", "A3", "Bob")
    wb.set_cell_contents("Sheet1", "B3", "25")
    wb.set_cell_contents("Sheet1", "C3", "=B3*2")

    # Sort the region A1:C3 based on Column A in ascending order first, then
    # Column C (formula results) in descending order
    wb.sort_region("Sheet1", "A1", "C3", [1, -3])

    # Check the order after sorting based on names first, then on the formula
    # evaluation results in descending order
    # Expected order: Alice (B2*2 is the largest), then Bob, then Charlie
    assert wb.get_cell_value("Sheet1", "A1") == "Alice"
    assert wb.get_cell_value("Sheet1", "A2") == "Bob"
    assert wb.get_cell_value("Sheet1", "A3") == "Charlie"



def test_sort_region_with_error_values():
    """
    Tests sorting functionality when the region contains cells with error values.
    This test expects cells with errors to be sorted appropriately based on their
    type.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    # Set cells where some have error values
    wb.set_cell_contents("Sheet1", "A1", "=#REF!")
    wb.set_cell_contents("Sheet1", "A2", "2")
    wb.set_cell_contents("Sheet1", "A3", "=#DIV/0!")

    wb.sort_region("Sheet1", "A1", "A3", [1])

    # Check that the first cell after sorting contains an error
    cell_value_a1 = wb.get_cell_value("Sheet1", "A1")
    assert cell_value_a1.get_type() == CellErrorType.BAD_REFERENCE
    assert (wb.get_cell_value("sheet1", "a2").get_type() ==
            CellErrorType.DIVIDE_BY_ZERO)

def test_sort_region_with_errors_and_values_ascending():
    """
    Tests sorting functionality in ascending order when the region contains
    error values alongside numeric and string values.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "3")
    wb.set_cell_contents("Sheet1", "A2", "=#DIV/0!")
    wb.set_cell_contents("Sheet1", "A3", "apple")
    wb.set_cell_contents("Sheet1", "A4", "=#VALUE!")

    wb.sort_region("Sheet1", "A1", "A4", [1])
    assert wb.get_cell_contents("Sheet1", "A3") == "3"
    assert wb.get_cell_contents("Sheet1", "A4") == "apple"
    print(wb.get_cell_value("Sheet1", "A1"))
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), CellError)
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), CellError)
    assert wb.get_cell_value("sheet1", "a3") == Decimal(3)
    assert wb.get_cell_value("sheet1", "a4") == "apple"


def test_sort_region_with_blank_cells_ascending():
    """
    Tests sorting functionality in ascending order when the region contains
    blank cells alongside numeric and string values. This test expects blank
    cells to be treated as the smallest value and thus appear first in the
    sorted range.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")

    # Set cells where some are blank
    wb.set_cell_contents("Sheet1", "A1", "10")
    wb.set_cell_contents("Sheet1", "A2", "")  # Blank cell
    wb.set_cell_contents("Sheet1", "A3", "apple")
    wb.set_cell_contents("Sheet1", "A4", "5")

    # Sort the region A1:A4 in ascending order based on the first column
    wb.sort_region("Sheet1", "A1", "A4", [1])

    # Validate the cells have been sorted correctly, with blank cells appearing first
    assert wb.get_cell_value("Sheet1", "A1") is None
    assert wb.get_cell_contents("Sheet1", "A2") == "5"
    assert wb.get_cell_contents("Sheet1", "A3") == "10"
    assert wb.get_cell_contents("Sheet1", "A4") == "apple"
