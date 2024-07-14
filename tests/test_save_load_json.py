"""
Tests for various saving and loading workbook to and from JSON cases
"""
import json
from io import StringIO
import pytest
import sheets

def test_save_load_workbook():
    """
    Test that saving a valid workbook then loading from that JSON works
    """
    # Create a workbook and add some data
    wb = sheets.Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "Hello")

    # Save the workbook to a string
    file = StringIO()
    wb.save_workbook(file)

    # Load the workbook from the string
    file.seek(0)
    wb2 = sheets.Workbook.load_workbook(file)

    # Check that the loaded workbook has the same data
    assert wb2.get_cell_contents("Sheet1", "A1") == "Hello"

def test_load_workbook_invalid_json():
    """
    Test that loading invalid JSON raises a JSONDecodeError
    """
    file = StringIO("{")
    with pytest.raises(json.JSONDecodeError):
        sheets.Workbook.load_workbook(file)

def test_load_workbook_missing_key():
    """
    Test that loading JSON with a missing key raises a KeyError
    """
    file = StringIO('{"sheets": [{"name": "Sheet1"}]}')
    with pytest.raises(KeyError):
        sheets.Workbook.load_workbook(file)

def test_load_workbook_extra_key():
    """    
    Test that loading JSON with too many keys raises a KeyError
    """
    file = StringIO('{"sheets": [{"name": "Sheet1", "cell-contents": {}, "bad": "bad"}]}')
    with pytest.raises(KeyError):
        sheets.Workbook.load_workbook(file)

def test_load_workbook_wrong_key():
    """
    Test that loading JSON with wrong key name raises a KeyError
    """
    file = StringIO('{"sheets": [{"namsssss": "Sheet1", "cell-contents": {}}]}')
    with pytest.raises(KeyError):
        sheets.Workbook.load_workbook(file)

def test_load_workbook_wrong_type():
    """
    Test that loading JSON with a value of the wrong type raises a TypeError
    """
    file = StringIO('{"sheets": "urmom"}')
    with pytest.raises(TypeError):
        sheets.Workbook.load_workbook(file)

    file = StringIO('{"sheets": [{"name": "Sheet1", "cell-contents": "moomoo"}]}')
    with pytest.raises(TypeError):
        sheets.Workbook.load_workbook(file)
