"""
This file contains tests for the cell update notification system on a workbook.
It ensures that the notification system works as expected and properly notifies 
all subscribers when a cell is updated.
"""

import decimal
import sheets

OUT = None

def test_spec_example(capsys):
    """
    Tests the exact example of the cell update notification system given in the
    spec.
    """
    # Define the subscriber function
    def on_cells_changed(workbook, changed_cells): # pylint: disable=unused-argument
        '''
        This function gets called when cells change in the workbook that the
        function was registered on.  The changed_cells argument is an iterable
        of tuples; each tuple is of the form (sheet_name, cell_location).
        '''
        print(f'Cell(s) changed:  {changed_cells}')

    # Create the workbook and register the subscriber function
    wb = sheets.Workbook()
    wb.notify_cells_changed(on_cells_changed)

    # Perform some cell operations and ensure that the subscriber function is
    # called at the correct times with the correct arguments

    # Creating a new sheet with no references should not trigger the subscriber
    wb.new_sheet()
    output = capsys.readouterr().out
    assert output == ""

    # Setting a cell's contents should trigger the subscriber for that cell
    wb.set_cell_contents("Sheet1", 'A1', "'123")
    output = capsys.readouterr().out
    assert output.lower() == "cell(s) changed:  [('sheet1', 'a1')]\n"

    # Setting a cell's contents to a formula dependent on another cell will
    # change the cell's value, but not the dependencies value
    wb.set_cell_contents("Sheet1", "C1", "=A1+B1")
    output = capsys.readouterr().out
    assert output.lower() == "cell(s) changed:  [('sheet1', 'c1')]\n"

    # Changing a dependency of a formula should evaluate the set cell and the
    # formula cell. Note that the updated cells may be passed to the subscriber
    # in any order.
    wb.set_cell_contents("Sheet1", "B1", "5.3")
    output = capsys.readouterr().out.lower()
    assert output in [
        "cell(s) changed:  [('sheet1', 'b1'), ('sheet1', 'c1')]\n",
        "cell(s) changed:  [('sheet1', 'c1'), ('sheet1', 'b1')]\n"]

    # Deleting the sheet should not trigger the subscriber for the deleted cells
    wb.del_sheet("Sheet1")
    output = capsys.readouterr().out.lower()
    assert output in [""]


def test_set_contents_notifs():
    """
    Tests that the cell update notification system works when cells are set
    using the set_cell_contents function without any dependencies.
    """
    global OUT # pylint: disable=global-statement
    # Define the subscriber function
    def on_cells_changed(workbook, changed_cells): # pylint: disable=unused-argument
        '''
        This function gets called when cells change in the workbook that the
        function was registered on.  The changed_cells argument is an iterable
        of tuples; each tuple is of the form (sheet_name, cell_location).
        '''
        global OUT # pylint: disable=global-statement
        OUT = set()
        for changed_cell in changed_cells:
            OUT.add((changed_cell[0].lower(), changed_cell[1].lower()))

    # Create the workbook and register the subscriber function
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.notify_cells_changed(on_cells_changed)

    # Set the contents of many cells and ensure the subscriber is called with
    # only the cells which are set as arguments
    wb.set_cell_contents("Sheet1", "A1", "123")
    assert OUT == set([("sheet1", "a1")])

    wb.set_cell_contents("Sheet1", "B1", "123")
    assert OUT == set([("sheet1", "b1")])

    wb.set_cell_contents("Sheet1", "C1", "123")
    assert OUT == set([("sheet1", "c1")])

    wb.set_cell_contents("Sheet1", "D1", "foo")
    assert OUT == set([("sheet1", "d1")])

    # Ensure that the workbook may have multiple subscribers without triggering
    # any errors
    wb.notify_cells_changed(on_cells_changed)
    wb.set_cell_contents("Sheet1", "E1", "bar")
    assert OUT == set([("sheet1", "e1")])


def test_set_forms_notifs():
    """
    Tests that the cell update notification system works when cells are set
    using the set_cell_contents function with dependencies.
    """
    global OUT # pylint: disable=global-statement
    # Define the subscriber function
    def on_cells_changed(workbook, changed_cells): # pylint: disable=unused-argument
        '''
        This function gets called when cells change in the workbook that the
        function was registered on.  The changed_cells argument is an iterable
        of tuples; each tuple is of the form (sheet_name, cell_location).
        '''
        global OUT # pylint: disable=global-statement
        OUT = set()
        for changed_cell in changed_cells:
            OUT.add((changed_cell[0].lower(), changed_cell[1].lower()))

    # Create the workbook and register the subscriber function
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.notify_cells_changed(on_cells_changed)

    # Set the contents of many cells and ensure the subscriber is called with
    # only the cells which are set as arguments
    wb.set_cell_contents("Sheet1", "A1", "123")
    assert OUT == set([("sheet1", "a1")])

    wb.set_cell_contents("Sheet1", "B1", "=A1")
    assert OUT == set([("sheet1", "b1")])

    wb.set_cell_contents("Sheet1", "C1", "=B1")
    assert OUT == set([("sheet1", "c1")])

    wb.set_cell_contents("Sheet1", "D1", "=C1")
    assert OUT == set([("sheet1", "d1")])

    wb.set_cell_contents("Sheet1", "E1", "=D1")
    assert OUT == set([("sheet1", "e1")])

    # Now make sure that fomulas which evaluate multiple cells return all updated
    # cells to the subscriber
    wb.set_cell_contents("Sheet1", "A1", "5")
    assert OUT == set([("sheet1", "a1"), ("sheet1", "b1"), ("sheet1", "c1"),
                       ("sheet1", "d1"), ("sheet1", "e1")])


def test_multi_notif():
    """
    Tests that multiple subscribers may be registered to a workbook at the same 
    time
    """
    global OUT # pylint: disable=global-statement
    # Define the subscriber function
    OUT = []
    def on_cells_changed(workbook, changed_cells): # pylint: disable=unused-argument
        '''
        This function gets called when cells change in the workbook that the
        function was registered on.  The changed_cells argument is an iterable
        of tuples; each tuple is of the form (sheet_name, cell_location).
        '''
        for changed_cell in changed_cells:
            OUT.append((changed_cell[0].lower(), changed_cell[1].lower()))

    # Create the workbook and register the subscriber function
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.notify_cells_changed(on_cells_changed)
    wb.notify_cells_changed(on_cells_changed)

    # Set the contents of many cells and ensure the subscriber is called with
    # only the cells which are set as arguments
    wb.set_cell_contents("Sheet1", "A1", "123")
    assert OUT == [("sheet1", "a1"), ("sheet1", "a1")]
    OUT = []

    wb.set_cell_contents("Sheet1", "B1", "=A1")
    assert OUT == [("sheet1", "b1"), ("sheet1", "b1")]
    OUT = []

    wb.set_cell_contents("Sheet1", "C1", "=B1")
    assert OUT == [("sheet1", "c1"), ("sheet1", "c1")]
    OUT = []


def test_notif_form_err():
    """
    Ensures that the cell update notification provides an update for any cell
    which changes from a formula to an error and vice versa.
    """
    global OUT # pylint: disable=global-statement
    # Define the subscriber function
    def on_cells_changed(workbook, changed_cells): # pylint: disable=unused-argument
        '''
        This function gets called when cells change in the workbook that the
        function was registered on.  The changed_cells argument is an iterable
        of tuples; each tuple is of the form (sheet_name, cell_location).
        '''
        global OUT # pylint: disable=global-statement
        OUT = set()
        for changed_cell in changed_cells:
            OUT.add((changed_cell[0].lower(), changed_cell[1].lower()))

    # Create the workbook and register the subscriber function
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.notify_cells_changed(on_cells_changed)

    # Set the contents of many cells and ensure the subscriber is called with
    # only the cells which are set as arguments
    wb.set_cell_contents("Sheet1", "A1", "123")
    assert OUT == set([("sheet1", "a1")])

    wb.set_cell_contents("Sheet1", "A1", "=1/0")
    assert OUT == set([("sheet1", "a1")])

    wb.set_cell_contents("Sheet1", "A1", "=B1")
    assert OUT == set([("sheet1", "a1")])

    wb.set_cell_contents("Sheet1", "B1", "1/")
    assert OUT == set([("sheet1", "b1"), ("sheet1", "a1")])

    wb.set_cell_contents("Sheet1", "B1", "1+1")
    assert OUT == set([("sheet1", "b1"), ("sheet1", "a1")])


def test_notif_err():
    """
    Ensures that if the cell update subscriber throws an error, the internal 
    state and computation of the spreadsheet is not affected.
    """
    def on_cells_changed(workbook, changed_cells): # pylint: disable=unused-argument
        '''
        This function gets called when cells change in the workbook that the
        function was registered on.  The changed_cells argument is an iterable
        of tuples; each tuple is of the form (sheet_name, cell_location).
        '''
        raise ValueError("Just because I'm a bad person")

    # Create the workbook and register the subscriber function
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.notify_cells_changed(on_cells_changed)

    # Set the contents of many cells and ensure the subscriber is called with
    # only the cells which are set as arguments
    wb.set_cell_contents("Sheet1", "A1", "123")
    assert wb.get_cell_contents("Sheet1", "A1") == "123"
    assert wb.get_cell_value("Sheet1", "A1") == decimal.Decimal(123)

    wb.set_cell_contents("Sheet1", "A1", "=1/0")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.DIVIDE_BY_ZERO)

    wb.set_cell_contents("Sheet1", "A1", "=A1")
    assert isinstance(wb.get_cell_value("Sheet1", "A1"), sheets.CellError)
    assert (wb.get_cell_value("Sheet1", "A1").get_type() ==
            sheets.CellErrorType.CIRCULAR_REFERENCE)

    wb.set_cell_contents("Sheet1", "A1", "=2")
    wb.set_cell_contents("Sheet1", "B1", "=(3*(A1+3)-5)&\"foo\"")
    assert wb.get_cell_value("Sheet1", "B1") == str(3*(2+3)-5)+"foo"


def test_multi_call_err():
    """
    Ensures that if a workbook has multiple subscribers, one of which raises an
    error, that the other subscribers are still called.
    """
    global OUT # pylint: disable=global-statement
    # Define the subscriber function
    OUT = []
    def on_cells_changed(workbook, changed_cells): # pylint: disable=unused-argument
        OUT.append((changed_cells[0][0].lower(), changed_cells[0][1].lower()))


    def on_cell_changed2(workbook, changed_cells): # pylint: disable=unused-argument
        raise ValueError("Just because I'm a bad person")


    # Create the workbook and register the subscriber function
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.notify_cells_changed(on_cell_changed2)
    wb.notify_cells_changed(on_cells_changed)

    # Set the contents of many cells and ensure the subscriber is called with
    # only the cells which are set as arguments
    wb.set_cell_contents("Sheet1", "A1", "123")
    assert wb.get_cell_contents("Sheet1", "A1") == "123"
    assert wb.get_cell_value("Sheet1", "A1") == decimal.Decimal(123)
    assert OUT == [("sheet1", "a1")]


def test_del_sheet():
    """
    Ensures that when a sheet is deleted which has other formulas in the workbook
    which reference it, that the subscriber is called with the cells which are
    updated, being those in the sheet which was not deleted that depend on the 
    deleted sheet.
    """
    global OUT # pylint: disable=global-statement
    # Define the subscriber function
    OUT = []
    def on_cells_changed(workbook, changed_cells): # pylint: disable=unused-argument
        OUT.append(changed_cells)

    # Create the workbook and register the subscriber function
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "123")
    wb.set_cell_contents("Sheet1", "B1", "=A1")
    wb.set_cell_contents("Sheet1", "C1", "=B1")
    wb.new_sheet()
    wb.set_cell_contents("Sheet2", "A1", "=Sheet1!A1")
    wb.notify_cells_changed(on_cells_changed)

    # Delete the first sheet and ensure the subscriber is called with the cells
    # which are updated
    wb.del_sheet("Sheet1")
    assert OUT[0] == [("sheet2", "A1")]


def test_copy_notifs():
    """
    Ensures that when a sheet is copied, notifications are sent to the subscriber
    for all non-empty cells in the new sheet.
    """
    global OUT # pylint: disable=global-statement
    # Define the subscriber function
    OUT = []
    def on_cells_changed(workbook, changed_cells): # pylint: disable=unused-argument
        OUT.append(set(changed_cells))

    # Create the workbook and register the subscriber function
    wb = sheets.Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "123")
    wb.set_cell_contents("Sheet1", "B1", "=A1")
    wb.set_cell_contents("Sheet1", "C1", "=B1")
    wb.notify_cells_changed(on_cells_changed)

    # Copy the first sheet and ensure the subscriber is called with the cells
    # which are updated
    wb.copy_sheet("Sheet1")
    assert OUT[0] == set([("sheet1_1", "A1"), ("sheet1_1", "B1"), ("sheet1_1", "C1")])
