""" 
This module implements the Cell class, which is the basic unit of the 
spreadsheet application. Cells are containers holding both the string content 
that the user input into the cell as well as the evaluated value of the cell. 
Cells are restricted to a certain number of types, defined in the CellType 
enumeration.
"""

from decimal import Decimal, InvalidOperation
import enum
import re
from functools import lru_cache

import lark

from .error_types import CellError, CellErrorType, error_dict

# Preallocate a parser for the evaluator to use
PARSER = lark.Lark.open('sheets/formulas.lark', start='formula', ordered_sets=False)


@lru_cache(maxsize=None)
def cached_parse(contents: str):
    """
    This function is a decorator that caches the results of the parse method
    for a given string. This should improve the performance of evaluating formulas
    """
    return PARSER.parse(contents)


class CellType(enum.Enum):
    """ 
    This enumeration defines the types of cells that are supported by the 
    spreadsheet application. 
    """
    STRING = 1

    NUMBER = 2

    FORMULA = 3

    PARSE_ERROR = 4

    BOOL = 5

# Utility Functions)

class Cell:
    """ 
    This class represents a single cell in the spreadsheet application.

    Attributes:
        content (str): The string content of the cell.
        type (CellType): The type of the cell.
        value: The evaluated value of the cell. Can be a string or a Decimal.
        sheet (Spreadsheet): The spreadsheet that the cell belongs to.
        parse_tree: The cached parse tree of the cell's formula or None.
    """

    def __init__(self, content: str, sheet=None, location=None):
        """ 
        Initializes a new cell with the given content. Determines the type of
        the cell based on the content, and sets the value based on the type.
        Strips whitespace from the content as appropriate.
        """
        # Cells hold string contents, a CellType, and a value
        self._content = content.strip()
        self._type = None
        self._value = None
        self.sheet = sheet
        self.location = location

        # Determine the type and evaluate the cell
        self._parse_contents()

    # Getters and Setters

    def get_content(self) -> str:
        """ 
        Returns the content of the cell.
        """
        return self._content

    def get_type(self) -> CellType:
        """ 
        Returns the type of the cell.
        """
        return self._type

    def get_value(self):
        """ 
        Returns the value of the cell.
        """
        return self._value

    def set_content(self, content: str) -> None:
        """ 
        Sets the content of the cell and re-evaluates the cell.
        """
        self._content = content.strip()
        self._parse_contents()

    def set_value(self, value) -> None:
        """ 
        Sets the value of the cell. This should only be called when the cell is
        a formula cell and the formula is being evaluated at the Spreadsheet
        level.
        """
        if not self._type == CellType.FORMULA:
            raise TypeError("Value cannot be mutated for non-formula cells.")
        self._value = value

    # Private Methods

    def _parse_contents(self) -> None:
        """
        Determines and sets the type of the cell and evaluates the cell's value 
        based on the contents.
        """
        if self._content == "":
            raise ValueError("Cell content cannot be empty.")

        # Check whether cell holds a formula
        if self._content.startswith("="):
            self._type = CellType.FORMULA
            try:
                cached_parse(self._content)
            except lark.exceptions.LarkError as e:
                self._type = CellType.PARSE_ERROR
                self._value = CellError(CellErrorType.PARSE_ERROR, str(e))
                return
            return

        # Check if the cell is a boolean
        if self._content.upper() in ["TRUE", "FALSE"]:
            self._type = CellType.BOOL
            self._value = self._content.upper() == "TRUE"
            return

        # Check if the cell may be parsed as a number
        try:
            # Check if the cell may be parsed as a number
            assert self._content == re.sub("[a-z|A-Z]", "", self._content)
            value = Decimal(self._content)
            # Strip trailing zeroes while preserving value
            self._value = (value.quantize(1) if value == value.to_integral()
                          else value.normalize())
            self._type = CellType.NUMBER

        # If not a number or formula, cell is a string
        except (InvalidOperation, AssertionError) as _:
            self._type = CellType.STRING
            if error_dict.get(self._content.upper()):
                self._value = CellError(error_dict[self._content.upper()],
                                        "Error from contents")
            elif self._content.startswith('\''):
                # Strip leading apostrophe
                self._value = self._content[1:]
            else:
                self._value = self._content
