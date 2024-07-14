"""
Tests for correct behavior when evaluating formula expressions independent of anything else.
"""

# import testing packages
from decimal import Decimal
import test_utils as utils

# import modules to be tested
from sheets.workbook import Workbook
from sheets.cell import PARSER
from sheets.evaluator import Evaluator, error_dict
from sheets.error_types import CellErrorType, CellError


def test_rand_add_expr():
    """
    Tests for correct behavior when evaluating an addition and subtraction expression.
    """
    wb = Workbook()
    _, _ = wb.new_sheet(), wb.new_sheet()
    location1, location2 = utils.rand_loc(), utils.rand_loc()
    ref_loc1 = utils.ref_loc(location1)
    ref_loc2 = utils.ref_loc(location2)
    rand_num1, rand_num2 = utils.generate_random_number(), utils.generate_random_number()

    wb.set_cell_contents("sheet1", location1, str(rand_num1))
    wb.set_cell_contents("sheet2", location2, str(rand_num2))

    evaler = Evaluator(wb, wb.sheets["sheet1".lower()])
    t1 = PARSER.parse(f"={ref_loc1}+sheet2!{ref_loc2}")
    assert utils.check_dec_equal(evaler.visit(t1), Decimal(rand_num1 + rand_num2))

    t2 = PARSER.parse(f"={rand_num1}-{rand_num2}")
    assert utils.check_dec_equal(evaler.visit(t2), Decimal(rand_num1 - rand_num2))


def test_rand_add_parens():
    """
    Tests for correct behavior when evaluating an addition and subtraction expression
    with parentheses.
    """
    wb = Workbook()
    sheet_name1, sheet_name2 = utils.generate_random_string(), utils.generate_random_string()
    wb.new_sheet(sheet_name1)
    wb.new_sheet(sheet_name2)
    location1, location2 = utils.rand_loc(), utils.rand_loc()
    ref_loc1 = utils.ref_loc(location1)
    ref_loc2 = utils.ref_loc(location2)
    rand_num1, rand_num2 = utils.generate_random_number(), utils.generate_random_number()

    wb.set_cell_contents(sheet_name1, location1, str(rand_num1))
    wb.set_cell_contents(sheet_name2, location2, str(rand_num2))

    evaler = Evaluator(wb, wb.sheets[sheet_name1.lower()])
    t1 = PARSER.parse(f"=({ref_loc1}+{sheet_name2}!{ref_loc2})")
    assert utils.check_dec_equal(evaler.visit(t1), Decimal(rand_num1 + rand_num2))

    t2 = PARSER.parse(f"=({rand_num1}-{rand_num2})")
    assert utils.check_dec_equal(evaler.visit(t2), Decimal(rand_num1 - rand_num2))


def test_rand_mul_expr():
    """
    Tests for correct behavior when evaluating a multiplication and division
    expression.
    """
    wb = Workbook()
    sheet_name1, sheet_name2 = utils.generate_random_string(), utils.generate_random_string()
    wb.new_sheet(sheet_name1)
    wb.new_sheet(sheet_name2)
    location1, location2 = utils.rand_loc(), utils.rand_loc()
    ref_loc1 = utils.ref_loc(location1)
    ref_loc2 = utils.ref_loc(location2)
    rand_num1, rand_num2 = (abs(utils.generate_random_number()) + 1,
                            abs(utils.generate_random_number()) + 1)

    wb.set_cell_contents(sheet_name1, location1, "0")
    wb.set_cell_contents(sheet_name2, location2, str(rand_num2))

    evaler = Evaluator(wb, wb.sheets[sheet_name1.lower()])
    t1 = PARSER.parse(f"={ref_loc1}*{sheet_name2}!{ref_loc2}")
    assert utils.check_dec_equal(evaler.visit(t1), Decimal(0))

    wb.set_cell_contents(sheet_name1, location1, str(rand_num1))
    t2 = PARSER.parse(f"={rand_num1}*{rand_num2}")
    assert utils.check_dec_equal(evaler.visit(t1), Decimal(rand_num1 * rand_num2))

    t2 = PARSER.parse(f"={rand_num1}/{rand_num2}")
    assert utils.check_dec_equal(evaler.visit(t2), Decimal(rand_num1 / rand_num2))


def test_rand_mul_parens():
    """
    Tests for correct behavior when evaluating a multiplication and division
    expression with parentheses.
    """
    wb = Workbook()
    sheet_name1, sheet_name2 = utils.generate_random_string(), utils.generate_random_string()
    wb.new_sheet(sheet_name1)
    wb.new_sheet(sheet_name2)
    location1, location2 = utils.rand_loc(), utils.rand_loc()
    ref_loc1 = utils.ref_loc(location1)
    ref_loc2 = utils.ref_loc(location2)
    rand_num1, rand_num2 = (abs(utils.generate_random_number()) + 1,
                            abs(utils.generate_random_number()) + 1)

    wb.set_cell_contents(sheet_name1, location1, "0")
    wb.set_cell_contents(sheet_name2, location2, str(rand_num2))

    evaler = Evaluator(wb, wb.sheets[sheet_name1.lower()])
    t1 = PARSER.parse(f"=({ref_loc1}*{sheet_name2}!{ref_loc2})")
    assert utils.check_dec_equal(evaler.visit(t1), Decimal(0))

    wb.set_cell_contents(sheet_name1, location1, str(rand_num1))
    t2 = PARSER.parse(f"=({rand_num1}*{rand_num2})")
    assert utils.check_dec_equal(evaler.visit(t1),
                                 Decimal(rand_num1 * rand_num2))

    t2 = PARSER.parse(f"=({rand_num1}/{rand_num2})")
    assert utils.check_dec_equal(evaler.visit(t2),
                                 Decimal(rand_num1 / rand_num2))


def test_rand_concat_expr():
    """
    Tests for correct behavior when evaluating a concatenation expression.
    """
    wb = Workbook()
    sheet_name1, sheet_name2 = (utils.generate_random_string(),
                                utils.generate_random_string())
    wb.new_sheet(sheet_name1)
    wb.new_sheet(sheet_name2)
    location1, location2 = utils.rand_loc(), utils.rand_loc()
    ref_loc1 = utils.ref_loc(location1)
    ref_loc2 = utils.ref_loc(location2)
    rand_string1, rand_string2 = (utils.generate_random_string(),
                                  utils.generate_random_string())

    wb.set_cell_contents(sheet_name1, location1, rand_string1)
    wb.set_cell_contents(sheet_name2, location2, rand_string2)

    formula = f"={ref_loc1}&{sheet_name2}!{ref_loc2}"

    evaler = Evaluator(wb, wb.sheets[sheet_name1.lower()])
    t = PARSER.parse(formula)
    assert evaler.visit(t) == rand_string1 + rand_string2


def test_rand_unary_op():
    """
    Tests for correct behavior when evaluating a unary operation.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    evaler = Evaluator(wb, wb.sheets["Sheet1".lower()])
    rand_num1, rand_num2 = (abs(utils.generate_random_number()),
                            abs(utils.generate_random_number()))
    t1 = PARSER.parse(f"=-{rand_num1}")
    assert evaler.visit(t1) == Decimal(-rand_num1)

    t2 = PARSER.parse(f"=+{rand_num2}")
    assert evaler.visit(t2) == Decimal(rand_num2)

    t3= PARSER.parse(f"=-{rand_num1}+{rand_num2}")
    assert evaler.visit(t3) == Decimal(-rand_num1 + rand_num2)


def test_error():
    """
    Tests that setting a cell to an error value is handled correctly.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    evaler = Evaluator(wb, wb.sheets["Sheet1".lower()])
    t1 = PARSER.parse("=#ERROR!")
    assert isinstance(evaler.error(t1), CellError)
    assert evaler.error(t1).get_type() == error_dict["#ERROR!"]

    t2 = PARSER.parse("=#DIV/0!")
    assert isinstance(evaler.error(t2), CellError)
    assert evaler.error(t2).get_type() == error_dict["#DIV/0!"]

    t3 = PARSER.parse("=#CIRCREF!")
    assert isinstance(evaler.error(t3), CellError)
    assert evaler.error(t3).get_type() == error_dict["#CIRCREF!"]

    t4 = PARSER.parse("=#REF!")
    assert isinstance(evaler.error(t4), CellError)
    assert evaler.error(t4).get_type() == error_dict["#REF!"]

    t5 = PARSER.parse("=#NAME?")
    assert isinstance(evaler.error(t5), CellError)
    assert evaler.error(t5).get_type() == error_dict["#NAME?"]

    t6 = PARSER.parse("=#VALUE!")
    assert isinstance(evaler.error(t6), CellError)
    assert evaler.error(t6).get_type() == error_dict["#VALUE!"]


def test_rand_cell_ref_valid():
    """
    Tests that valid and invalid cell refs across a single sheet or across
    multiple sheets are handled correctly.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    evaler = Evaluator(wb, wb.sheets["Sheet1".lower()])
    location = utils.rand_loc()
    ref_loc = utils.ref_loc(location)
    random_number = utils.generate_random_number()
    wb.set_cell_contents("Sheet1", location, str(random_number))
    t1 = PARSER.parse(f"={ref_loc}")
    assert evaler.visit(t1) == random_number


def test_rand_check_type():
    """
    Tests that check_type is handled correctly.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    evaler = Evaluator(wb, wb.sheets["Sheet1".lower()])

    rand_num = utils.generate_random_number()
    test_str = f"'{rand_num}"
    assert evaler.check_numeric(test_str) == Decimal(rand_num)

    err = CellError(CellErrorType.BAD_REFERENCE, "No such cell")
    assert isinstance(evaler.check_numeric(err), CellError)
    assert evaler.check_numeric(err).get_type() == CellErrorType.BAD_REFERENCE

    rand_string = utils.generate_random_string()
    assert isinstance(evaler.check_numeric(rand_string), CellError)
    assert (evaler.check_numeric(rand_string).get_type() ==
            CellErrorType.TYPE_ERROR)


def test_chains():
    """
    Tests that a chain of references across sheets is handled correctly
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=1")
    for i in range(2, 9):
        wb.new_sheet()
        wb.set_cell_contents(f"Sheet{i}", "A1", f"=ShEet{i-1}!$a$1+1")
    assert wb.get_cell_value("ShEEt8", "A1") == 8

    # Delete the head of the chain and ensure errors propogate
    wb.del_sheet("Sheet1")
    assert isinstance(wb.get_cell_value("Sheet8", "A1"), CellError)

    # Replace the head of the chain and ensure the values are reset properly
    _, name = wb.new_sheet()
    assert name == "Sheet1"
    wb.set_cell_contents("Sheet1", "A1", "=2")
    assert wb.get_cell_value("Sheet8", "A1") == 9


def test_rand_order_op():
    """
    Tests that expressions are evaluated using the correct order of operations
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    evaler = Evaluator(wb, wb.sheets["Sheet1".lower()])
    rand_num1, rand_num2, rand_num3 = (abs(utils.generate_random_number()) + 1,
                                       abs(utils.generate_random_number()) + 1,
                                       abs(utils.generate_random_number()) + 1)
    t1 = PARSER.parse(f"={rand_num1}+{rand_num2}*{rand_num3}")
    assert utils.check_dec_equal(evaler.visit(t1),
                                 Decimal(rand_num1 + rand_num2 * rand_num3))

    t2 = PARSER.parse(f"=({rand_num1}+{rand_num2})*{rand_num3}")
    assert utils.check_dec_equal(evaler.visit(t2),
                                 Decimal((rand_num1 + rand_num2) * rand_num3))

    t3 = PARSER.parse(f"={rand_num1}*{rand_num2}+{rand_num3}")
    assert utils.check_dec_equal(evaler.visit(t3),
                                 Decimal(rand_num1 * rand_num2 + rand_num3))

    t4 = PARSER.parse(f"={rand_num1}/{rand_num2}+{rand_num3}")
    assert utils.check_dec_equal(evaler.visit(t4),
                                 Decimal(rand_num1 / rand_num2 + rand_num3))

    t5 = PARSER.parse(f"={rand_num1}+{rand_num2}/{rand_num3}")
    assert utils.check_dec_equal(evaler.visit(t5),
                                 Decimal(rand_num1 + rand_num2 / rand_num3))

    t6 = PARSER.parse(f"={rand_num1}-{rand_num2}+{rand_num3}")
    assert utils.check_dec_equal(evaler.visit(t6),
                                 Decimal(rand_num1 - rand_num2 + rand_num3))

    t7 = PARSER.parse(f"=({rand_num1}+{rand_num2})/{rand_num3}")
    assert utils.check_dec_equal(evaler.visit(t7),
                                 Decimal((rand_num1 + rand_num2) / rand_num3))

    t8 = PARSER.parse(f"={rand_num1}-({rand_num2}/{rand_num3})")
    assert utils.check_dec_equal(evaler.visit(t8),
                                 Decimal(rand_num1 - rand_num2 / rand_num3))

    t9 = PARSER.parse(f"=({rand_num1}-{rand_num2})/{rand_num3}")
    assert utils.check_dec_equal(evaler.visit(t9),
                                 Decimal((rand_num1 - rand_num2) / rand_num3))


def test_div0_form():
    """
    Tests that the #DIV/0! error is thrown if the denominator of some expression
    is a formula which evaluates to 0
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")

    # Simple div0 with references
    wb.set_cell_contents("Sheet1", "A1", "=1")
    wb.set_cell_contents("Sheet1", "A2", "=0")
    wb.set_cell_contents("Sheet1", "A3", "=$A$1/sHeEt1!$a$2")
    assert isinstance(wb.get_cell_value("Sheet1", "A3"), CellError)
    assert (wb.get_cell_value("Sheet1", "A3").get_type() ==
            CellErrorType.DIVIDE_BY_ZERO)

    # Div0 with simple arithmetic expression
    wb.set_cell_contents("Sheet1", "A4", "=1/(2-2)")
    assert isinstance(wb.get_cell_value("Sheet1", "A4"), CellError)
    assert (wb.get_cell_value("Sheet1", "A4").get_type() ==
            CellErrorType.DIVIDE_BY_ZERO)

    # Div0 with arithmetic expression with references
    wb.set_cell_contents("Sheet1", "A5", "=1/($a$1-$A$1)")
    assert isinstance(wb.get_cell_value("SheET1", "a5"), CellError)
    assert (wb.get_cell_value("Sheet1", "A5").get_type() ==
            CellErrorType.DIVIDE_BY_ZERO)

def test_err_paren():
    """
    Tests that setting a cell to an error literal wrapped in parentheses results 
    in the correct error value.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")

    # Parse error
    wb.set_cell_contents("Sheet1", "A1", "=(#ERROR!)")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            CellErrorType.PARSE_ERROR)

    # Circular reference error
    wb.set_cell_contents("Sheet1", "A2", "=(#CIRCREF!)")
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), CellError)
    assert (wb.get_cell_value("Sheet1", "A2").get_type() ==
            CellErrorType.CIRCULAR_REFERENCE)

    # Bad reference error
    wb.set_cell_contents("Sheet1", "A3", "=(#REF!)")
    assert isinstance(wb.get_cell_value("Sheet1", "A3"), CellError)
    assert (wb.get_cell_value("Sheet1", "A3").get_type() ==
            CellErrorType.BAD_REFERENCE)

    # Bad name error
    wb.set_cell_contents("Sheet1", "A4", "=(#NAME?)")
    assert isinstance(wb.get_cell_value("Sheet1", "A4"), CellError)
    assert (wb.get_cell_value("Sheet1", "A4").get_type() ==
            CellErrorType.BAD_NAME)

    # Type error
    wb.set_cell_contents("Sheet1", "A5", "=(#VALUE!)")
    assert isinstance(wb.get_cell_value("Sheet1", "A5"), CellError)
    assert (wb.get_cell_value("Sheet1", "A5").get_type() ==
            CellErrorType.TYPE_ERROR)

    # Divide by zero error
    wb.set_cell_contents("Sheet1", "A6", "=(#DIV/0!)")
    assert isinstance(wb.get_cell_value("Sheet1", "A6"), CellError)
    assert (wb.get_cell_value("Sheet1", "A6").get_type() ==
            CellErrorType.DIVIDE_BY_ZERO)


def test_concat_cell_str():
    """
    Test concatenating a cell and a string with various whitespace
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("ShEEt1", "a1", "Hello")
    wb.set_cell_contents("SheEt1", "A3", '=$a$1&"World"')
    assert wb.get_cell_value("SheeT1", "A3") == "HelloWorld"

    wb.set_cell_contents("Sheet1", "a4", '=\'sHeEt1\'!$A$1&" World"')
    assert wb.get_cell_value("Sheet1", "A4") == "Hello World"

    wb.set_cell_contents("Sheet1", "A5", '=$a$1&"World "')
    assert wb.get_cell_value("SheET1", "a5") == "HelloWorld "

    wb.set_cell_contents("SheET1", "A6", '=sheet1!$a$1&" World "')
    assert wb.get_cell_value("Sheet1", "a6") == "Hello World "

    wb.set_cell_contents("sheet1", "A1", "'    Hello")
    wb.set_cell_contents("sheet1", "a2", '=sheet1!$A$1&"    World"')
    assert wb.get_cell_value("sheet1", "a2") == "    Hello    World"



def test_concat_unset():
    """
    Tests that concatenating an empty cell with a string literal treats the
    empty cell as an empty string.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("ShEEt1", "a1", '=$a$2&"World"')
    assert wb.get_cell_value("Sheet1", "a1") == "World"
    wb.set_cell_contents("Sheet1", "A1", '="World"&ShEEt1!$a$500')
    assert wb.get_cell_value("Sheet1", "A1") == "World"


def test_concat_computation_str():
    """
    Tests concatenating a string literal with a numeric computation
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "a1", "Hello")
    wb.set_cell_contents("ShEEt1", "A2", '=$a$1&" "&(1+1)')
    assert wb.get_cell_value("Sheet1", "A2") == "Hello 2"

    wb.set_cell_contents("SheEt1", "a3", '=ShEEt1!$A$1&" "&(1-1)')
    assert wb.get_cell_value("Sheet1", "A3") == "Hello 0"

    wb.set_cell_contents("Sheet1", "a4", '=$a$1&" "&(1*1)')
    assert wb.get_cell_value("Sheet1", "A4") == "Hello 1"

    wb.set_cell_contents("Sheet1", "A5", '=\'shEET1\'!$a$1&" "&(1/1)')
    assert wb.get_cell_value("Sheet1", "A5") == "Hello 1"

    wb.set_cell_contents("ShEET1", "a6", '=sHeet1!$a$1&" "&(1/2)')
    assert wb.get_cell_value("Sheet1", "A6") == "Hello 0.5"

def test_trail_0_concat():
    """
    Tests that trailing zeros are removed when concatenating a number with a
    string (Including both literal numbers and referenced cells)
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "Hello")
    wb.set_cell_contents("Sheet1", "A2", '=$A$1&" "&1.0')
    assert wb.get_cell_value("Sheet1", "A2") == "Hello 1"

    wb.set_cell_contents("Sheet1", "A3", '=$a$1&" "&1.00')
    assert wb.get_cell_value("Sheet1", "A3") == "Hello 1"

    wb.set_cell_contents("Sheet1", "A4", '=\'shEet1\'!$A$1&" "&1.000')
    assert wb.get_cell_value("Sheet1", "A4") == "Hello 1"

    wb.set_cell_contents("Sheet1", "A5", '=sheet1!$A$1&" "&1.0000')
    assert wb.get_cell_value("Sheet1", "A5") == "Hello 1"


def test_cell_forms():
    """
    Tests a variety of formulas that include multiple operators between only 
    cells.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "1")
    wb.set_cell_contents("Sheet1", "A2", "7")
    wb.set_cell_contents("Sheet1", "A3", "3")
    wb.set_cell_contents("Sheet1", "A4", "4")
    wb.set_cell_contents("Sheet1", "A5", "5")
    wb.set_cell_contents("Sheet1", "A6", "6")
    wb.set_cell_contents("Sheet1", "A7", "=$A$1+$a$2-$A$3+'sHeEt1'!$A$4-sheeT1!$A$5*sheet1!$a$6")
    assert utils.check_dec_equal(wb.get_cell_value("Sheet1", "A7"),
                                 Decimal(1 + 7 - 3 + 4 - 5 * 6))
    wb.set_cell_contents("Sheet1", "A8", "=A1+sheet1!A2-'SHEET1'!A3+A4-a5/a6")
    assert utils.check_dec_equal(wb.get_cell_value("Sheet1", "A8"),
                                 Decimal(1 + 7 - 3 + 4 - 5 / 6))
    wb.set_cell_contents("Sheet1", "A9", "=(A1+a2-'sheet1'!A3+a4-shEEt1!a5)*a6")
    assert utils.check_dec_equal(wb.get_cell_value("Sheet1", "A9"),
                                 Decimal((1 + 7 - 3 + 4 - 5) * 6))
    wb.set_cell_contents("Sheet1", "A10", "=(a1+A2-a3)&(A4-a5*A6)")
    assert wb.get_cell_value("Sheet1", "A10") == str(1+7-3)+ str(4-5*6)


def test_num_cell_forms():
    """
    Tests a variety of formulas that include multiple operators between cells and 
    numeric literals.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "1")
    wb.set_cell_contents("Sheet1", "A2", "12")
    wb.set_cell_contents("Sheet1", "A3", "3")
    wb.set_cell_contents("Sheet1", "A4", "4")
    wb.set_cell_contents("Sheet1", "A5", "5")
    wb.set_cell_contents("Sheet1", "A6", "6")
    wb.set_cell_contents("Sheet1", "A7", "=$A$1+12-3+4-5*$a$6")
    assert utils.check_dec_equal(wb.get_cell_value("Sheet1", "A7"),
                                 Decimal(1 + 12 - 3 + 4 - 5 * 6))
    wb.set_cell_contents("Sheet1", "A8", "=$A$1+12-3+4-5/'sHeEt1'!$a$6")
    assert utils.check_dec_equal(wb.get_cell_value("Sheet1", "A8"),
                                 Decimal(1 + 12 - 3 + 4 - 5 / 6))
    wb.set_cell_contents("Sheet1", "A9", "=(shEeT1!A1+12-3+4-5)*6")
    assert utils.check_dec_equal(wb.get_cell_value("Sheet1", "A9"),
                                 Decimal((1 + 12 - 3 + 4 - 5) * 6))
    wb.set_cell_contents("Sheet1", "A10", "=($a$1+12-3)&(4-5*$A$6)")
    assert wb.get_cell_value("Sheet1", "A10") == str(1+12-3)+ str(4-5*6)



def test_num_forms():
    """
    Tests a variety of formulas that include multiple operators between numeric
    literals.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "1")
    wb.set_cell_contents("Sheet1", "A2", "13")
    wb.set_cell_contents("Sheet1", "A3", "3")
    wb.set_cell_contents("Sheet1", "A4", "4")
    wb.set_cell_contents("Sheet1", "A5", "5")
    wb.set_cell_contents("Sheet1", "A6", "6")
    wb.set_cell_contents("Sheet1", "A7", "=1+13-3+4-5*6")
    assert utils.check_dec_equal(wb.get_cell_value("Sheet1", "A7"),
                                 Decimal(1 + 13 - 3 + 4 - 5 * 6))
    wb.set_cell_contents("Sheet1", "A8", "=1+13-3+4-5/6")
    assert utils.check_dec_equal(wb.get_cell_value("Sheet1", "A8"),
                                 Decimal(1 + 13 - 3 + 4 - 5 / 6))
    wb.set_cell_contents("Sheet1", "A9", "=(1+13-3+4-5)*6")
    assert utils.check_dec_equal(wb.get_cell_value("Sheet1", "A9"),
                                 Decimal((1 + 13 - 3 + 4 - 5) * 6))
    wb.set_cell_contents("Sheet1", "A10", "=(1+13-3)&(4-5*6)")
    assert wb.get_cell_value("Sheet1", "A10") == str(1+13-3)+ str(4-5*6)

def test_not_numeric():
    """
    Ensure that a non-numeric value cannot be automatically converted to a number
    and triggers an error
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "Hello")
    wb.set_cell_contents("Sheet1", "A2", "=$A$1+1")
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), CellError)
    assert (wb.get_cell_value("Sheet1", "A2").get_type() ==
            CellErrorType.TYPE_ERROR)

    wb.set_cell_contents("Sheet1", "A3", "World")
    wb.set_cell_contents("Sheet1", "A4", "=$A$1+$A$3")
    assert isinstance(wb.get_cell_value("Sheet1", "A4"), CellError)
    assert (wb.get_cell_value("Sheet1", "A4").get_type() ==
            CellErrorType.TYPE_ERROR)

    wb.set_cell_contents("Sheet1", "A5", "1")
    wb.set_cell_contents("Sheet1", "A6", "=$A$5+$A$3")
    assert isinstance(wb.get_cell_value("Sheet1", "A6"), CellError)
    assert (wb.get_cell_value("Sheet1", "A6").get_type() ==
            CellErrorType.TYPE_ERROR)


def test_concat_err():
    """
    Ensure that if a string literal is input into a formula, it cannot be 
    automatically converted into a string in a concatenation formula.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "#ERROR!")
    wb.set_cell_contents("Sheet1", "A2", "=A1&Hello")
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), CellError)
    assert (wb.get_cell_value("Sheet1", "A2").get_type() ==
            CellErrorType.PARSE_ERROR)


def test_strip_zeros():
    """
    Ensure that trailing zeros are removed from a number when it is generated as
    a result of an arithmetic operation.
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "1.0")
    wb.set_cell_contents("Sheet1", "A2", "2.0")
    wb.set_cell_contents("Sheet1", "A3", "0.300")
    wb.set_cell_contents("Sheet1", "A4", "0.700")
    wb.set_cell_contents("Sheet1", "A5", "=$A$3+$a$4")
    wb.set_cell_contents("Sheet1", "A6", "=0.50*4.0")
    wb.set_cell_contents("sheet1", "a7", "=(1.0)")
    wb.set_cell_contents("sheet1", "a8", "=(1.5+1.5)")
    wb.set_cell_contents("sHeEt1", "A9", "=-1.0")
    wb.set_cell_contents("sHeEt1", "A10", "=-(1.5*2.0)")
    assert str(wb.get_cell_value("Sheet1", "A1")) == "1"
    assert str(wb.get_cell_value("Sheet1", "A2")) == "2"
    assert str(wb.get_cell_value("Sheet1", "A5")) == "1"
    assert str(wb.get_cell_value("Sheet1", "A6")) == "2"
    assert str(wb.get_cell_value("Sheet1", "A7")) == "1"
    assert str(wb.get_cell_value("Sheet1", "A8")) == "3"
    assert str(wb.get_cell_value("Sheet1", "A9")) == "-1"
    assert str(wb.get_cell_value("Sheet1", "A10")) == "-3"


def test_mul_div_unset():
    """
    Tests multiplication and division with an unset cell. (Should become 0).
    """
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("sheet1", "a1", "=$a$2*2")
    assert wb.get_cell_value("Sheet1", "a1") == 0
    wb.set_cell_contents("Sheet1", "a3", "=$a$4/2")
    assert wb.get_cell_value("Sheet1", "A3") == 0
    wb.set_cell_contents("Sheet1", "A5", "=2/$A$6")
    assert isinstance(wb.get_cell_value("Sheet1", "A5"), CellError)
    assert (wb.get_cell_value("Sheet1", "A5").get_type() ==
            CellErrorType.DIVIDE_BY_ZERO)


def test_bool_ref():
    """
    Tests that evaluating a formula which consists of only a single reference to 
    a boolean typed cell correctly returns the value of the cell. Ensures case 
    insensitivity.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("ShEEt1", "a1", "TRUE")
    wb.set_cell_contents("Sheet1", "A2", "FALSE")
    wb.set_cell_contents("SheEt1", "A3", "=A1")
    wb.set_cell_contents("SheeT1", "a4", "=a2")
    assert wb.get_cell_value("ShEeT1", "a3") is True
    assert wb.get_cell_value("sheet1", "A4") is False

    wb.set_cell_contents("sheet1", "A1", "tRuE")
    wb.set_cell_contents("Sheet1", "A2", "fAlSe")
    assert wb.get_cell_value("Sheet1", "A3") is True
    assert wb.get_cell_value("Sheet1", "A4") is False


def test_bool_lit():
    """
    Ensures that a boolean literal in a cell formula is evaluated correctly in 
    isolation.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=TRUE")
    wb.set_cell_contents("Sheet1", "A2", "=FALSE")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), bool)
    assert isinstance(wb.get_cell_value("Sheet1", "A2"), bool)
    assert wb.get_cell_value("Sheet1", "A1") is True
    assert wb.get_cell_value("Sheet1", "A2") is False

    # Ensure case insensitivity
    wb.set_cell_contents("Sheet1", "A3", "=tRuE")
    wb.set_cell_contents("Sheet1", "A4", "=fAlSe")
    assert isinstance(wb.get_cell_value("Sheet1", "A3"), bool)
    assert isinstance(wb.get_cell_value("Sheet1", "A4"), bool)
    assert wb.get_cell_value("Sheet1", "A3") is True
    assert wb.get_cell_value("Sheet1", "A4") is False


def test_str_bool_conversion():
    """
    Tests that booleans literals used in string contexts are converted to strings 
    correctly.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=TruE&\"Hello\"")
    wb.set_cell_contents("Sheet1", "A2", "=FaLSe&\"World\"")
    assert wb.get_cell_value("Sheet1", "A1") == "TRUEHello"
    assert wb.get_cell_value("Sheet1", "A2") == "FALSEWorld"

    wb.set_cell_contents("Sheet1", "A3", "=\"Hello\"&TRuE")
    wb.set_cell_contents("Sheet1", "A4", "=\"World\"&fALSE")
    assert wb.get_cell_value("Sheet1", "A3") == "HelloTRUE"
    assert wb.get_cell_value("Sheet1", "A4") == "WorldFALSE"

    wb.set_cell_contents("Sheet1", "A5", "=TRUE&FALSE")
    wb.set_cell_contents("Sheet1", "A6", "=FALSE&TRUE")
    assert wb.get_cell_value("Sheet1", "A5") == "TRUEFALSE"
    assert wb.get_cell_value("Sheet1", "A6") == "FALSETRUE"


def test_str_lit_bool():
    """
    Ensures that a boolean literal encapsulated within a string literal is not 
    evaluated as a boolean.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=\"TRUE\"")
    wb.set_cell_contents("Sheet1", "A2", "=\"FALSE\"")
    assert wb.get_cell_value("Sheet1", "A1") == "TRUE"
    assert wb.get_cell_value("Sheet1", "A2") == "FALSE"
    assert not isinstance(wb.get_cell_value("Sheet1", "A1"), bool)

    wb.set_cell_contents("Sheet1", "A3", "=\"tRuE\"")
    wb.set_cell_contents("Sheet1", "A4", "=\"fAlSe\"")
    assert wb.get_cell_value("Sheet1", "A3") == "tRuE"
    assert wb.get_cell_value("Sheet1", "A4") == "fAlSe"


def test_bool_num_conversion():
    """
    Tests that boolean literals used in numeric contexts are converted to numbers
    correctly.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=TRUE+1")
    wb.set_cell_contents("Sheet1", "A2", "=FALSE+1")
    assert wb.get_cell_value("SheeT1", "A1") == 2
    assert wb.get_cell_value("ShEEt1", "A2") == 1

    wb.set_cell_contents("Sheet1", "A3", "=1+TRUE")
    wb.set_cell_contents("Sheet1", "a4", "=1+FALSE")
    assert wb.get_cell_value("Sheet1", "A3") == 2
    assert wb.get_cell_value("ShEEt1", "A4") == 1

    wb.set_cell_contents("Sheet1", "A5", "=TRue+FALSE")
    wb.set_cell_contents("Sheet1", "A6", "=FALSE+TRUE")
    assert wb.get_cell_value("Sheet1", "A5") == 1
    assert wb.get_cell_value("Sheet1", "A6") == 1

    wb.set_cell_contents("sheet1", "a1", "=tRuE*1")
    wb.set_cell_contents("shEEt1", "a2", "=fAlSe*1")
    assert wb.get_cell_value("ShEet1", "a1") == 1
    assert wb.get_cell_value("SheeT1", "A2") == 0

    wb.set_cell_contents("SheET1", "a3", "=1/tRuE")
    wb.set_cell_contents("Sheet1", "A4", "=1/fAlSe")
    assert wb.get_cell_value("Sheet1", "A3") == 1
    assert isinstance(wb.get_cell_value("sheet1", "a4"), CellError)
    assert (wb.get_cell_value("Sheet1", "A4").get_type() ==
            CellErrorType.DIVIDE_BY_ZERO)


def test_bool_ref_num_conversion():
    """
    Ensure that a ref to a boolean valued cell used in a numeric context is
    converted to a number correctly.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "TRUE")
    wb.set_cell_contents("Sheet1", "A2", "FALSE")
    wb.set_cell_contents("Sheet1", "A3", "=A1+1")
    wb.set_cell_contents("Sheet1", "A4", "=A2+1")
    assert wb.get_cell_value("Sheet1", "A3") == 2
    assert wb.get_cell_value("Sheet1", "A4") == 1

    wb.set_cell_contents("Sheet1", "A5", "=1+A1")
    wb.set_cell_contents("Sheet1", "A6", "=1+A2")
    assert wb.get_cell_value("Sheet1", "A5") == 2
    assert wb.get_cell_value("Sheet1", "A6") == 1

    wb.set_cell_contents("Sheet1", "A7", "=a1+FalSE")
    wb.set_cell_contents("ShEEt1", "a8", "=A2+TRuE")
    assert wb.get_cell_value("Sheet1", "A7") == 1
    assert wb.get_cell_value("Sheet1", "A8") == 1

    wb.set_cell_contents("Sheet1", "A9", "=sheet1!A1*1")
    wb.set_cell_contents("Sheet1", "A10", "=ShEeT1!a2*1")
    assert wb.get_cell_value("Sheet1", "A9") == 1
    assert wb.get_cell_value("Sheet1", "A10") == 0

    wb.set_cell_contents("Sheet1", "A11", "=1/a1")
    wb.set_cell_contents("Sheet1", "A12", "=1/'sHeeT1'!A2")
    assert wb.get_cell_value("Sheet1", "A11") == 1
    assert isinstance(wb.get_cell_value("Sheet1", "A12"), CellError)
    assert (wb.get_cell_value("Sheet1", "A12").get_type() ==
            CellErrorType.DIVIDE_BY_ZERO)


def test_bool_ref_str_conversion():
    """
    Ensure that a ref to a boolean valued cell used in a string context is
    converted to a string correctly.
    """
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "true")
    wb.set_cell_contents("Sheet1", "A2", "FAlse")
    wb.set_cell_contents("Sheet1", "A3", "=A1&\"Hello\"")
    wb.set_cell_contents("Sheet1", "A4", "=A2&\"World\"")
    assert wb.get_cell_value("Sheet1", "A3") == "TRUEHello"
    assert wb.get_cell_value("Sheet1", "A4") == "FALSEWorld"

    wb.set_cell_contents("Sheet1", "A5", "=\"Hello\"&A1")
    wb.set_cell_contents("Sheet1", "A6", "=\"World\"&A2")
    assert wb.get_cell_value("Sheet1", "A5") == "HelloTRUE"
    assert wb.get_cell_value("Sheet1", "A6") == "WorldFALSE"

    wb.set_cell_contents("Sheet1", "A7", "=A1&FaLsE")
    wb.set_cell_contents("Sheet1", "A8", "=A2&TRue")
    assert wb.get_cell_value("Sheet1", "A7") == "TRUEFALSE"
    assert wb.get_cell_value("Sheet1", "A8") == "FALSETRUE"

    wb.set_cell_contents("Sheet1", "A9", "=sheet1!A1&\"Hello\"")
    wb.set_cell_contents("Sheet1", "A10", "=ShEeT1!a2&\"World\"")
    assert wb.get_cell_value("Sheet1", "A9") == "TRUEHello"
    assert wb.get_cell_value("Sheet1", "A10") == "FALSEWorld"


def test_str_bool_conv():
    """
    Tests that strings correctly convert to booleans when implicitly converted
    by the conversion function.
    """
    false_test_str = ["false", "FALSE", "FaLsE"]
    true_test_str = ["true", "TRUE", "TRuE"]
    err_test_str = ["hello", "world", "123", "1.0", "0.0", "1", "0", "1.5", "0.5"]
    for s in false_test_str:
        assert Evaluator.check_bool(s) is False
    for s in true_test_str:
        assert Evaluator.check_bool(s) is True
    for s in err_test_str:
        val = Evaluator.check_bool(s)
        assert isinstance(val, CellError)
        assert val.get_type() == CellErrorType.TYPE_ERROR


def test_num_bool_conv():
    """
    Tests that nums correctly convert to bools when implicitly converted
    by the conversion function.
    """
    false_test_num = [Decimal(0), Decimal(0.0)]
    true_test_num = [Decimal(1), Decimal(0.5), Decimal(100), Decimal(-1), Decimal(-0.5)]
    for n in false_test_num:
        assert Evaluator.check_bool(n) is False
    for n in true_test_num:
        assert Evaluator.check_bool(n) is True


utils.run_all(__name__)
