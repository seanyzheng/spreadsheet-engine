"""
This module contains the logic for the FuncDir class. This class is used to
store the functions that are defined within a certain Workbook. Every function
in the FuncDir for a workbook is available for use via function calls in 
formula cells within the workbook. The function calls are automatically 
recognized by the formulas evaluator which refers to the workbook's FuncDir
in order to evaluate it.
"""

from typing import Optional, Callable, Tuple
from decimal import Decimal
from functools import reduce
from copy import deepcopy

import sheets
from .error_types import CellError, CellErrorType
from .regexp import is_ref, find_refs
from .evaluator import Evaluator

# A map from the required types of arguments to the function which converts
# an argument to that type.
type_conv_map = {
    str : Evaluator.check_str,
    Decimal : Evaluator.check_numeric,
    bool : Evaluator.check_bool,
}

class FuncInfo():
    """
    A class representing the information about a function. This includes the
    function's name, the function's properties, the function's requirements,
    and the function's implementation.
    """

    def __init__(self, arg_limit: Optional[int], min_args: int,
                 req_arg_types: Optional[dict[int, type]],
                 rpt_type: Optional[type], evaler: Callable,
                 contextual: bool = False):
        """
        Initializes a new FuncInfo object with the given properties.
        """
        self.arg_limit = arg_limit
        self.min_args = min_args
        self.req_arg_types = req_arg_types
        self.rpt_type = rpt_type
        self.evaler = evaler
        self.contextual = contextual

    def get_requirements(self) -> tuple:
        """
        Returns a tuple of the requirements for the function.
        """
        return (self.arg_limit, self.min_args, self.req_arg_types, self.rpt_type)

    def check_args(self, args : list) -> Tuple[bool, list]:
        """
        Takes in a list of arguments and checks if the arguments are valid
        based on the requirements of the function.
        """
        if self.arg_limit is not None and len(args) > self.arg_limit:
            return (False, [])
        if len(args) < self.min_args:
            return (False, [])
        new_args = deepcopy(args)
        if self.req_arg_types is not None:
            for arg in self.req_arg_types:
                if not isinstance(args[arg], self.req_arg_types[arg]):
                    new_arg = type_conv_map[self.req_arg_types[arg]](args[arg])
                    if isinstance(new_arg, CellError):
                        return (False, [])
                    new_args[arg] = new_arg
        if self.rpt_type is not None:
            for i, arg in enumerate(args):
                if self.req_arg_types is not None and i in self.req_arg_types:
                    continue
                if not isinstance(arg, self.rpt_type):
                    new_arg = type_conv_map[self.rpt_type](arg)
                    if isinstance(new_arg, CellError):
                        return (False, [])
                    new_args[i] = new_arg
        return (True, new_args)


def choose(args):
    """
    The function implementation for the default CHOOSE function.
    """
    index = args[0]
    int_index = int(index)
    if int_index != index:
        return CellError(CellErrorType.TYPE_ERROR, "CHOOSE: Index is not an integer.")
    if int_index < 1 or int_index > len(args) - 1:
        return CellError(CellErrorType.TYPE_ERROR, "CHOOSE: Index out of range.")
    return args[int_index]


def indirect(args, wb, from_sheet, from_cell, evaluator):
    """
    The function implementation for the default INDIRECT function.
    """
    ref = args[0]
    if ref.startswith("ERROR"):
        ref = ref.replace('[',',')
        l = ref.split(',')
        error = l[1]
        if error == 'CellErrorType.DIVIDE_BY_ZERO':
            return CellError(CellErrorType.DIVIDE_BY_ZERO, "INDIRECT: Divide by zero.")
        if error == 'CellErrorType.PARSE_ERROR':
            return CellError(CellErrorType.PARSE_ERROR, "INDIRECT: Parse error.")
        if error == 'CellErrorType.CIRCULAR_REFERENCE':
            return CellError(CellErrorType.CIRCULAR_REFERENCE, "INDIRECT: Circular reference.")
        if error == 'CellErrorType.BAD_REFERENCE':
            return CellError(CellErrorType.BAD_REFERENCE, "INDIRECT: Bad reference.")
        if error == 'CellErrorType.BAD_NAME':
            return CellError(CellErrorType.BAD_NAME, "INDIRECT: Bad name.")
        if error == 'CellErrorType.TYPE_ERROR':
            return CellError(CellErrorType.TYPE_ERROR, "INDIRECT: Type error.")

    if isinstance(ref, CellError):
        print("gothere")
        return ref
    if not is_ref(ref):
        return CellError(CellErrorType.BAD_REFERENCE, "INDIRECT: Invalid reference.")
    val = find_refs(ref)
    if val[1]:
        index = val[1][0][1].upper()
        sheet_name = val[1][0][0].strip('\'"').lower()
    else:
        sheet_name = from_sheet.display_name
        index = val[0][0].upper()
        index = index.replace("$", "")
    if sheet_name.lower() not in wb.sheets:
        return CellError(CellErrorType.BAD_REFERENCE, "INDIRECT: Sheet does not exist.")

    from_sheet_name = from_sheet.display_name.lower()
    from_index = from_cell.location
    if ((sheet_name.lower(), index) not in
        wb.interaction_graph.graph[(from_sheet_name, from_index)]):
        evaluator.eval_dependencies.add(((from_sheet_name, from_index),
                                         (sheet_name.lower(), index)))
        wb.interaction_graph.add_dependency((from_sheet_name, from_index),
                                             (sheet_name.lower(), index))
    return wb.get_cell_value(sheet_name, index)


# Default functions that are available in every workbook
FUNCTION_DEFAULTS = {
    # Boolean Functions
    "AND" : FuncInfo(None, 1, None, bool, lambda l:
                     reduce(lambda x, y: x and y, l, True)),
    "OR" : FuncInfo(None, 1, None, bool, lambda l:
                    reduce(lambda x, y: x or y, l)),
    "NOT" : FuncInfo(1, 1, {0 : bool}, None, lambda x: not x[0]),
    "XOR" : FuncInfo(None, 1, None, bool, lambda l:
                     reduce(lambda x, y: x + y, l) % 2 == 1),
    # String matching functions
    "EXACT" : FuncInfo(2, 2, {0 : str, 1 : str}, None, lambda x: x[0] == x[1]),
    # Conditional functions
    "IF" : FuncInfo(3, 2, {0 : bool}, None, lambda x: x[1] if x[0]
                    else (x[2]if len(x) > 2 else False)),
    "IFERROR" : FuncInfo(3, 1, None, None, lambda x: x[0] if not
                         isinstance(x[0], CellError) else (x[1] if len(x) > 1 else "")),
    "CHOOSE" : FuncInfo(None, 2, {0 : Decimal}, None, choose),
    # Info Functions
    "ISBLANK" : FuncInfo(1, 1, None, None, lambda x: x[0] is None),
    "ISERROR" : FuncInfo(1, 1, None, None, lambda x: isinstance(x[0], CellError)),
    "VERSION" : FuncInfo(0, 0, None, None, lambda _: sheets.version),
    # Indirection
    "INDIRECT" : FuncInfo(1, 1, {0 : str}, None, indirect, True),
}


class FuncDir():
    """
    A directory mapping function names to their respective properties,
    requirements, and implementations.
    """

    def __init__(self):
        """
        Initializes a new FuncDir object with an empty directory.
        """
        self.funcs = deepcopy(FUNCTION_DEFAULTS)

    def list_functions(self) -> list:
        """
        Returns a list of the names of all the functions in the directory.
        """
        return list(self.funcs.keys())

    def evaluate(self, func_name: str, args: list,
                 wb, sheet, cell, evaluator) -> any:
        """
        Takes in a function name and a list of arguments and evaluates the
        function with the given arguments. Returns the result of the evaluation.
        """
        if func_name in self.funcs:
            func = self.funcs[func_name]
            valid_args, conv_args = func.check_args(args)
            if valid_args:
                if func.contextual:
                    content = func.evaler(conv_args, wb, sheet, cell, evaluator)
                else:
                    content = func.evaler(conv_args)
                return content
            return CellError(CellErrorType.TYPE_ERROR,
                             f"Invalid arguments for function {func_name}.")
        return CellError(CellErrorType.BAD_NAME,
                         f"Function {func_name} does not exist.")
