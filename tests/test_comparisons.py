"""
Tests for the correct evaluation of comparison operators between all manner of 
literals, expressions, and references to cells.
"""

from sheets import Workbook, CellError, CellErrorType

def test_comp_bool_literal():
    """
    Test all comparison operators with combinations of boolean literals
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=TRUE=TRUE")
    wb.set_cell_contents("Sheet1", "A2", "=TRUE=FALSE")
    wb.set_cell_contents("Sheet1", "A3", "=true==TRUE")
    wb.set_cell_contents("Sheet1", "A4", "=TRUE==FALSE")
    wb.set_cell_contents("Sheet1", "A5", "=false==FALSE")
    wb.set_cell_contents("Sheet1", "A6", "=TRUE != TRUE")
    wb.set_cell_contents("Sheet1", "A7", "=TRUE != true")
    wb.set_cell_contents("Sheet1", "A8", "=TRUE != FALSE")
    wb.set_cell_contents("Sheet1", "A9", "=TRUE <> FALSE")
    wb.set_cell_contents("Sheet1", "A10", "=FALSE <> FALSE")
    wb.set_cell_contents("Sheet1", "A11", "=false <> FALSE")
    wb.set_cell_contents("Sheet1", "A12", "=TRUE < FALSE")
    wb.set_cell_contents("Sheet1", "A13", "=TRUE < TRUE")
    wb.set_cell_contents("Sheet1", "A14", "=FALSE < TRUE")
    wb.set_cell_contents("Sheet1", "A15", "=TRUE > FALSE")
    wb.set_cell_contents("Sheet1", "A16", "=TRUE > TRUE")
    wb.set_cell_contents("Sheet1", "A17", "=FALSE > TRUE")
    wb.set_cell_contents("Sheet1", "A18", "=TRUE <= FALSE")
    wb.set_cell_contents("Sheet1", "A19", "=TRUE <= TRUE")
    wb.set_cell_contents("Sheet1", "A20", "=FALSE <= TRUE")
    wb.set_cell_contents("Sheet1", "A21", "=TRUE >= FALSE")
    wb.set_cell_contents("Sheet1", "A22", "=TRUE >= TRUE")
    assert wb.get_cell_value("Sheet1", "A1") is True
    assert wb.get_cell_value("Sheet1", "A2") is False
    assert wb.get_cell_value("Sheet1", "A3") is True
    assert wb.get_cell_value("Sheet1", "A4") is False
    assert wb.get_cell_value("Sheet1", "A5") is True
    assert wb.get_cell_value("Sheet1", "A6") is False
    assert wb.get_cell_value("Sheet1", "A7") is False
    assert wb.get_cell_value("Sheet1", "A8") is True
    assert wb.get_cell_value("Sheet1", "A9") is True
    assert wb.get_cell_value("Sheet1", "A10") is False
    assert wb.get_cell_value("Sheet1", "A11") is False
    assert wb.get_cell_value("Sheet1", "A12") is False
    assert wb.get_cell_value("Sheet1", "A13") is False
    assert wb.get_cell_value("Sheet1", "A14") is True
    assert wb.get_cell_value("Sheet1", "A15") is True
    assert wb.get_cell_value("Sheet1", "A16") is False
    assert wb.get_cell_value("Sheet1", "A17") is False
    assert wb.get_cell_value("Sheet1", "A18") is False
    assert wb.get_cell_value("Sheet1", "A19") is True
    assert wb.get_cell_value("Sheet1", "A20") is True
    assert wb.get_cell_value("Sheet1", "A21") is True
    assert wb.get_cell_value("Sheet1", "A22") is True


def test_comp_empty_ref():
    """
    Tests comparison operators on the result of references to empty cells. If one
    operand is not None, then the other operand should default to the empty cell 
    value of the same type. If both operands are None, then the result should be
    equality of both operands.
    """
    wb = Workbook()
    wb.new_sheet()
    # Two empty operands should be equal
    wb.set_cell_contents("Sheet1", "B1", "=A1=A2")
    wb.set_cell_contents("Sheet1", "B2", "=A1<>A2")
    wb.set_cell_contents("Sheet1", "B3", "=A1>A2")
    wb.set_cell_contents("Sheet1", "B4", "=A1<A2")
    wb.set_cell_contents("Sheet1", "B5", "=A1>=A2")
    wb.set_cell_contents("Sheet1", "B6", "=A1<=A2")
    assert wb.get_cell_value("Sheet1", "B1") is True
    assert wb.get_cell_value("Sheet1", "B2") is False
    assert wb.get_cell_value("Sheet1", "B3") is False
    assert wb.get_cell_value("Sheet1", "B4") is False
    assert wb.get_cell_value("Sheet1", "B5") is True
    assert wb.get_cell_value("Sheet1", "B6") is True

    # Empty cell should default to 0 when compared to a number
    wb.set_cell_contents("Sheet1", "c1", "=A1=0")
    wb.set_cell_contents("Sheet1", "c2", "=A1<>0")
    wb.set_cell_contents("Sheet1", "c3", "=A1>0")
    wb.set_cell_contents("Sheet1", "c4", "=A1<0")
    wb.set_cell_contents("Sheet1", "c5", "=A1>=0")
    wb.set_cell_contents("Sheet1", "c6", "=A1<=0")
    assert wb.get_cell_value("Sheet1", "C1") is True
    assert wb.get_cell_value("Sheet1", "C2") is False
    assert wb.get_cell_value("Sheet1", "C3") is False
    assert wb.get_cell_value("Sheet1", "C4") is False
    assert wb.get_cell_value("Sheet1", "C5") is True
    assert wb.get_cell_value("Sheet1", "C6") is True

    # Empty cell should default to "" when compared to a string
    wb.set_cell_contents("Sheet1", "D1", "=A1=\"\"")
    wb.set_cell_contents("Sheet1", "D2", "=A1<>\"\"")
    wb.set_cell_contents("Sheet1", "D3", "=A1>\"\"")
    wb.set_cell_contents("Sheet1", "D4", "=A1<\"\"")
    wb.set_cell_contents("Sheet1", "D5", "=A1>=\"\"")
    wb.set_cell_contents("Sheet1", "D6", "=A1<=\"\"")
    assert wb.get_cell_value("Sheet1", "D1") is True
    assert wb.get_cell_value("Sheet1", "D2") is False
    assert wb.get_cell_value("Sheet1", "D3") is False
    assert wb.get_cell_value("Sheet1", "D4") is False
    assert wb.get_cell_value("Sheet1", "D5") is True
    assert wb.get_cell_value("Sheet1", "D6") is True


def test_comp_num_lit():
    """
    Test all comparison operators with combinations of numeric literals
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=1=1")
    wb.set_cell_contents("Sheet1", "A2", "=1=2")
    wb.set_cell_contents("Sheet1", "A3", "=1==1")
    wb.set_cell_contents("Sheet1", "A4", "=1==2")
    wb.set_cell_contents("Sheet1", "A5", "=1!=2")
    wb.set_cell_contents("Sheet1", "A6", "=1!=1")
    wb.set_cell_contents("Sheet1", "A7", "=1<>2")
    wb.set_cell_contents("Sheet1", "A8", "=1<>1")
    wb.set_cell_contents("Sheet1", "A9", "=1<2")
    wb.set_cell_contents("Sheet1", "A10", "=1<1")
    wb.set_cell_contents("Sheet1", "A11", "=1>2")
    wb.set_cell_contents("Sheet1", "A12", "=1>1")
    wb.set_cell_contents("Sheet1", "A13", "=1<=2")
    wb.set_cell_contents("Sheet1", "A14", "=1<=1")
    wb.set_cell_contents("Sheet1", "A15", "=1>=2")
    wb.set_cell_contents("Sheet1", "A16", "=1>=1")
    assert wb.get_cell_value("Sheet1", "A1") is True
    assert wb.get_cell_value("Sheet1", "A2") is False
    assert wb.get_cell_value("Sheet1", "A3") is True
    assert wb.get_cell_value("Sheet1", "A4") is False
    assert wb.get_cell_value("Sheet1", "A5") is True
    assert wb.get_cell_value("Sheet1", "A6") is False
    assert wb.get_cell_value("Sheet1", "A7") is True
    assert wb.get_cell_value("Sheet1", "A8") is False
    assert wb.get_cell_value("Sheet1", "A9") is True
    assert wb.get_cell_value("Sheet1", "A10") is False
    assert wb.get_cell_value("Sheet1", "A11") is False
    assert wb.get_cell_value("Sheet1", "A12") is False


def test_comp_str_lit():
    """
    Test all comparison operators with combinations of single char string
    literals.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=\"a\"=\"a\"")
    wb.set_cell_contents("Sheet1", "A2", "=\"a\"=\"b\"")
    wb.set_cell_contents("Sheet1", "A3", "=\"A\"==\"a\"")
    wb.set_cell_contents("Sheet1", "A4", "=\"a\"==\"b\"")
    wb.set_cell_contents("Sheet1", "A5", "=\"a\"!=\"b\"")
    wb.set_cell_contents("Sheet1", "A6", "=\"a\"!=\"A\"")
    wb.set_cell_contents("Sheet1", "A7", "=\"a\"<>\"b\"")
    wb.set_cell_contents("Sheet1", "A8", "=\"a\"<>\"a\"")
    wb.set_cell_contents("Sheet1", "A9", "=\"a\"<\"b\"")
    wb.set_cell_contents("Sheet1", "A10", "=\"a\"<\"A\"")
    wb.set_cell_contents("Sheet1", "A11", "=\"a\">\"b\"")
    wb.set_cell_contents("Sheet1", "A12", "=\"A\">\"a\"")
    wb.set_cell_contents("Sheet1", "A13", "=\"a\"<=\"b\"")
    wb.set_cell_contents("Sheet1", "A14", "=\"a\"<=\"a\"")
    wb.set_cell_contents("Sheet1", "A15", "=\"a\">=\"b\"")
    wb.set_cell_contents("Sheet1", "A16", "=\"a\">=\"a\"")
    assert wb.get_cell_value("Sheet1", "A1") is True
    assert wb.get_cell_value("Sheet1", "A2") is False
    assert wb.get_cell_value("Sheet1", "A3") is True
    assert wb.get_cell_value("Sheet1", "A4") is False
    assert wb.get_cell_value("Sheet1", "A5") is True
    assert wb.get_cell_value("Sheet1", "A6") is False
    assert wb.get_cell_value("Sheet1", "A7") is True
    assert wb.get_cell_value("Sheet1", "A8") is False
    assert wb.get_cell_value("Sheet1", "A9") is True
    assert wb.get_cell_value("Sheet1", "A10") is False
    assert wb.get_cell_value("Sheet1", "A11") is False
    assert wb.get_cell_value("Sheet1", "A12") is False
    assert wb.get_cell_value("Sheet1", "A13") is True
    assert wb.get_cell_value("Sheet1", "A14") is True
    assert wb.get_cell_value("Sheet1", "A15") is False
    assert wb.get_cell_value("Sheet1", "A16") is True


def test_comp_word_lit():
    """
    Tests for ascii based comparison of multi-character strings
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=\"hello\"=\"HELLO\"")
    wb.set_cell_contents("Sheet1", "A2", "=\"hello\"==\"goodbye\"")
    wb.set_cell_contents("Sheet1", "A3", "=\"a\" < \"[\"")
    assert wb.get_cell_value("Sheet1", "A1") is True
    assert wb.get_cell_value("Sheet1", "A2") is False
    assert wb.get_cell_value("Sheet1", "A3") is False


def test_str_num_ineq():
    """
    Tests that comparisons of strings and numbers do not automatically convert
    between types.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=\"1\"=1")
    wb.set_cell_contents("Sheet1", "A2", "=\"\"<>0")
    assert wb.get_cell_value("Sheet1", "A1") is False
    assert wb.get_cell_value("Sheet1", "A2") is True


def test_bool_nonconv():
    """
    Ensure that boolean literals do not automatically convert to numbers or
    strings when compared to other types.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=TRUE=1")
    wb.set_cell_contents("Sheet1", "A2", "=TRUE=0")
    wb.set_cell_contents("Sheet1", "A3", "=TRUE=\"TRUE\"")
    wb.set_cell_contents("Sheet1", "A4", "=TRUE=\"FALSE\"")
    assert wb.get_cell_value("Sheet1", "A1") is False
    assert wb.get_cell_value("Sheet1", "A2") is False
    assert wb.get_cell_value("Sheet1", "A3") is False
    assert wb.get_cell_value("Sheet1", "A4") is False


def test_mixed_type_comp():
    """
    Ensure that the comparison of mixed types results in the correct boolean 
    values. bool > string > number
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", '=True>"True"')
    wb.set_cell_contents("Sheet1", "A2", '=True>"False"')
    wb.set_cell_contents("Sheet1", "A3", '=False>"True"')
    wb.set_cell_contents("Sheet1", "A4", '=False>"False"')
    wb.set_cell_contents("Sheet1", "A5", '=True>1')
    wb.set_cell_contents("Sheet1", "A6", '=True>0')
    wb.set_cell_contents("Sheet1", "A7", '=False>1')
    wb.set_cell_contents("Sheet1", "A8", '=False>0')
    wb.set_cell_contents("Sheet1", "A9", '=1>"True"')
    wb.set_cell_contents("Sheet1", "A10", '=1>"False"')
    wb.set_cell_contents("Sheet1", "A11", '=0>"True"')
    wb.set_cell_contents("Sheet1", "A12", '=0>"False"')
    wb.set_cell_contents("Sheet1", "B1", '=True<"True"')
    wb.set_cell_contents("Sheet1", "B2", '=True<"False"')
    wb.set_cell_contents("Sheet1", "B3", '=False<"True"')
    wb.set_cell_contents("Sheet1", "B4", '=False<"False"')
    wb.set_cell_contents("Sheet1", "B5", '=True<1')
    wb.set_cell_contents("Sheet1", "B6", '=True<0')
    wb.set_cell_contents("Sheet1", "B7", '=False<1')
    wb.set_cell_contents("Sheet1", "B8", '=False<0')
    wb.set_cell_contents("Sheet1", "B9", '=1<"True"')
    wb.set_cell_contents("Sheet1", "B10", '=1<"False"')
    wb.set_cell_contents("Sheet1", "B11", '=0<"True"')
    assert wb.get_cell_value("Sheet1", "A1") is True
    assert wb.get_cell_value("Sheet1", "A2") is True
    assert wb.get_cell_value("Sheet1", "A3") is True
    assert wb.get_cell_value("Sheet1", "A4") is True
    assert wb.get_cell_value("Sheet1", "A5") is True
    assert wb.get_cell_value("Sheet1", "A6") is True
    assert wb.get_cell_value("Sheet1", "A7") is True
    assert wb.get_cell_value("Sheet1", "A8") is True
    assert wb.get_cell_value("Sheet1", "A9") is False
    assert wb.get_cell_value("Sheet1", "A10") is False
    assert wb.get_cell_value("Sheet1", "A11") is False
    assert wb.get_cell_value("Sheet1", "A12") is False
    assert wb.get_cell_value("Sheet1", "B1") is False
    assert wb.get_cell_value("Sheet1", "B2") is False
    assert wb.get_cell_value("Sheet1", "B3") is False
    assert wb.get_cell_value("Sheet1", "B4") is False
    assert wb.get_cell_value("Sheet1", "B5") is False
    assert wb.get_cell_value("Sheet1", "B6") is False
    assert wb.get_cell_value("Sheet1", "B7") is False
    assert wb.get_cell_value("Sheet1", "B8") is False
    assert wb.get_cell_value("Sheet1", "B9") is True
    assert wb.get_cell_value("Sheet1", "B10") is True
    assert wb.get_cell_value("Sheet1", "B11") is True


def test_comp_eval_order():
    """
    Tests the edge case given in the spec for the evaluation order of comparison
    operators.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A2", 'None type')
    wb.set_cell_contents("Sheet1", "B2", 'None')
    wb.set_cell_contents("Sheet1", "A1", '=a2 =B2&" type"')
    assert wb.get_cell_value("Sheet1", "A1") is True


def test_comp_refs():
    """
    Test a variety of comparison operators with a mix of references to cells and
    literals.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "tRuE") # True
    wb.set_cell_contents("Sheet1", "A2", "FaLsE") # False
    wb.set_cell_contents("Sheet1", "A3", "1") # 1
    wb.set_cell_contents("Sheet1", "A4", "2") # 2
    wb.set_cell_contents("Sheet1", "A5", "hello") # hello
    wb.set_cell_contents("Sheet1", "A6", "goodbye") # goodbye
    wb.set_cell_contents("Sheet1", "A7", "=A1=A1") # True
    wb.set_cell_contents("Sheet1", "A8", "=A1=A2") # False
    wb.set_cell_contents("Sheet1", "A9", "=A1>A3") # True
    wb.set_cell_contents("Sheet1", "A10", "=A1<A3") # False
    wb.set_cell_contents("Sheet1", "A11", "=A1>=A5") # True
    wb.set_cell_contents("Sheet1", "A12", "=A1<=A6") # False
    wb.set_cell_contents("Sheet1", "A13", "=A5=A5") # True
    wb.set_cell_contents("Sheet1", "A14", "=A5=A6") # False
    wb.set_cell_contents("Sheet1", "A15", "=Z100=A13") # False
    wb.set_cell_contents("Sheet1", "A16", "=Z100=A14") # True
    assert wb.get_cell_value("Sheet1", "A7") is True
    assert wb.get_cell_value("Sheet1", "A8") is False
    assert wb.get_cell_value("Sheet1", "A9") is True
    assert wb.get_cell_value("Sheet1", "A10") is False
    assert wb.get_cell_value("Sheet1", "A11") is True
    assert wb.get_cell_value("Sheet1", "A12") is False
    assert wb.get_cell_value("Sheet1", "A13") is True
    assert wb.get_cell_value("Sheet1", "A14") is False
    assert wb.get_cell_value("Sheet1", "A15") is False
    assert wb.get_cell_value("Sheet1", "A16") is True

    wb.set_cell_contents("Sheet1", "A17", "=A1 + 10 > A2 - 5") # True
    wb.set_cell_contents("Sheet1", "A18", "=A3 / 10 > A4 * 5") # False
    assert wb.get_cell_value("Sheet1", "A17") is True
    assert wb.get_cell_value("Sheet1", "A18") is False


def test_comp_error():
    """
    Test that error propagation works correctly for comparison operators on 
    literal values only.
    """
    wb = Workbook()
    wb.new_sheet()
    # Ensure all literals with a compare op will lead to the correct error value
    wb.set_cell_contents("Sheet1", "A1", "=1/0=1")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), CellError)
    assert wb.get_cell_value("Sheet1", "A1").get_type() == CellErrorType.DIVIDE_BY_ZERO
    wb.set_cell_contents("Sheet1", "A2", "=1=1+")
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), CellError)
    assert wb.get_cell_value("Sheet1", "A2").get_type() == CellErrorType.PARSE_ERROR
    wb.set_cell_contents("Sheet1", "A3", '=1=1+"five"')
    assert isinstance(wb.get_cell_value("Sheet1", "A3"), CellError)
    assert wb.get_cell_value("Sheet1", "A3").get_type() == CellErrorType.TYPE_ERROR
    wb.set_cell_contents("Sheet1", "A4", '=A4<2')
    assert isinstance(wb.get_cell_value("Sheet1", "A4"), CellError)
    assert wb.get_cell_value("Sheet1", "A4").get_type() == CellErrorType.CIRCULAR_REFERENCE


def test_comp_ref_error():
    """
    Ensure that comparison operators propagate errors from references correctly.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=1/0")
    wb.set_cell_contents("Sheet1", "A2", "=1")
    wb.set_cell_contents("Sheet1", "A3", "=A1=A2")
    assert isinstance(wb.get_cell_value("Sheet1", "A3"), CellError)
    assert wb.get_cell_value("Sheet1", "A3").get_type() == CellErrorType.DIVIDE_BY_ZERO
    wb.set_cell_contents("sheet1", "a4", "=5 > 'sheEt2'!a1")
    assert isinstance(wb.get_cell_value("Sheet1", "A4"), CellError)
    assert wb.get_cell_value("Sheet1", "A4").get_type() == CellErrorType.BAD_REFERENCE
    wb.set_cell_contents("Sheet1", "A5", "=A4=1")
    assert isinstance(wb.get_cell_value("Sheet1", "A5"), CellError)
    assert wb.get_cell_value("Sheet1", "A5").get_type() == CellErrorType.BAD_REFERENCE
    wb.set_cell_contents("Sheet1", "A6", "=A7")
    wb.set_cell_contents("Sheet1", "A7", "=A6")
    wb.set_cell_contents("Sheet1", "A8", "=A6=A7")
    assert isinstance(wb.get_cell_value("Sheet1", "A8"), CellError)
    assert wb.get_cell_value("Sheet1", "A8").get_type() == CellErrorType.CIRCULAR_REFERENCE
