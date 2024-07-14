"""
Tests the renaming of sheets in the workbook and the propagation of that name 
change throughout the formulas in the entire workbook.
"""

import pytest
from sheets import Workbook, CellError, CellErrorType


def test_simple_rename():
    """
    Sanity check that a simple rename operation works as expected.
    """
    # Create a workbook, add a couple sheets, set up some formula references
    # between the sheets, and then rename the sheets and ensure that the changes
    # are propagated correctly
    wb = Workbook()
    _, _ = wb.new_sheet(), wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=5")
    wb.set_cell_contents("Sheet2", "A1", "=Sheet1!A1")
    wb.rename_sheet("Sheet1", "NEWNAME")
    assert wb.get_cell_value("NEWNAME", "A1") == 5
    assert wb.get_cell_contents("Sheet2", "A1") == "=NEWNAME!A1"
    assert wb.get_cell_value("Sheet2", "A1") == 5
    wb.set_cell_contents("Sheet2", "A1", "=NEWNAME!A1 + 5")
    assert wb.get_cell_value("Sheet2", "A1") == 10
    wb.rename_sheet("Sheet2", "NEWNAME2")
    assert wb.get_cell_contents("NEWNAME2", "A1") == "=NEWNAME!A1 + 5"
    assert wb.get_cell_value("NEWNAME2", "A1") == 10
    wb.set_cell_contents("NEWNAME", "A2", "=NEWNAME2!A1 + 5")
    assert wb.get_cell_value("NEWNAME", "A2") == 15


def test_invalid_name_err():
    """
    Tests that attempting to rename a sheet to an invalid error both raises an 
    error and does not mutate the workbook.
    """
    wb = Workbook()
    _, _ = wb.new_sheet(), wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=5")
    wb.set_cell_contents("Sheet2", "A1", "=Sheet1!A1")

    # Sheet names may not start or end with white space
    with pytest.raises(ValueError):
        wb.rename_sheet("Sheet1", " NEWNAME")
    assert wb.get_cell_value("Sheet1", "A1") == 5
    assert wb.get_cell_contents("Sheet2", "A1") == "=Sheet1!A1"
    assert wb.get_cell_value("Sheet2", "A1") == 5
    with pytest.raises(ValueError):
        wb.rename_sheet("Sheet2", "NEWNAME ")
    assert wb.get_cell_value("Sheet1", "A1") == 5
    assert wb.get_cell_contents("Sheet2", "A1") == "=Sheet1!A1"
    assert wb.get_cell_value("Sheet2", "A1") == 5

    # Sheet names may not contain single or double quotes
    with pytest.raises(ValueError):
        wb.rename_sheet("Sheet2", "NEW\"NAME")
    assert wb.get_cell_value("Sheet1", "A1") == 5
    assert wb.get_cell_contents("Sheet2", "A1") == "=Sheet1!A1"
    assert wb.get_cell_value("Sheet2", "A1") == 5
    with pytest.raises(ValueError):
        wb.rename_sheet("Sheet2", "NEW'NAME")
    assert wb.get_cell_value("Sheet1", "A1") == 5
    assert wb.get_cell_contents("Sheet2", "A1") == "=Sheet1!A1"
    assert wb.get_cell_value("Sheet2", "A1") == 5

    # Sheet names may not be the empty string or all whitespace
    with pytest.raises(ValueError):
        wb.rename_sheet("Sheet2", "")
    assert wb.get_cell_value("Sheet1", "A1") == 5
    assert wb.get_cell_contents("Sheet2", "A1") == "=Sheet1!A1"
    assert wb.get_cell_value("Sheet2", "A1") == 5
    with pytest.raises(ValueError):
        wb.rename_sheet("Sheet2", "   ")
    assert wb.get_cell_value("Sheet1", "A1") == 5
    assert wb.get_cell_contents("Sheet2", "A1") == "=Sheet1!A1"
    assert wb.get_cell_value("Sheet2", "A1") == 5

    # Sheet names may not be the same as another sheet name in the workbook
    with pytest.raises(ValueError):
        wb.rename_sheet("Sheet2", "Sheet1")
    assert wb.get_cell_value("Sheet1", "A1") == 5
    assert wb.get_cell_contents("Sheet2", "A1") == "=Sheet1!A1"
    assert wb.get_cell_value("Sheet2", "A1") == 5


def test_stress_formula_change():
    """
    Stress test to ensure that renaming a sheet will change all references to
    that sheet in any formulas in any other sheet. Ensures that the casing of 
    the new name is preserved exactly when it is inserted into the formulas.
    """
    wb = Workbook()
    # Set up a bunch of references in formulas and ensure they all change
    _, _, _, _= wb.new_sheet(), wb.new_sheet(), wb.new_sheet(), wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=5")
    wb.set_cell_contents("Sheet2", "A1", "=Sheet1!A1")
    wb.set_cell_contents("Sheet3", "A2", "=Sheet1!A1 + 5")
    wb.set_cell_contents("Sheet4", "A3", "=Sheet1!A1 + Sheet1!A1")
    wb.set_cell_contents("Sheet3", "A4", "=Sheet1!A1 + Sheet1!A1 + Sheet1!A1")
    wb.set_cell_contents("Sheet2", "A5", "=Sheet1!A1 + Sheet1!A1 + Sheet1!A1 + "
                         + "Sheet1!A1")
    wb.rename_sheet("Sheet1", "!@#$%^&*()")
    assert wb.get_cell_contents("!@#$%^&*()", "A1") == "=5"
    assert wb.get_cell_contents("Sheet2", "A1") == "='!@#$%^&*()'!A1"
    assert wb.get_cell_contents("Sheet3", "A2") == "='!@#$%^&*()'!A1 + 5"
    assert wb.get_cell_contents("Sheet4", "A3") == ("='!@#$%^&*()'!A1 + "
                                                    + "'!@#$%^&*()'!A1")
    assert wb.get_cell_contents("Sheet3", "A4") == ("='!@#$%^&*()'!A1 + " +
                                                    "'!@#$%^&*()'!A1 + " +
                                                    "'!@#$%^&*()'!A1")
    assert wb.get_cell_contents("Sheet2", "A5") == ("='!@#$%^&*()'!A1 + " +
                                                    "'!@#$%^&*()'!A1 + " +
                                                    "'!@#$%^&*()'!A1 + " +
                                                    "'!@#$%^&*()'!A1")

    # Ensure that the casing of the new sheet name is preserved in all formulas
    wb.rename_sheet("!@#$%^&*()", "cAsEcOnFuSiOn")
    assert wb.get_cell_contents("cAsEcOnFuSiOn", "A1") == "=5"
    assert wb.get_cell_contents("Sheet2", "A1") == "=cAsEcOnFuSiOn!A1"
    assert wb.get_cell_contents("Sheet3", "A2") == "=cAsEcOnFuSiOn!A1 + 5"
    assert wb.get_cell_contents("Sheet4", "A3") == ("=cAsEcOnFuSiOn!A1 + "
                                                    +"cAsEcOnFuSiOn!A1")
    assert wb.get_cell_contents("Sheet3", "A4") == ("=cAsEcOnFuSiOn!A1 + " +
                                                    "cAsEcOnFuSiOn!A1 + " +
                                                    "cAsEcOnFuSiOn!A1")
    assert wb.get_cell_contents("Sheet2", "A5") == ("=cAsEcOnFuSiOn!A1 + " +
                                                    "cAsEcOnFuSiOn!A1 + " +
                                                    "cAsEcOnFuSiOn!A1 + " +
                                                    "cAsEcOnFuSiOn!A1")


def test_case_insensitive_rename():
    """
    Ensures that the replacement of sheet references throughout formulas when 
    renaming is case insensitive... I.e if a user renames SHEET1 to Sheet5, then 
    instances of sheet1, ShEeT1, sHEeT1, etc. should all be replaced with
    Sheet5.
    """
    wb = Workbook()
    _, _ = wb.new_sheet(), wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=5")
    wb.set_cell_contents("Sheet2", "A1", "=Sheet1!A1")
    wb.set_cell_contents("Sheet2", "A2", "=sHeEt1!A1")
    wb.set_cell_contents("Sheet2", "A3", "=SHEET1!A1")
    wb.set_cell_contents("Sheet2", "A4", "=SheEt1!A1")
    wb.set_cell_contents("Sheet2", "A5", "=SHeeT1!A1")
    wb.set_cell_contents("Sheet2", "A6", "=SHEET1!A1")
    wb.set_cell_contents("Sheet2", "A7", "=sheet1!A1")
    wb.rename_sheet("Sheet1", "Sheet5")
    assert wb.get_cell_contents("Sheet5", "A1") == "=5"
    assert wb.get_cell_contents("Sheet2", "A1") == "=Sheet5!A1"
    assert wb.get_cell_contents("Sheet2", "A2") == "=Sheet5!A1"
    assert wb.get_cell_contents("Sheet2", "A3") == "=Sheet5!A1"
    assert wb.get_cell_contents("Sheet2", "A4") == "=Sheet5!A1"
    assert wb.get_cell_contents("Sheet2", "A5") == "=Sheet5!A1"
    assert wb.get_cell_contents("Sheet2", "A6") == "=Sheet5!A1"


def test_sq_names():
    """
    Tests the handling of single-quoted sheet names in formulas during renaming.
    In renaming, the single quotes should be stripped off of any sheet names in 
    the formulas which had single quotes but did not require them. Additionally, 
    the single quotes should be added to the new sheet name if the new sheet
    name requires them.
    """
    wb = Workbook()
    wb.new_sheet("MyFaveSheet") # Does not require single quotes in formulas
    wb.new_sheet("My Fave Sheet") # Requires single quotes in formulas
    wb.new_sheet("PLACEHOLD")
    wb.set_cell_contents("MyFaveSheet", "A1", "=5")
    wb.set_cell_contents("My Fave Sheet", "A1", "=5")

    # Should not be changed when renaming
    wb.set_cell_contents("MyFaveSheet", "A2", "='My Fave Sheet'!A1 + " +
                         "PLACEHOLD!B2")
    # Should have single quotes stripped off when renaming
    wb.set_cell_contents("My Fave Sheet", "A2", "='MyFaveSheet'!A1 + " +
                         "PLACEHOLD!B2")

    wb.rename_sheet("PLACEHOLD", "!!!") # Requires single quotes in formulas

    assert wb.get_cell_contents("MyFaveSheet", "A2") == ("='My Fave Sheet'!A1" +
                                                         " + '!!!'!B2")
    assert wb.get_cell_contents("My Fave Sheet", "A2") == ("=MyFaveSheet!A1 +"
                                                           + " '!!!'!B2")


def test_preserve_paren():
    """
    Tests that parentheses are always preserved in changed formulas when
    renaming sheets.
    """
    wb = Workbook()
    _, _ = wb.new_sheet(), wb.new_sheet()
    wb.set_cell_contents("Sheet2", "A1", "=(Sheet1!A1) + ('Sheet2'!C12)")
    wb.set_cell_contents("Sheet2", "A2", "=((Sheet1!A1))")
    wb.set_cell_contents("Sheet2", "A3", "=(((Sheet1!A1)))")
    wb.set_cell_contents("Sheet2", "A4", "=((Sheet1!A1) + (Sheet1!A2)) - " +
                         "(Sheet1!A3)")
    wb.rename_sheet("Sheet1", "Sheet5")
    assert wb.get_cell_contents("Sheet2", "A1") == "=(Sheet5!A1) + (Sheet2!C12)"
    assert wb.get_cell_contents("Sheet2", "A2") == "=((Sheet5!A1))"
    assert wb.get_cell_contents("Sheet2", "A3") == "=(((Sheet5!A1)))"
    assert wb.get_cell_contents("Sheet2", "A4") == ("=((Sheet5!A1) + " +
                                                    "(Sheet5!A2)) - " +
                                                    "(Sheet5!A3)")


def test_bad_ref_rename():
    """
    Ensures that if a cell contains a reference to C, where C is a sheet that 
    doesn't exist (and therefore the cell contains a bad reference error), but 
    then some other cell is renamed to C, then the bad reference error should 
    dissapear and be resolved.
    """
    wb = Workbook()
    _, _ = wb.new_sheet(), wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "5")
    wb.set_cell_contents("Sheet2", "A1", "=NOTASHEET!A1")
    assert isinstance(wb.get_cell_value("Sheet2", "A1"), CellError)
    assert (wb.get_cell_value("Sheet2", "A1").get_type() ==
            CellErrorType.BAD_REFERENCE)
    wb.rename_sheet("Sheet1", "NOTASHEET")
    assert not isinstance(wb.get_cell_value("Sheet2", "A1"), CellError)
    assert wb.get_cell_value("Sheet2", "A1") == 5
