"""
This module contains stress tests for the feature set introduced in project 4.
"""

from sheets import Workbook, CellError, CellErrorType


def test_stack_iferrors():
    """
    Tests a large stacked structure of conditional evaluation which must repeat 
    Tajan's algorithm many times.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "A3", "True")
    wb.set_cell_contents("sheet1", "A2", "=if(A3,B2,C2)")
    wb.set_cell_contents("sheet1", "B2", "=A2")
    wb.set_cell_contents("sheet1", "C2", "1")
    wb.set_cell_contents("sheet1", "A1", "=iferror(A2,B1)")
    wb.set_cell_contents("sheet1", "B1", "=A1")
    assert isinstance(wb.get_cell_value("sheet1", "A1"), CellError)
    assert wb.get_cell_value("sheet1", "A1").get_type() == CellErrorType.CIRCULAR_REFERENCE
    assert isinstance(wb.get_cell_value("sheet1", "B1"), CellError)
    assert wb.get_cell_value("sheet1", "B1").get_type() == CellErrorType.CIRCULAR_REFERENCE
    assert isinstance(wb.get_cell_value("sheet1", "A2"), CellError)
    assert wb.get_cell_value("sheet1", "A2").get_type() == CellErrorType.CIRCULAR_REFERENCE
    assert isinstance(wb.get_cell_value("sheet1", "B2"), CellError)
    assert wb.get_cell_value("sheet1", "B2").get_type() == CellErrorType.CIRCULAR_REFERENCE


def test_op_precedence():
    """
    Mainly designed to test operator precedence with boolean operations
    including comparison operations and boolean functions.
    """
    wb = Workbook()
    wb.new_sheet()
    true_formulas = [
        '=tRuE=("a"<"b")=("B"<"c")=("c"<"D")=("D"<"E")=(1<2)=(1<3)=("a">1000)',
        '=TRuE=(5 = (2 - (3 - (4 - (5 - (6 - (7 - 8)))))))=True',
        '=fALSE=(FAlSE==True>"FALSE"<=TrUE)=falSe',
        '=1*2*3*4*(5+6+7+8)>1*2*3*(5+6+7)>1*2*(5+6)',
        '=aNd(1<2, and(2<3, anD(3<4, And(4<5, aNd(5<6, AND(6<7, and(7<8, True)))))))',
        '=oR(2<1,or(3<2,or(4<3,or(5<4,or(6<5,or(7<6,TRUE))))))',
        '=xOr(True, xor(FalSe, Xor(TrUe, FAlSe)), AND(1<(1<(1<True))))',
        '=and(1<>and(2!=3)) >= "True" > 1'
    ]
    for formula in true_formulas:
        wb.set_cell_contents("sheet1", "a1", formula)
        assert wb.get_cell_value("SHEET1", "A1") is True


def test_weird_indirect():
    """
    Tests weird cases of functions using references to cells
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("sheet1", "d1", "1")
    wb.set_cell_contents("sheet1", "c1", "=\"1\"")
    wb.set_cell_contents("SHEET1", "a3", "=\"Z69\"")
    wb.set_cell_contents("sheet1", "g455", "1")
    wb.set_cell_contents("sheet1", "b1", "=1*2*3-6+'sheet1'!g455")
    wb.set_cell_contents("shEEt1", "Z69", "B45")
    wb.set_cell_contents("sheet1", "b45", "no")
    wb.set_cell_contents("sHeeT1", "A1", "=indirect(indirect(indirect(\"a\" & (b1 + c1 + d1))))")
    assert wb.get_cell_value("shEEt1", "a1") == "no"
