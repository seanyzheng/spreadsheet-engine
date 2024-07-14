"""
Package setup for the sheets package.
"""

# Ensure only the cell error types and workbook classes are imported when using
# the sheets package.
from .workbook import Workbook
from .error_types import CellErrorType, CellError
__all__ = ["CellErrorType", "CellError", "Workbook"]

# Sets the version of the package.
version = "1.3" # pylint: disable=invalid-name
