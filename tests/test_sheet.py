"""
This file holds tests for the Spreadsheet class implemented in spreadsheet.py. 
The spreadsheet is a fairly simple container for cells which needs to be able 
to create, query, mutate, and delete the cells that it holds. The spreadsheet 
should never be able to hold cells at invalid locations or mutate the values of 
cells which are not formulas.
"""

# import testing packages
import random as rand
import pytest
import test_utils as utils

# import modules to be tested
from sheets import cell
import sheets.spreadsheet as sht


def test_rand_str_set_get():
    """
    Tests that a string cell may be set and retrieved correctly.
    """
    tst_sheet = sht.Spreadsheet(utils.generate_random_string())
    tst_cell, tst_str = utils.get_random_cell(cell.CellType.STRING)
    loc = utils.rand_loc()
    assert tst_sheet[loc] is None
    assert tst_sheet.get_cell_contents(loc) is None
    tst_sheet.set_cell_contents(loc, tst_str)
    assert tst_sheet.get_cell_contents(loc) == tst_str
    assert tst_sheet[loc] == tst_cell.get_value() == tst_str
    assert tst_sheet.get_cell_type(loc) == tst_cell.get_type()


def test_rand_num_set_get():
    """
    Tests that a number cell may be set and retrieved correctly.
    """
    tst_sheet = sht.Spreadsheet(utils.generate_random_string())
    tst_cell, tst_num = utils.get_random_cell(cell.CellType.NUMBER)
    loc = utils.rand_loc()
    assert tst_sheet[loc] is None
    assert tst_sheet.get_cell_contents(loc) is None
    tst_sheet.set_cell_contents(loc, str(tst_num))
    assert tst_sheet.get_cell_contents(loc) == str(tst_num)
    assert tst_sheet[loc] == tst_cell.get_value()
    assert tst_sheet.get_cell_type(loc) == tst_cell.get_type()


def test_rand_cell_removal():
    """
    Tests that a cell is removed when its contents are set to empty or
    whitespace.
    """
    tst_sheet = sht.Spreadsheet(utils.generate_random_string())
    tst_cell, tst_str = utils.get_random_cell(cell.CellType.STRING)
    loc = utils.rand_loc()
    tst_sheet.set_cell_contents(loc, tst_str)
    assert tst_sheet[loc] == tst_cell.get_value() == tst_str
    space_num = rand.randint(0, 100)
    tst_sheet.set_cell_contents(loc, " " * space_num)
    assert tst_sheet[loc] is None
    assert tst_sheet.get_cell_contents(loc) is None
    assert tst_sheet.get_cell_type(loc) is None


def test_invalid_loc():
    """
    Tests that an invalid location throws an error.
    """
    tst_sheet = sht.Spreadsheet(utils.generate_random_string())
    loc = utils.rand_loc()
    # Test the boundaries explicitly
    tst_sheet.set_cell_contents("A1", "test")
    tst_sheet.set_cell_contents("ZZZZ9999", "test")
    with pytest.raises(ValueError):
        tst_sheet["A0"].get_content()
    with pytest.raises(ValueError):
        tst_sheet["ZZZZ10000"].get_content()
    with pytest.raises(ValueError):
        tst_sheet["ZZZZA1"].get_content()
    # Test random locations
    assert tst_sheet[loc] is None
    with pytest.raises(ValueError):
        tst_sheet.set_cell_contents(loc + "A", "test")
    with pytest.raises(ValueError):
        tst_sheet.get_cell_contents(loc + "A")
    with pytest.raises(ValueError):
        tst_sheet.get_cell_type(loc + "A")


def test_mutate_val():
    """
    Tests that the value of a cell may not be mutated for non-formula types
    """
    tst_sheet = sht.Spreadsheet(utils.generate_random_string())
    loc = utils.rand_loc()
    tst_sheet.set_cell_contents(loc, "test")
    with pytest.raises(TypeError):
        tst_sheet.set_cell_value(loc, "test")
    tst_sheet.set_cell_contents(loc, str(utils.generate_random_number()))
    with pytest.raises(TypeError):
        tst_sheet.set_cell_value(loc, 1)


def test_cell_extent():
    """
    Tests that the extent of the spreadsheet is correct.
    """
    tst_sheet = sht.Spreadsheet(utils.generate_random_string())
    assert tst_sheet.get_extent() == (0, 0)
    tst_sheet.set_cell_contents("A1", "test")
    assert tst_sheet.get_extent() == (1, 1)
    tst_sheet.set_cell_contents("B2", "test")
    assert tst_sheet.get_extent() == (2, 2)
    tst_sheet.set_cell_contents("A1", "")
    assert tst_sheet.get_extent() == (2, 2)
    tst_sheet.set_cell_contents("B2", "")
    assert tst_sheet.get_extent() == (0, 0)


def test_get_cell_invalid():
    """
    Ensure that calling get_cell on an invalid location throws an error.
    """
    tst_sheet = sht.Spreadsheet(utils.generate_random_string())
    with pytest.raises(ValueError):
        tst_sheet.get_cell("A0")
    with pytest.raises(ValueError):
        tst_sheet.get_cell("ZZZZ10000")
    with pytest.raises(ValueError):
        tst_sheet.get_cell("ZZZZA1")


utils.run_all(__name__)
