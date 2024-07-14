"""
These tests should test the entire sheets package to ensure that it complies 
with the specification. These tests are aimed at the full system integration.
"""

# Import testing utilities
import decimal
import pytest
import test_utils as utils

# Import tested modules
import sheets


def test_spec_smoke():
    """
    Runs the exact smoke test example given in the spec for project1.
    """
    # Make sure version is correct and is a string
    assert sheets.version == "1.3"
    assert isinstance(sheets.version, str)

    # Ensure user can create a workbook
    wb = sheets.Workbook()

    # Test creating a new sheet
    index, name = wb.new_sheet()
    assert index == 0
    assert name == "Sheet1"

    # Test populating some cells with different types
    wb.set_cell_contents(name, 'a1', '12')
    wb.set_cell_contents(name, 'b1', '34')
    wb.set_cell_contents(name, 'c1', '=a1+b1')

    # value should be a decimal.Decimal('46')
    value = wb.get_cell_value(name, 'c1')
    assert value == decimal.Decimal('46')

    # Test referencing a cell in a nonexistent sheet
    wb.set_cell_contents(name, 'd3', '=nonexistent!b4')
    value = wb.get_cell_value(name, 'd3')
    assert isinstance(value, sheets.CellError)
    assert value.get_type() == sheets.CellErrorType.BAD_REFERENCE

    # Cells can be set to error values as well
    wb.set_cell_contents(name, 'e1', '#div/0!')
    wb.set_cell_contents(name, 'e2', '=e1+5')
    value = wb.get_cell_value(name, 'e2')
    assert isinstance(value, sheets.CellError)
    assert value.get_type() == sheets.CellErrorType.DIVIDE_BY_ZERO

    # Test an error directly input into a formula
    wb.set_cell_contents(name, 'f1', '=#REF! + 5')
    value = wb.get_cell_value(name, 'f1')
    assert isinstance(value, sheets.CellError)


def test_cycle_detection():
    """
    Tests that the interaction graph correctly detects cycles in cells.
    """
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "Z12", "=Z12")
    assert isinstance(wb.get_cell_value("Sheet1", "Z12"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "Z12").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)
    wb.set_cell_contents("Sheet1", "A1", "1")
    for i in range(2, 10):
        wb.set_cell_contents("Sheet1", f"A{i}",f"=A{i-1}+1")
    wb.set_cell_contents("Sheet1", "A1", "=A9+1")
    for i in range(1, 10):
        assert isinstance(wb.get_cell_value("Sheet1", f"A{i}"), sheets.CellError)
        assert (wb.get_cell_value("Sheet1", f"A{i}").get_type()
                == sheets.CellErrorType.CIRCULAR_REFERENCE)
    wb.set_cell_contents("Sheet1", "A1", "1")
    for i in range(1, 10):
        assert not isinstance(wb.get_cell_value("Sheet1", f"A{i}"), sheets.CellError)


def test_error_order():
    """
    Tests that the order with which errors are returned is correct according to 
    the spec, i.e:
        - Parsing errors
        - Circular references
        - Any other error (first evaluated)
    """
    # Set up testing workbook
    wb = sheets.Workbook()
    wb.new_sheet()

    # Test that a parse error has precedence over:
    # DIV/0!
    wb.set_cell_contents("Sheet1", "A1", "=1/0")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    wb.set_cell_contents("Sheet1", "A2", "=A1++")
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A2").get_type()
            == sheets.CellErrorType.PARSE_ERROR)

    #CIRCREF!
    wb.set_cell_contents("Sheet1", "A3", "1")
    wb.set_cell_contents("Sheet1", "A4", "=A3+1")
    wb.set_cell_contents("Sheet1", "A5", "=A4+1")
    wb.set_cell_contents("Sheet1", "A3", "=A5+")
    assert isinstance(wb.get_cell_value("Sheet1", "A3"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A3").get_type()
            == sheets.CellErrorType.PARSE_ERROR)

    #BAD REF!
    wb.set_cell_contents("Sheet1", "A6", "=Sheet2!A3+")
    assert isinstance(wb.get_cell_value("Sheet1", "A6"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A6").get_type()
            == sheets.CellErrorType.PARSE_ERROR)

    #TYPE_ERROR
    wb.set_cell_contents("Sheet1", "A7", "test")
    wb.set_cell_contents("Sheet1", "A8", "=A7+1+")
    assert isinstance(wb.get_cell_value("Sheet1", "A8"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A8").get_type()
            == sheets.CellErrorType.PARSE_ERROR)

    # Test that a circular reference has precedence over:
    # DIV/0!
    wb.set_cell_contents("Sheet1", "A7", "=1")
    wb.set_cell_contents("Sheet1", "A8", "=A7+1")
    wb.set_cell_contents("Sheet1", "A9", "=A8+1")
    wb.set_cell_contents("Sheet1", "A7", "=1/0+A9")
    assert isinstance(wb.get_cell_value("Sheet1", "A7"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A7").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)

    #BAD REF!
    wb.set_cell_contents("Sheet1", "A10", "=Sheet2!A3+A9")
    assert isinstance(wb.get_cell_value("Sheet1", "A10"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A10").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)

    # BAD REF! 2
    wb.set_cell_contents("sheet1", "b1", "=c1+sheet5!a1")
    wb.set_cell_contents("sheet1", "c1", "=b1")
    assert isinstance(wb.get_cell_value("sheet1", "b1"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "b1").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("sheet1", "c1"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "c1").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)

    #TYPE_ERROR
    wb.set_cell_contents("Sheet1", "A11", "test")
    wb.set_cell_contents("Sheet1", "A12", "=A11+1+A9")
    assert isinstance(wb.get_cell_value("Sheet1", "A12"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A12").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)


def test_circ_ref_priority_iso():
    """
    Tests in isolation that the priority of circular reference errors is correct
    ensuring case insensitivity in local sheet references.
    """
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "a1", "=b1+Sheet4!b1")
    wb.set_cell_contents("sheet1", "b1", "=a1")
    assert isinstance(wb.get_cell_value("Sheet1", "a1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "a1").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "b1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B1").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)


def test_error_prop():
    """
    Tests that errors propagate correctly. Any cell referencing a cell which
    contains an error should then also evaluate to that error.
    """
    wb = sheets.Workbook()
    wb.new_sheet()

    #first check if error will propagate
    wb.set_cell_contents("Sheet1", "B1", "=ZZZZZ99999")
    wb.set_cell_contents("Sheet1", "B2", "=B1")
    wb.set_cell_contents("Sheet1", "B3", "=B2")
    assert isinstance(wb.get_cell_value("Sheet1", "B1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B1").get_type()
            == sheets.CellErrorType.BAD_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "B2"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B2").get_type()
            == sheets.CellErrorType.BAD_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "B3"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B3").get_type()
            == sheets.CellErrorType.BAD_REFERENCE)

    #check if changing the error to a different type of same priority propagates
    #correctly
    wb.set_cell_contents("Sheet1", "B1", "=1/0")
    assert isinstance(wb.get_cell_value("Sheet1", "B1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B1").get_type()
            == sheets.CellErrorType.DIVIDE_BY_ZERO)
    assert isinstance(wb.get_cell_value("Sheet1", "B2"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B2").get_type()
            == sheets.CellErrorType.DIVIDE_BY_ZERO)
    assert isinstance(wb.get_cell_value("Sheet1", "B3"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B3").get_type()
            == sheets.CellErrorType.DIVIDE_BY_ZERO)
    #change contents of cell such that a loop is created and test if circ_ref
    #error propagates
    wb.set_cell_contents("Sheet1", "B1", "=B3")
    assert isinstance(wb.get_cell_value("Sheet1", "B1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B1").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "B2"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B2").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("Sheet1", "B3"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B3").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)

    # change contents of cell such that a parse error is created and test if it
    # propagagtes
    wb.set_cell_contents("Sheet1", "B1", "=B3++")
    assert isinstance(wb.get_cell_value("Sheet1", "B1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B1").get_type()
            == sheets.CellErrorType.PARSE_ERROR)
    assert isinstance(wb.get_cell_value("Sheet1", "B2"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B2").get_type()
            == sheets.CellErrorType.PARSE_ERROR)
    assert isinstance(wb.get_cell_value("Sheet1", "B3"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "B3").get_type()
            == sheets.CellErrorType.PARSE_ERROR)


def test_casing():
    """
    Check that the system is sufficiently robust to casing such that it will:
        - Ignore casing when referencing cells or sheets
        - Ignore casing when setting cell contents to errors
        - Remember the given casing of a sheet name
        - One may not add a sheet with the same name in different casing
    """
    # Set up the testt workbook
    wb = sheets.Workbook()
    wb.new_sheet("cAsEcOnFuSiOn")

    # Ensure we can set cells with all casings
    wb.set_cell_contents("caseconfusion", "a1", "1")
    wb.set_cell_contents("CASECONFUSION", "a2", "2")
    wb.set_cell_contents("CaseConfusion", "A3", "3")
    wb.set_cell_contents("cASEcONFUSIOn", "A4", "4")

    # Ensure we can get cells with all casings
    assert wb.get_cell_value("CASECONFUSION", "A1") == decimal.Decimal("1")
    assert wb.get_cell_value("caseconfusion", "A2") == decimal.Decimal("2")
    assert wb.get_cell_value("cASEcONFUSIOn", "a3") == decimal.Decimal("3")
    assert wb.get_cell_value("CaseConfusion", "a4") == decimal.Decimal("4")

    # Ensure we can set cells with all casings to errors
    wb.set_cell_contents("caseconfusion", "a1", "#DIV/0!")
    wb.set_cell_contents("CASECONFUSION", "A2", "#div/0!")
    assert isinstance(wb.get_cell_value("CaseConfusion", "a1"), sheets.CellError)
    assert isinstance(wb.get_cell_value("caseconfusion", "A2"), sheets.CellError)
    assert (wb.get_cell_value("CaseConfusion", "a1").get_type()
            == sheets.CellErrorType.DIVIDE_BY_ZERO)
    assert (wb.get_cell_value("caseconfusion", "A2").get_type()
            == sheets.CellErrorType.DIVIDE_BY_ZERO)

    # Ensure casing is ignored when referencing cells or sheets
    wb.set_cell_contents("caseconfusion", "a1", "1")
    wb.set_cell_contents("CASECONFUSION", "A2", "2")
    wb.set_cell_contents("caseconfusion", "a3", "=A1+A2")
    wb.set_cell_contents("CASECONFUSION", "A4", "=a1+a2")
    wb.set_cell_contents("CaseConfusion", "a5", "=a1+A2")
    wb.set_cell_contents("cASEcONFUSIOn", "A6", "=A1+a2")
    assert wb.get_cell_value("caseconfusion", "A3") == decimal.Decimal("3")
    assert wb.get_cell_value("CASECONFUSION", "a4") == decimal.Decimal("3")
    assert wb.get_cell_value("CaseConfusion", "A5") == decimal.Decimal("3")
    assert wb.get_cell_value("cASEcONFUSIOn", "a6") == decimal.Decimal("3")

    # Ensure the workbook maintained the original case and cannot re-add the sheet
    assert wb.list_sheets() == ["cAsEcOnFuSiOn"]
    with pytest.raises(ValueError):
        wb.new_sheet("CASECONFUSION")

    # Ensure cross-sheet referencing is case-insensitive
    wb.new_sheet("CoNfUsEdCaSe")
    wb.set_cell_contents("confusedcase", "A1", "1")
    wb.set_cell_contents("caseconfusion", "A2", "=confusedcase!a1")
    assert wb.get_cell_value("caseconfusion", "A2") == decimal.Decimal("1")


def test_decimal_edge_cases():
    """
    Tests edge cases for the Decimal class for which Decimal() can interpret the 
    content as a number, but should not do so.
    """
    wb = sheets.Workbook()
    wb.new_sheet()

    # Test that Decimal() does not interpret the following as numbers
    wb.set_cell_contents("Sheet1", "A1", "Infinity")
    wb.set_cell_contents("Sheet1", "A2", "NaN")
    wb.set_cell_contents("Sheet1", "A3", "Inf")
    wb.set_cell_contents("Sheet1", "A4", "sNaN")
    assert wb.get_cell_value("Sheet1", "A1") == "Infinity"
    assert wb.get_cell_value("Sheet1", "A2") == "NaN"
    assert wb.get_cell_value("Sheet1", "A3") == "Inf"
    assert wb.get_cell_value("Sheet1", "A4") == "sNaN"


def test_type_conv():
    """test adding a string with white space with a number"""
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "'    12.3")
    wb.set_cell_contents("Sheet1", "A2","5.3")
    wb.set_cell_contents("Sheet1", "A3", "=A1*A2")
    assert utils.check_dec_equal(wb.get_cell_value("Sheet1", "A3"),
                                 decimal.Decimal(65.19))

    #test using an empty cell as a number
    wb.set_cell_contents("Sheet1", "B2", "=B1+5")
    wb.set_cell_contents("Sheet1", "B3", "")
    wb.set_cell_contents("Sheet1", "B4", "=B1+B3")
    assert wb.get_cell_value("Sheet1", "B1") is None
    assert wb.get_cell_value("Sheet1", "B2") == decimal.Decimal(5)
    assert wb.get_cell_value("Sheet1", "B4") == decimal.Decimal(0)

    #test using an empty cell as a string
    wb.set_cell_contents("Sheet1", "C2", "'hello")
    wb.set_cell_contents("Sheet1", "C3", "=C2&C1")
    wb.set_cell_contents("Sheet1", "C4", "=B1&B3")
    assert wb.get_cell_value("Sheet1", "C3") == "hello"
    assert wb.get_cell_value("Sheet1", "C4") == ""

    #test using an empty cell in an ambiguous way
    wb.set_cell_contents("Sheet1", "D2", "=D1")
    assert wb.get_cell_value("Sheet1", "D2") == decimal.Decimal("0")


def test_sheet_extent():
    """
    Ensure that the sheet extent is correctly updated when cells are added or
    removed and is accessible from the Workbook level.
    """
    wb = sheets.Workbook()
    wb.new_sheet()

    # Ensure the sheet extent is initially empty
    assert wb.get_sheet_extent("Sheet1") == (0, 0)

    # Ensure the sheet extent is correctly updated when cells are added
    wb.set_cell_contents("Sheet1", "A1", "1")
    assert wb.get_sheet_extent("Sheet1") == (1, 1)
    wb.set_cell_contents("Sheet1", "A2", "2")
    assert wb.get_sheet_extent("Sheet1") == (1, 2)
    wb.set_cell_contents("Sheet1", "B1", "3")
    assert wb.get_sheet_extent("Sheet1") == (2, 2)
    wb.set_cell_contents("Sheet1", "B2", "4")
    assert wb.get_sheet_extent("Sheet1") == (2, 2)

    # Ensure the sheet extent is correctly updated when cells are removed
    wb.set_cell_contents("Sheet1", "A1", "")
    assert wb.get_sheet_extent("Sheet1") == (2, 2)
    wb.set_cell_contents("Sheet1", "A2", "")
    assert wb.get_sheet_extent("Sheet1") == (2, 2)
    wb.set_cell_contents("Sheet1", "B1", "")
    assert wb.get_sheet_extent("Sheet1") == (2, 2)
    wb.set_cell_contents("Sheet1", "B2", "")
    assert wb.get_sheet_extent("Sheet1") == (0, 0)


def test_swap_referr():
    """
    Tests that If A's BAD_REFERENCE error is due to missing a sheet S, and S
    gets added, then A should no longer be a BAD_REFERENCE error. (also tested
    in test_chains)
    """
    wb = sheets.Workbook()
    wb.new_sheet()

    # Set to empty reference
    wb.set_cell_contents("sheet1", "a1", "=sheet2!a1")
    assert isinstance(wb.get_cell_value("sheet1", "a1"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "a1").get_type()
            == sheets.CellErrorType.BAD_REFERENCE)

    # Create cell - should default value to 0 when cell empty
    wb.new_sheet("sheet2")
    assert wb.get_cell_value("sheet1", "a1") == decimal.Decimal("0")

    wb.set_cell_contents("sheet2", "a1", "5")
    assert wb.get_cell_value("sheet1", "a1") == decimal.Decimal("5")


def test_del_ref_err():
    """If A refers to a cell in some sheet S, but then sheet S is deleted, A
    should be updated to be a BAD_REFERENCE error."""
    wb = sheets.Workbook()
    wb.new_sheet()

    # Set to empty reference
    wb.set_cell_contents("sheet1", "a1", "=sheet2!a1")
    assert isinstance(wb.get_cell_value("sheet1", "a1"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "a1").get_type()
            == sheets.CellErrorType.BAD_REFERENCE)

    # Create cell - should default value to 0 when cell empty
    wb.new_sheet("sheet2")
    assert wb.get_cell_value("sheet1", "a1") == decimal.Decimal("0")

    wb.set_cell_contents("sheet2", "a1", "5")
    assert wb.get_cell_value("sheet1", "a1") == decimal.Decimal("5")

    # Delete sheet
    wb.del_sheet("sheet2")
    assert isinstance(wb.get_cell_value("sheet1", "a1"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "a1").get_type()
            == sheets.CellErrorType.BAD_REFERENCE)


def test_minus_circref():
    """If A is a circref error, and B=-A, then B is also a circref error."""
    wb = sheets.Workbook()
    wb.new_sheet()

    # Set to circular reference
    wb.set_cell_contents("sheet1", "a1", "=a1")
    assert isinstance(wb.get_cell_value("sheet1", "a1"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "a1").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)

    wb.set_cell_contents("sheet1", "a2", "=-a1")
    assert isinstance(wb.get_cell_value("sheet1", "a2"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "a2").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)


def test_multi_loop():
    """
    Tests that multiple loops across the workbook are all detected as cycles
    and handled.
    """
    wb = sheets.Workbook()
    wb.new_sheet()

    # Set to circular reference
    wb.set_cell_contents("sheet1", "a1", "=a1")
    wb.set_cell_contents("sheet1", "b1", "=c1")
    wb.set_cell_contents("sheet1", "c1", "=b1")
    assert isinstance(wb.get_cell_value("sheet1", "a1"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "a1").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("sheet1", "b1"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "b1").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("sheet1", "c1"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "c1").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)


def test_multi_sheet_cycle():
    """
    Ensures that cycles which go across sheets are caught and handled.
    """
    wb = sheets.Workbook()
    wb.new_sheet("Sheet1")
    wb.new_sheet("Sheet2")

    # Set to circular reference
    wb.set_cell_contents("sheet1", "a1", "=sheet2!a1")
    wb.set_cell_contents("sheet2", "a1", "=sheet1!A1")
    assert isinstance(wb.get_cell_value("sheet1", "a1"), sheets.CellError)
    assert (wb.get_cell_value("sheet1", "A1").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)
    assert isinstance(wb.get_cell_value("sheet2", "a1"), sheets.CellError)
    assert (wb.get_cell_value("sheet2", "A1").get_type()
            == sheets.CellErrorType.CIRCULAR_REFERENCE)


def test_missing_op_errs():
    """
    Tests that an invalid formula containing operators missing operands cause a
    parse error.
    """
    wb = sheets.Workbook()
    wb.new_sheet()

    # Test that a missing operand causes a parse error
    wb.set_cell_contents("Sheet1", "A1", "=+")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type()
            == sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=-")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type()
            == sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=*")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type()
            == sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=/")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type()
            == sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=5*")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type()
            == sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=5/")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type()
            == sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=5+")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type()
            == sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=5-")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type()
            == sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=&")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type()
            == sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=\"str\"&")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.PARSE_ERROR)


def test_parse_err_missing_quote():
    """
    Tests that a formula which is missing one or more quotes for strings triggers 
    a parse error.
    """
    wb = sheets.Workbook()
    wb.new_sheet()

    # Test that a missing quote causes a parse error
    wb.set_cell_contents("Sheet1", "A1", "=\"str")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=\"str\"&\"str")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=\"str\"&\"str\"&\"str")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.PARSE_ERROR)

def test_parse_err_prop():
    """
    This test ensures that if A is a parse error, and B depends on A, then B
    should also be a parse error. This test also ensures that if A is a parse
    error, and B=-A, then B is a parse error.
    """
    wb = sheets.Workbook()
    wb.new_sheet()

    # Test that a parse error propagates
    wb.set_cell_contents("Sheet1", "A1", "=1/")
    wb.set_cell_contents("Sheet1", "A2", "=A1+1")
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A2").get_type() ==
            sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=/0")
    wb.set_cell_contents("Sheet1", "A2", "=A1+1")
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A2").get_type() ==
            sheets.CellErrorType.PARSE_ERROR)
    wb.set_cell_contents("Sheet1", "A1", "=1*")
    wb.set_cell_contents("Sheet1", "A2", "=-A1")
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A2").get_type() ==
            sheets.CellErrorType.PARSE_ERROR)


def test_abs_ref_graph():
    """
    Tests for correct behavior of the ci_graph when there are absolute cell
    references in the formulas.
    """
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "a1", "=sheet1!$a2")
    assert wb.interaction_graph.graph[("sheet1", "A1")] == [("sheet1", "A2")]
    wb.set_cell_contents("ShEeT1", "b1", "=sHeET1!$a$5")
    assert wb.interaction_graph.graph[("sheet1", "B1")] == [("sheet1", "A5")]
    wb.set_cell_contents("shEEt1", "C1", "=$z$1 + 'Sheet1'!$z$2 + \"$Z3\" - ShEEt1!z$4")
    assert wb.interaction_graph.graph[("sheet1", "C1")] == [("sheet1", "Z1"),
                                                              ("sheet1", "Z2"),
                                                              ("sheet1", "Z4")]


utils.run_all(__name__)
