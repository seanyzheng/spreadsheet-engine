"""
Tests for correct behavior when mutating a cell. Cells may be mutated in two
ways, either the content changes, or the cell is a formula which gets evaluated 
at the spreadsheet level changing the value. These tests verify that the cell 
value may not be mutated for non-formula cells, that the cell content is parsed
correctly when mutated after initialization, and (TODO:)that the cell value is set 
correctly when the cell is a formula that gets reevaluated.
"""

# import testing packages
import pytest
import test_utils as utils

# import modules to be tested
from sheets import cell


def test_rand_mutate_str():
    """
    Tests that a string cell may be mutated correctly.
    """
    tst_cell, _ = utils.get_random_cell(cell.CellType.STRING)
    new_str = utils.generate_random_string()
    tst_cell.set_content(new_str)
    assert tst_cell.get_content() == new_str
    assert tst_cell.get_value() == new_str
    assert tst_cell.get_type() == cell.CellType.STRING


def test_rand_mutate_num():
    """
    Tests that a number cell may be mutated correctly.
    """
    tst_cell, _ = utils.get_random_cell(cell.CellType.NUMBER)
    new_num = utils.generate_random_number()
    tst_cell.set_content(str(new_num))
    assert tst_cell.get_content() == str(new_num)
    assert utils.check_dec_equal(tst_cell.get_value(), new_num)
    assert tst_cell.get_type() == cell.CellType.NUMBER


def test_rand_change_type():
    """
    Tests that a cell's type is changed correctly when the content is mutated.
    """
    tst_cell, _ = utils.get_random_cell(cell.CellType.STRING)
    new_num = utils.generate_random_number()
    tst_cell.set_content(str(new_num))
    assert tst_cell.get_content() == str(new_num)
    assert utils.check_dec_equal(tst_cell.get_value(), new_num)
    assert tst_cell.get_type() == cell.CellType.NUMBER


def test_rand_mutate_val_non_formula():
    """
    Tests that the value of a non-formula cell may not be mutated.
    """
    tst_cell, _ = utils.get_random_cell(cell.CellType.STRING)
    with pytest.raises(TypeError):
        tst_cell.set_value("test")
    tst_cell, _ = utils.get_random_cell(cell.CellType.NUMBER)
    with pytest.raises(TypeError):
        tst_cell.set_value(1)

# Test mutation of a formula cell by formula eval and by content change once
# implemented

utils.run_all(__name__)
