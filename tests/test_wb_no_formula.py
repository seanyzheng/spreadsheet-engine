"""
This file holds tests for the Workbook implementation without any formula
evaluation. The Workbook is a container for Spreadsheet objects which must be 
able to add, remove, and edit spreadhseets in a case-insensitive manner, while 
also remembering the display casing of the sheet name.
"""

# import testing packages
import random as rand
from decimal import Decimal
import pytest
import test_utils as utils

# import modules to be tested
from sheets import workbook


def test_rand_new_sheet_return():
    """
    Tests that the return value of new)sheet is the correct sheet number and name
    """
    tst_wb = workbook.Workbook()
    for i in range(0, 100):
        r_name = utils.generate_random_string()
        num, name = tst_wb.new_sheet(r_name)
        assert num == i
        assert name == r_name

    tst_wb.del_sheet(name)
    r_name = utils.generate_random_string()
    num, name = tst_wb.new_sheet(r_name)
    assert num == 99
    assert name == r_name


def test_rand_new_sheet():
    """
    Tests that a sheet may be added to the workbook. Ensures that a sheet with 
    the same name but different casing may not be created.
    """
    tst_wb = workbook.Workbook()
    assert tst_wb.num_sheets() == 0
    sheet_name = utils.generate_random_string()
    tst_wb.new_sheet(sheet_name)
    assert tst_wb.num_sheets() == 1
    assert sheet_name in tst_wb.list_sheets()
    if not sheet_name.isupper():
        with pytest.raises(ValueError):
            tst_wb.new_sheet(sheet_name.upper())
        assert tst_wb.num_sheets() == 1
    sheet_2 = utils.generate_random_string()
    tst_wb.new_sheet(sheet_2)
    assert tst_wb.num_sheets() == 2
    assert tst_wb.list_sheets() == [sheet_name, sheet_2]


def test_rand_del_sheet():
    """
    Tests that a sheet may be deleted from the workbook. Ensures that a sheet 
    with the same name but different casing may be deleted. Checks that 
    deleting a sheet that does not exist throws an error.
    """
    tst_wb = workbook.Workbook()
    assert tst_wb.num_sheets() == 0
    sheet_name = utils.generate_random_string()
    tst_wb.new_sheet(sheet_name)
    assert tst_wb.num_sheets() == 1
    tst_wb.del_sheet(sheet_name)
    assert tst_wb.num_sheets() == 0
    sheet_2 = utils.generate_random_string()
    tst_wb.new_sheet(sheet_2)
    assert tst_wb.num_sheets() == 1
    tst_wb.del_sheet(sheet_2.upper())
    assert tst_wb.num_sheets() == 0
    with pytest.raises(KeyError):
        tst_wb.del_sheet(sheet_name)
    assert tst_wb.num_sheets() == 0


def test_new_sheet_no_name():
    """
    Tests that a sheet may be added to the workbook without a name. Ensures that 
    a unique name is generated following the appropriate casing for any sheet.
    """
    tst_wb = workbook.Workbook()
    assert tst_wb.num_sheets() == 0
    sht_names = []
    for i in range(1, 10):
        tst_wb.new_sheet()
        assert tst_wb.num_sheets() == i
        sht_names.append(f"Sheet{i}")
    assert tst_wb.num_sheets() == 9
    assert tst_wb.list_sheets() == sht_names
    tst_wb.del_sheet("Sheet1")
    assert tst_wb.num_sheets() == 8
    assert tst_wb.list_sheets() == sht_names[1:]
    tst_wb.new_sheet()
    assert tst_wb.num_sheets() == 9
    sht_names = sht_names[1:]
    sht_names.append("Sheet1")
    assert tst_wb.list_sheets() == sht_names


def test_rand_new_sheet_invalid_name():
    """
    Tests that an invalid sheet name throws an error.
    """
    tst_wb = workbook.Workbook()
    assert tst_wb.num_sheets() == 0
    with pytest.raises(ValueError):
        rand_spaces = rand.randint(1, 100)
        tst_wb.new_sheet(" " * rand_spaces)
    assert tst_wb.num_sheets() == 0
    with pytest.raises(ValueError):
        rand_spaces = rand.randint(1, 100)
        tst_wb.new_sheet(" " * rand_spaces + "a")
    assert tst_wb.num_sheets() == 0
    with pytest.raises(ValueError):
        rand_spaces = rand.randint(1, 100)
        tst_wb.new_sheet("a" + " " * rand_spaces)
    assert tst_wb.num_sheets() == 0
    with pytest.raises(ValueError):
        tst_wb.new_sheet("'")
    assert tst_wb.num_sheets() == 0
    with pytest.raises(ValueError):
        tst_wb.new_sheet('"')
    assert tst_wb.num_sheets() == 0


def test_rand_get_value():
    """
    Tests that a workbook returns the value of the specified cell on the specified sheet.
    Tests the locations with upper and lower case letters.
    """
    tst_wb = workbook.Workbook()
    tst_wb.new_sheet("Sheet1")
    location = utils.rand_loc()
    tst_wb.set_cell_contents("Sheet1", location.upper(), "1")
    assert tst_wb.get_cell_value("Sheet1", location.upper()) == Decimal("1")
    tst_wb.set_cell_contents("Sheet1", location.lower(), "test")
    assert tst_wb.get_cell_value("Sheet1", location.lower()) == "test"
    tst_wb.set_cell_contents("Sheet1", location.upper(), "    50")
    assert tst_wb.get_cell_value("Sheet1", location.upper()) == Decimal("50")
    tst_wb.set_cell_contents("Sheet1", location.lower(), "    test")
    assert tst_wb.get_cell_value("Sheet1", location.lower()) == "test"
    tst_wb.set_cell_contents("Sheet1", location.upper(), "1    ")
    assert tst_wb.get_cell_value("Sheet1", location.upper()) == Decimal("1")
    tst_wb.set_cell_contents("Sheet1", location.lower(), "test    ")
    assert tst_wb.get_cell_value("Sheet1", location.lower()) == "test"
    tst_wb.set_cell_contents("Sheet1", location.upper(), "    50   ")
    assert tst_wb.get_cell_value("Sheet1", location.upper()) == Decimal("50")
    tst_wb.set_cell_contents("Sheet1", location.lower(), "    test    ")
    assert tst_wb.get_cell_value("Sheet1", location.lower()) == "test"
    tst_wb.set_cell_contents("Sheet1", location.lower(), "")
    assert tst_wb.get_cell_value("Sheet1", location.lower()) is None


def test_rand_set_contents():
    """
    Tests that a workbook can appropriately set the contents of a cell within 
    one of the spreadsheets that it owns.
    """
    tst_wb = workbook.Workbook()
    tst_wb.new_sheet("Sheet1")
    location = utils.rand_loc()
    assert tst_wb.get_cell_contents("Sheet1", location) is None
    tst_wb.set_cell_contents("Sheet1", location, "test")
    assert tst_wb.get_cell_contents("Sheet1", location) == "test"
    tst_wb.set_cell_contents("Sheet1", location, "    ")
    assert tst_wb.get_cell_contents("Sheet1", location) is None
    tst_wb.set_cell_contents("Sheet1", location, None)
    assert tst_wb.get_cell_contents("Sheet1", location) is None
    tst_wb.set_cell_contents("Sheet1", location, "  05")
    assert tst_wb.get_cell_contents("Sheet1", location) == "05"
    tst_wb.set_cell_contents("Sheet1", location, " " * rand.randint(0, 10))
    assert tst_wb.get_cell_contents("Sheet1", location) is None


def test_get_sheet_extent():
    """
    Tests that the workbook can acurately report the extent of sheets that it
    owns with multiple sheets, adding and deleting of cells
    """
    tst_wb = workbook.Workbook()
    with pytest.raises(KeyError):
        tst_wb.get_sheet_extent("Sheet1")
    tst_wb.new_sheet("Sheet1")
    assert tst_wb.get_sheet_extent("Sheet1") == (0, 0)
    tst_wb.set_cell_contents("Sheet1", "A1", "test")
    assert tst_wb.get_sheet_extent("SHEET1") == (1, 1)
    tst_wb.set_cell_contents("Sheet1", "A2", "test")
    assert tst_wb.get_sheet_extent("sheet1") == (1, 2)
    tst_wb.set_cell_contents("Sheet1", "B2", "test")
    assert tst_wb.get_sheet_extent("Sheet1") == (2, 2)
    tst_wb.new_sheet("Sheet2")
    assert tst_wb.get_sheet_extent("SHEET2") == (0, 0)
    tst_wb.set_cell_contents("Sheet2", "A1", "test")
    assert tst_wb.get_sheet_extent("sheet2") == (1, 1)
    tst_wb.set_cell_contents("Sheet2", "A2", "test")
    assert tst_wb.get_sheet_extent("Sheet2") == (1, 2)
    tst_wb.set_cell_contents("Sheet2", "B2", "test")
    assert tst_wb.get_sheet_extent("Sheet2") == (2, 2)
    assert tst_wb.get_sheet_extent("Sheet1") == (2, 2)
    tst_wb.set_cell_contents("Sheet1", "A1", "")
    assert tst_wb.get_sheet_extent("Sheet1") == (2, 2)
    tst_wb.set_cell_contents("Sheet1", "A2", "")
    assert tst_wb.get_sheet_extent("Sheet1") == (2, 2)
    tst_wb.set_cell_contents("Sheet1", "B2", "")
    assert tst_wb.get_sheet_extent("Sheet1") == (0, 0)


def test__new_sht_err():
    """
    Tests that creating a new sheet in a workbook with the empty string as its
    name throws an error.
    """
    wb = workbook.Workbook()
    with pytest.raises(ValueError):
        wb.new_sheet("")


def test_sheet_names():
    """
    Ensures that sheet names are checked to ensure they don't contain illegal 
    characters, and ensures that formulas parsed with quoted sheet names
    evaluate correctly.
    """
    wb = workbook.Workbook()
    wb.new_sheet()

    # Ensure that sheet names can contain allowed symbols
    for symbol in ".?!,:;@#$%^&*()-_":
        wb.new_sheet(f"Sheet{symbol}")
    # Ensure that sheet names cannot contain illegal symbols
    for symbol in ["'", '"']:
        with pytest.raises(ValueError):
            wb.new_sheet(f"Sheet{symbol}")

    # Ensure that formulas with quoted sheet names evaluate correctly
    wb.new_sheet("Sheet2")
    wb.set_cell_contents("Sheet1", "A1", "1")
    wb.set_cell_contents("Sheet2", "A1", "2")
    wb.set_cell_contents("Sheet1", "A2", "='Sheet2'!A1")
    wb.set_cell_contents("Sheet1", "A3", "=Sheet2!A1")
    assert wb.get_cell_value("Sheet1", "A2") == Decimal("2")
    assert wb.get_cell_value("Sheet1", "A3") == Decimal("2")


def test_del_nonexistant_sheet():
    """
    Tests that deleting a non-existant sheet throws an error.
    """
    wb = workbook.Workbook()
    with pytest.raises(KeyError):
        wb.del_sheet("Sheet1")


utils.run_all(__name__)
