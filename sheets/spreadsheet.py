"""
This module contains the Spreadsheet class. This class is responsible for 
managing the cells in the spreadsheet and for evaluating formulas. A Spreadsheet 
consists of a Dictionary mapping cell locations in a spreadsheet to Cell objects.
"""

from functools import cache

from .regexp import VALID_LOC
from .cell import Cell

# Utility Functions
@cache
def check_valid_location(location: str) -> bool:
    """
    Checks if the given location is a valid cell location. A valid location is 
    a string of the form <column><row>, where <column> is a letter from A-ZZZZ 
    and <row> is a number from 1-9999. Returns True if the location is valid,
    False, otherwise.
    """
    # Check if the input string matches the pattern
    return VALID_LOC.fullmatch(location) is not None


@cache
def column_label_to_number(label : str) -> int:
    """
    Converts a column label to the corresponding column number to keep track of 
    the extent.
    """
    num = 0
    for i in range(len(label)):
        num += (ord(label[-(i+1)]) - 64) * (26 ** i)
    return num


def get_column_label(location : str) -> str:
    """
    Returns the column label of the given location.
    """
    return location.strip('0123456789')


@cache
def get_row_number(location : str) -> int:
    """
    Returns the row number of the given location.
    """
    return int(location[len(get_column_label(location)):])

def get_column_label_from_number(col_num: int) -> str:
    """
    Converts a column number to its corresponding Excel column label.
    
    Args:
    col_num (int): The column number (1-based index).
    
    Returns:
    str: The corresponding column label.
    """
    # Initialize an empty string for the column label
    column_label = ""
    while col_num > 0:
        # Adjust for 0-indexing and find the remainder
        remainder = (col_num - 1) % 26
        # Convert the remainder to the corresponding letter
        letter = chr(remainder + 65)  # 65 is the ASCII value for 'A'
        # Prepend the letter to the column label (since we're iterating from
        # least to most significant digit)
        column_label = letter + column_label
        # Update the column number for the next iteration
        col_num = (col_num - 1) // 26

    return column_label


class Spreadsheet():
    """
    This class represents a spreadsheet. It is responsible for managing the cells
    in the spreadsheet and for evaluating formulas.

    Attributes:
        cells (dict): A dictionary mapping cell locations to Cell objects.
        max_row (int): The maximum row number of the spreadsheet.
        max_col (int): The maximum column number of the spreadsheet.
        display_name (str): The name of the spreadsheet with preserved casing.
    """

    def __init__(self, display_name: str):
        self._cells = {}
        self._rows = {}
        self._cols = {}
        self._max_row = 0
        self._max_col = 0
        self.display_name = display_name

    def set_cell_contents(self, location: str, content: str) -> None:
        """ 
        Sets the contents of the cell at the given location to the given content.
        """
        # Setting a cell to empty should delete it if it was populated,
        # otherwise do nothing
        if not check_valid_location(location):
            raise ValueError(f"Invalid cell location: {location}")

        # If contents are empty, then delete the cell
        if content is None or content.strip() == "":
            self._del_cell(location)
            return

        col_label = get_column_label(location)
        col_num = column_label_to_number(col_label)
        row_num = get_row_number(location)

        # If no cell deleted, then set the contents as desired. If the cell
        # already exists, mutate it, otherwise allocate a new cell.
        cell = self._cells.get(location)
        if cell:
            cell.set_content(content)
        else:
            self._cells[location] = Cell(content, self, location)
            self._max_row = max(self._max_row, row_num)
            self._max_col = max(self._max_col, column_label_to_number(col_label))
        # Update the row and column dicts to include the new cell
        if row_num not in self._rows:
            self._rows[row_num] = set()
        if col_num not in self._cols:
            self._cols[col_num] = set()
        self._rows[row_num].add(col_num)
        self._cols[col_num].add(row_num)

    def _del_cell(self, location: str) -> str:
        """
        Deletes the cell at the given location and updates the spreadsheet extent
        accordingly. Should only be called by the spreadsheet set_cell_contents
        method.
        """
        if location in self._cells:
            col_label = get_column_label(location)
            col_num = column_label_to_number(col_label)
            row_num = get_row_number(location)
            del self._cells[location]
            # Remove from row and col dictionaries
            if col_num in self._cols:
                self._cols[col_num].remove(row_num)
                if len(self._cols[col_num]) == 0:
                    del self._cols[col_num]
            if row_num in self._rows:
                self._rows[row_num].remove(col_num)
                if len(self._rows[row_num]) == 0:
                    del self._rows[row_num]
            # If the row or column are the max row or column, and they are now
            # empty, then update the max row or column
            if col_num == self._max_col and self._cols.get(col_num) is None:
                self._max_col = (max(self._cols.keys()) if len(self._cols)
                                    > 0 else 0)
            if row_num == self._max_row and self._rows.get(row_num) is None:
                self._max_row = (max(self._rows.keys()) if len(self._rows)
                                    > 0 else 0)

    def get_extent(self) -> tuple:
        """
        Returns the extent of the spreadsheet as a tuple of the form 
        (max_row, max_col).
        """
        return (self._max_col, self._max_row)

    def get_cell_contents(self, location: str) -> str:
        """ 
        Returns the contents of the cell at the given location.
        """
        if not check_valid_location(location):
            raise ValueError(f"Invalid cell location {location}")
        cell = self._cells.get(location)
        return cell.get_content() if cell else None

    def get_cell_value(self, location: str):
        """ 
        Returns the value of the cell at the given location.
        """
        if not check_valid_location(location):
            raise ValueError(f"Invalid cell location {location}")
        cell = self._cells.get(location)
        return cell.get_value() if cell else None

    def get_cell_type(self, location: str):
        """ 
        Returns the type of the cell at the given location.
        """
        if not check_valid_location(location):
            raise ValueError(f"Invalid cell location {location}")
        cell = self._cells.get(location)
        return cell.get_type() if cell else None

    def set_cell_value(self, location: str, value):
        """ 
        Sets the value of the cell at the given location. Should be called when 
        cells are formulas being evaluated or cells are being set to errors.
        """
        assert check_valid_location(location)
        cell = self._cells.get(location)
        cell.set_value(value)

    def get_cell(self, location: str) -> Cell:
        """ 
        Returns the cell object at the given location.
        """
        if not check_valid_location(location):
            raise ValueError(f"Invalid cell location: {location}")
        return self._cells.get(location)

    def get_cells(self) -> list:
        """
        Returns a list of all cells locations populated in the sheet.
        """
        return list(self._cells.keys())

    def __getitem__(self, location: str) -> Cell:
        """ 
        Returns the value of the cell at the given location.
        """
        return self.get_cell_value(location)

    def adjust_extent(self, new_max_row: int, new_max_col: int) -> None:
        """
        Adjusts the spreadsheet's extent to accommodate new cell locations.

        Args:
        new_max_row (int): The new maximum row number.
        new_max_col (int): The new maximum column number.
        """
        self._max_row = max(self._max_row, new_max_row)
        self._max_col = max(self._max_col, new_max_col)
