"""
This module contains the formula evaluator responsible for computing the values
of cells throughout a workbook. The evaluator inherents from the
lark.visitors.Interpreter class, which allows it to traverse the parse tree
generated by the parser and evaluate the formula.

This module also contains a simple ref finder class used to find all cell
references in a given formula. This is used by the workbook to populate its cell
dependency graph.
"""

from functools import lru_cache
from decimal import Decimal, InvalidOperation

from lark.visitors import Interpreter, visit_children_decor


from .error_types import CellError, CellErrorType, error_dict
from .spreadsheet import check_valid_location


# Default empty cell types for each datatype
NONE_TYPES = {
    str: "",
    Decimal: Decimal(0),
    bool: False
}


# Type values for each datatype for comparison. Used to determined the value of
# comparison operations between two values of potentially different types.
TYPE_VALUES = {
    Decimal: 0,
    str: 1,
    bool: 2
}


class Evaluator(Interpreter):
    """
    The formula evaluator is responsible for computing the values of cells
    throughout a workbook. The evaluator inherits from the
    lark.visitors.Interpreter class, which allows it to traverse the parse tree.
    The rules here describe how a node in the parse tree should be evaluated. 
    When invoked with Evaluator.visit(), the evaluator will traverse the parse
    tree top down and evaluate the formula.

    Attributes:
        workbook (Workbook): The workbook that the cell belongs to.
        sheet (Spreadsheet): The sheet that the cell belongs to.
    """

    def __init__(self, workbook, sheet, cell=None):
        """
        Initialize the evaluator with a pointer to a workbook object and 
        Spreadsheet object. This is required to access the values of cells
        across other sheets.
        """
        self.workbook = workbook
        self.sheet = sheet
        self.from_cell = cell
        # list of dependencies acquired from evaluation
        self.eval_dependencies = set()

    def get_eval_dependencies(self):
        """
        Returns the list of dependencies acquired from evaluation.
        """
        return self.eval_dependencies
    def reset_eval_dependencies(self):
        """
        Resets the list of dependencies acquired from evaluation.
        """
        self.eval_dependencies = set()

    @staticmethod
    def values_error_helper(values):
        """
        Helper function for checking the types of values in a formula.
        """
        errors = []
        for value in values:
            if isinstance(value, CellError):
                if value.get_type() == CellErrorType.CIRCULAR_REFERENCE:
                    return value
                errors.append(value)
        if len(errors) > 0:
            return errors[0]
        return None

    @staticmethod
    def process_num(value):
        """
        Processes a numeric output of the evaluator. If the output is not a number, 
        returns the original value. If the output is a number, then all trailing 
        zeros are stripped while maintaining the value and the value is returned
        """
        if isinstance(value, Decimal):
            try:
                value = Decimal(value)
                return (value.quantize(1) if value == value.to_integral()
                            else value.normalize())
            except InvalidOperation:
                return value.normalize()
        return value

    @staticmethod
    def check_numeric(value):
        """
        Helper function for checking if a value is numeric. Returns the numeric 
        representation of the value if numeric, otherwise returns a CellError.
        """
        # Attempt to parse as a decimal
        try:
            if value is None:
                return Decimal(0)
            if isinstance(value, str) and value[0] == "'":
                return Decimal(value[1:].strip())
            if isinstance(value, bool):
                value = 1 if value else 0
            return Decimal(value)

        # If unable to parse, return a CellError
        except (InvalidOperation, TypeError):
            if isinstance(value, CellError):
                return value
            return CellError(CellErrorType.TYPE_ERROR, "Not numeric")

    @staticmethod
    def check_str(value):
        """
        Called to parse the arguments to a string operator as strings.
        """
        if value is None:
            return ""
        if isinstance(value, bool):
            return str(value).upper()
        return str(value)

    @staticmethod
    def check_bool(value):
        """
        Called to parse the arguments to a boolean operator as booleans.
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.upper() in ["TRUE", "FALSE"]:
                return value.upper() == "TRUE"
            return CellError(CellErrorType.TYPE_ERROR, "Not boolean")
        if isinstance(value, Decimal):
            return value != 0
        if isinstance(value, CellError):
            return value
        return False

    @lru_cache(maxsize=200)
    def number(self, tree):
        """
        Return the value of a number node.
        """
        # For a number node we should be able to parse as a decimal
        try:
            value =  Decimal(tree.children[0])
            return Evaluator.process_num(value)

        # If unable to parse, return a CellError
        except InvalidOperation:
            return CellError(CellErrorType.TYPE_ERROR, "Not numeric")

    @lru_cache(maxsize=200)
    def string(self, tree):
        """
        Return the value of a string node.
        """
        if not error_dict.get(tree.children[0].upper()):
            return tree.children[0].strip('"')

        # If string version of an error, return the error
        return CellError(error_dict[tree.children[0].upper()], "Error from string")

    @visit_children_decor
    def parens(self, values):
        """
        Return the value of a parentheses node.
        """
        return Evaluator.process_num(values[0])

    @visit_children_decor
    def cell(self, values):
        """
        Return the value of a cell node.
        """
        try:
            if len(values) == 2:
                index = values[1].value.upper()
                sheet_name = values[0].value.strip('\'"').lower()
            else:
                sheet_name = self.sheet.display_name
                index = values[0].value.upper()

            index = index.replace("$", "")

            if not check_valid_location(index):
                return CellError(CellErrorType.BAD_REFERENCE, f"Invalid cell location {index}")

            # adding evaluation time dependencies if they are not already in the graph
            if self.from_cell: # evaluator must have a cell for this to work
                from_sheet_name = self.sheet.display_name.lower()
                from_index = self.from_cell.location
                if ((sheet_name.lower(), index) not in
                    self.workbook.interaction_graph.graph[(from_sheet_name, from_index)]):

                    self.eval_dependencies.add(((from_sheet_name, from_index),
                                                (sheet_name.lower(), index)))
                    self.workbook.interaction_graph.add_dependency((from_sheet_name, from_index),
                                                                    (sheet_name.lower(), index))

            ref_val = self.workbook.get_cell_value(sheet_name, index)

        except KeyError:
            return CellError(CellErrorType.BAD_REFERENCE, "No such sheet")

        return ref_val

    @visit_children_decor
    def add_expr(self, values):
        """
        Return the value of an addition expression node.
        """
        values[0], values[2] = (Evaluator.check_numeric(values[0]),
                                Evaluator.check_numeric(values[2]))
        e = Evaluator.values_error_helper(values)
        if e:
            return e
        if values[1] == '+':
            return Evaluator.process_num(values[0] + values[2])
        if values[1] == '-':
            return Evaluator.process_num(values[0] - values[2])
        raise ValueError("Invalid operator")

    @visit_children_decor
    def mul_expr(self, values):
        """
        Return the value of a multiplication expression node.
        """
        values[0], values[2] = (Evaluator.check_numeric(values[0]),
                                Evaluator.check_numeric(values[2]))
        e = Evaluator.values_error_helper(values)
        if e:
            return e
        if values[1] == '*':
            return Evaluator.process_num(values[0] * values[2])
        if values[1] == '/':
            if values[2] == 0:
                return CellError(CellErrorType.DIVIDE_BY_ZERO, "Divided by zero")
            return Evaluator.process_num(values[0] / values[2])
        raise ValueError("Invalid operator")

    @visit_children_decor
    def concat_expr(self, values):
        """
        Return the value of a concatenation expression node.
        """
        e = Evaluator.values_error_helper(values)
        if e:
            return e
        values[0], values[1] = (Evaluator.check_str(values[0]),
                                Evaluator.check_str(values[1]))

        return values[0] + values[1]

    @visit_children_decor
    def unary_op(self, values):
        """
        Return the value of a unary operation node.
        """
        values[1] = Evaluator.check_numeric(values[1])
        e = Evaluator.values_error_helper(values)
        if e:
            return e
        if values[0] == '+':
            return Evaluator.process_num(values[1])
        if values[0] == '-':
            return Evaluator.process_num(-values[1])
        raise ValueError("Invalid operator")

    @staticmethod
    def comp_helper(val1, val2):
        """
        Helper function for comparison operations between two values of
        potentially different types. Equal to => 0, Less than => negative, Greater
        than => positive.
        """
        if isinstance(val1, type(val2)):
            if val1 == val2:
                return 0
            return 1 if val1 > val2 else -1
        return TYPE_VALUES[type(val1)] - TYPE_VALUES[type(val2)]

    @visit_children_decor
    def comp_expr(self, values):
        """
        Return the value of a comparison expression node
        """
        e = Evaluator.values_error_helper(values)
        if e:
            return e
        if values[0] is None:
            if values[2] is not None:
                values[0] = NONE_TYPES[type(values[2])]
            else:
                values[0] = 0
                values[2] = 0
        elif values[2] is None:
            values[2] = NONE_TYPES[type(values[0])]
        values[0], values[2] = map(lambda x: x.lower() if isinstance(x, str) else x,
                                   [values[0], values[2]])
        match values[1]:
            case "=" | "==":
                result = Evaluator.comp_helper(values[0], values[2]) == 0
            case "<>" | "!=":
                result = Evaluator.comp_helper(values[0], values[2]) != 0
            case "<":
                result = Evaluator.comp_helper(values[0], values[2]) < 0
            case "<=":
                result = Evaluator.comp_helper(values[0], values[2]) <= 0
            case ">":
                result = Evaluator.comp_helper(values[0], values[2]) > 0
            case ">=":
                result = Evaluator.comp_helper(values[0], values[2]) >= 0
        return result

    def error(self, tree):
        """
        Return the value of a cell error node.
        """
        return CellError(error_dict[tree.children[0].upper()], "Error from error() str")

    def bool(self, tree):
        """
        Return the value of a boolean node.
        """
        return tree.children[0].upper() == "TRUE"


    def function(self, tree):
        """
        Return the value of a function node.
        """
        func_name = tree.children[0].upper()
        if func_name in ("IF", "IFERROR", "CHOOSE"):
            if tree.children[1] is None:
                return CellError(CellErrorType.TYPE_ERROR, "Invalid number of arguments.")
            # why .children.children?
            subtrees = tree.children[1].children
            if len(subtrees) == 0:
                return CellError(CellErrorType.TYPE_ERROR, "Invalid number of arguments.")
            first_arg = self.visit(subtrees[0])

            if func_name == "IF":
                # why is this the condition and counting number of subtrees does not work?
                if subtrees[-1] is None or len(subtrees) > 3:
                    return CellError(CellErrorType.TYPE_ERROR, "IF: Invalid number of arguments.")
                condition = self.check_bool(first_arg)
                if isinstance(condition, CellError):
                    return condition
                if condition:
                    return self.visit(subtrees[1])
                if not condition:
                    if len(subtrees) == 3:
                        return self.visit(subtrees[2])
                    if subtrees[1] is not None:
                        return False
            elif func_name == "IFERROR":
                if len(subtrees) > 2:
                    return CellError(CellErrorType.TYPE_ERROR,
                                        "IFERROR: Invalid number of arguments.")
                if isinstance(first_arg, CellError):
                    if len(subtrees) == 2:
                        if subtrees[-1] is not None:
                            return self.visit(subtrees[1])
                        return ""
                else:
                    return first_arg
            elif func_name == "CHOOSE":
                index = self.check_numeric(first_arg)
                if isinstance(index, CellError):
                    return index
                int_index = int(index)
                if int_index != index:
                    return CellError(CellErrorType.TYPE_ERROR, "CHOOSE: Index is not an integer.")
                if int_index < 1 or int_index > len(subtrees) - 1:
                    return CellError(CellErrorType.TYPE_ERROR, "CHOOSE: Index out of range.")
                if subtrees[int_index] is None:
                    return CellError(CellErrorType.TYPE_ERROR,
                                     "CHOOSE: Invalid number of arguments.")
                return self.visit(subtrees[int_index])
        else:
            values = self.visit_children(tree)
            args = values[1]
            if values[1] is not None:
                if values[1][-1] is None:
                    args = values[1][:-1]
            else:
                args = []
            # Propagate errors if necessary
            if func_name not in ["INDIRECT", "ISERROR"]:
                e_vals = Evaluator.values_error_helper(args)
                if e_vals is not None:
                    return e_vals
            # if need_to_eval is true, res is a tree that needs to be visited, otherwise it is
            # just the value. need_to_eval can be true only for if, iferror, choose, and indirect
            return self.workbook.func_dir.evaluate(func_name, args, self.workbook,
                                               self.sheet, self.from_cell, self)


@lru_cache(maxsize=None)
def cached_evaluators(wb, sheet, cell) -> Evaluator:
    """
    Cache enabled factory function for creating evaluators. Returning the same 
    evaluator for the same workbook and sheet should then allow caching of 
    results of the evaluation of formulas.
    """
    return Evaluator(wb, sheet, cell)
