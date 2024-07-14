"""
This module defines the types of errors that can exist in cells. These
constitute a required part of the spreadsheet public-facing API and so are 
placed in their own file to allow independent export from the package without 
the rest of the Cell class internals.
"""

from typing import Optional
import enum

class CellErrorType(enum.Enum):
    '''
    This enum specifies the kinds of errors that spreadsheet cells can hold, and 
    how they should be formatted into a string representation.
    '''

    # A formula doesn't parse successfully ("#ERROR!")
    PARSE_ERROR = 1

    # A cell is part of a circular reference ("#CIRCREF!")
    CIRCULAR_REFERENCE = 2

    # A cell-reference is invalid in some way ("#REF!")
    BAD_REFERENCE = 3

    # Unrecognized function name ("#NAME?")
    BAD_NAME = 4

    # A value of the wrong type was encountered during evaluation ("#VALUE!")
    TYPE_ERROR = 5

    # A divide-by-zero was encountered during evaluation ("#DIV/0!")
    DIVIDE_BY_ZERO = 6


class CellError:
    '''
    This class represents an error value from user input, cell parsing, or
    evaluation.
    '''

    def __init__(self, error_type: CellErrorType, detail: str,
                 exception: Optional[Exception] = None):
        self._error_type = error_type
        self._detail = detail
        self._exception = exception

    def get_type(self) -> CellErrorType:
        ''' The category of the cell error. '''
        return self._error_type

    def get_detail(self) -> str:
        ''' More detail about the cell error. '''
        return self._detail

    def get_exception(self) -> Optional[Exception]:
        '''
        If the cell error was generated from a raised exception, this is the
        exception that was raised.  Otherwise this will be None.
        '''
        return self._exception

    def __str__(self) -> str:
        return f'ERROR[{self._error_type}, "{self._detail}"]'

    def __repr__(self) -> str:
        return self.__str__()


# Preallocate a Dict mapping cell error expression strings to their error types
error_dict = {
    '#DIV/0!': CellErrorType.DIVIDE_BY_ZERO,
    '#ERROR!': CellErrorType.PARSE_ERROR,
    '#CIRCREF!': CellErrorType.CIRCULAR_REFERENCE,
    '#REF!': CellErrorType.BAD_REFERENCE,
    '#NAME?': CellErrorType.BAD_NAME,
    '#VALUE!': CellErrorType.TYPE_ERROR
}

# Preallocate a Dict mapping cell error types to their corresponding literal strings
rev_error_dict = {
    CellErrorType.DIVIDE_BY_ZERO: '#DIV/0!',
    CellErrorType.PARSE_ERROR: '#ERROR!',
    CellErrorType.CIRCULAR_REFERENCE: '#CIRCREF!',
    CellErrorType.BAD_REFERENCE: '#REF!',
    CellErrorType.BAD_NAME: '#NAME?',
    CellErrorType.TYPE_ERROR: '#VALUE!'
}
