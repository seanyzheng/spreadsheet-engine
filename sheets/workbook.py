"""
This module defines a workbook, which is a collection of spreadsheets.
Spreadsheets are stored as a dictionary of sheets, mapping sheet names to 
Spreadsheet objects. Since cells in sheets are able to reference cells in other
sheets within the same workbook, the workbook is responsible for managing the 
evaluation of formulas.
"""

from typing import List, Tuple, Optional, Callable, TextIO
from copy import deepcopy
from decimal import Decimal
import json
import re
from functools import total_ordering

from .regexp import find_refs, find_refs_absolute, has_eval_dep
from .spreadsheet import (Spreadsheet, check_valid_location, get_column_label,
                            get_row_number, column_label_to_number,
                            get_column_label_from_number)
from .cell import CellType, cached_parse
from .evaluator import cached_evaluators
from .error_types import CellErrorType, CellError, rev_error_dict
from .regexp import VALID_SHEET_NAME
from.ci_graph import CellInteractionGraph
from .func_dir import FuncDir

# Define the maximum row and column values
MAX_ROW = 9999
MAX_COLUMN = column_label_to_number('ZZZZ')
#functions that have evaluation time dependencies
EVAL_TIME_DEP_FUNCS = {"=IF", "=IFERROR", "=CHOOSE", "=INDIRECT"}

class Workbook():
    """
    A workbook is a collection of spreadsheets which may reference each other.

    Attributes:
        sheets (dict): A dictionary mapping sheet names to Spreadsheet objects.
    """

    def __init__(self):
        self.sheets = {}
        self.interaction_graph = CellInteractionGraph()
        self._notifs = []
        self.sheet_order = []
        self.func_dir = FuncDir()

    def num_sheets(self) -> int:
        """
        Returns the number of sheets in the workbook.
        """
        return len(self.sheets)

    def notify_cells_changed(self, notify_function: Callable) -> None:
        """
        Registers a function to be called whenever a cell is changed. The 
        function should return an iterable of cells that have changed.
        """
        self._notifs.append(notify_function)

    def list_sheets(self) -> list:
        """
        Returns a list of the sheet names in the workbook.
        """
        return [sheet.display_name for sheet in self.sheet_order]

    def get_sheet(self, name: str) -> Spreadsheet:
        """
        Takes in a name of a spreadsheet and returns the spreadsheet object
        matching it. Needed internally to find and edit cell objects.
        """
        return self.sheets[name.lower()]

    def _generate_unique_name(self) -> str:
        """
        Generate a unique name for a sheet. The name is always "Sheet{num}"
        where {num} is the lowest integer such that the name is unique.
        """
        base_name = "Sheet"
        index = 1
        generated_name = f"{base_name}{index}"
        while generated_name.lower() in (name.lower() for name in
                                         self.sheets):
            index += 1
            generated_name = f"{base_name}{index}"
        return generated_name

    def _check_name_valid(self, sheet_name: str) -> bool:
        """
        Takes in a string of a proposed sheet name and returns a boolean 
        indicating if it is a valid name for a spreadsheet.
        """
        try:
            assert VALID_SHEET_NAME.fullmatch(sheet_name)
            assert self.sheets.get(sheet_name.lower()) is None
            return True
        except AssertionError:
            return False

    def new_sheet(self, sheet_name: str = None) -> tuple:
        """
        Adds a new sheet to the workbook which must have a case-insensitively 
        unique name. If a name is given, it is checked for uniqueness, and 
        otherwise a unique name is generated.

        The function returns a tuple with two elements: (0-based index of sheet
        in workbook, sheet name).
        """
        if sheet_name is None:
            # If name not specified, generate a unique one
            sheet_name = self._generate_unique_name()

        else:
            # Ensure specified name is valid
            if not self._check_name_valid(sheet_name):
                raise ValueError(f'Sheet name {sheet_name} is invalid or not unique.')

        # Create a new Spreadsheet object and add to the sheets dictionary
        new_sheet = Spreadsheet(sheet_name)
        self.sheets[sheet_name.lower()] = new_sheet

        # Append the new Spreadsheet object to the sheet_order list
        self.sheet_order.append(new_sheet)

        # Update cells if necessary
        self.update_cells(set(), set())

        # Return the index and name of the new sheet
        return len(self.sheet_order) - 1, new_sheet.display_name


    def del_sheet(self, sheet_name: str) -> None:
        """
        Deletes the sheet with the specified name from the workbook. Needs to 
        reevaluate cells in case any cells in workbook are dependent on some of 
        the deleted cells.
        """
        # Delete the sheet
        # Convert the sheet name to lowercase for case-insensitive matching
        lower_sheet_name = sheet_name.lower()

        # Check if the sheet exists in the workbook
        if lower_sheet_name not in self.sheets:
            raise KeyError(f"Sheet '{sheet_name}' not found.")

        # Remove the sheet from the sheets dictionary
        del self.sheets[lower_sheet_name]

        # Find and remove the corresponding Spreadsheet object from sheet_order
        sheet_to_remove = None
        for sheet in self.sheet_order:
            if sheet.display_name.lower() == lower_sheet_name:
                sheet_to_remove = sheet
                break

        if sheet_to_remove:
            self.sheet_order.remove(sheet_to_remove)

        # Collect those cells which were deleted and lived in the dependency
        # graph and remove them from the graph
        to_remove = []
        for cell in self.interaction_graph.get_cells():
            if cell[0] == sheet_name.lower():
                to_remove.append(cell)
        for cell in to_remove:
            self.interaction_graph.remove_cell(cell)

        # Update any cells whose values may have changed
        self.update_cells(set(), set())

    def rename_sheet(self, sheet_name: str, new_sheet_name: str) -> None:
        """
        Renames the specified sheet in the workbook to the new name and
        automatically updates all formulas referencing the sheet.
        """
        # Fetch the given sheet from the workbook, or raise a KeyError if not
        # found
        sheet = self.get_sheet(sheet_name)

        # Ensure that the given sheet name is valid or throw a ValueError
        try:
            assert self._check_name_valid(new_sheet_name)
        except AssertionError as exc:
            raise ValueError(f'Sheet name {new_sheet_name} is invalid or not' +
                             ' unique.') from exc

        # Rename the sheet and update the sheets dictionary
        sheet.display_name = new_sheet_name
        self.sheets[new_sheet_name.lower()] = sheet
        del self.sheets[sheet_name.lower()]

        # Use the reference graph to update all cells that reference the sheet
        self.interaction_graph.rename_sheet(self, sheet_name, new_sheet_name)

        # Update the cells in the graph in case a rename has repaired a bad ref
        self.update_cells(set(), set())

    def move_sheet(self, sheet_name: str, index: int) -> None:
        """Move the specified sheet to the specified index in the workbook's ordered 
        sequence of sheets. The index ranges from 0 to workbook.num_sheets() - 1. 
        The index is interpreted as if the specified sheet were removed from the 
        list of sheets, and then re-inserted at the specified index.

        The sheet name match is case-insensitive; the text must match but the 
        case does not have to. If the specified sheet name is not found, a KeyError 
        is raised. If the index is outside the valid range, an IndexError is raised."""
        if sheet_name.lower() not in self.sheets:
            raise KeyError(f"Sheet '{sheet_name}' not found.")
        if not 0 <= index < len(self.sheet_order):
            raise IndexError("Index out of range.")

        # Find the sheet object
        sheet = self.sheets[sheet_name.lower()]

        # Remove the sheet object from its current position and insert it at the new index
        self.sheet_order.remove(sheet)
        self.sheet_order.insert(index, sheet)

    def copy_sheet(self, sheet_name: str) -> Tuple[int, str]:
        """Make a copy of the specified sheet, storing the copy at the end of the 
        workbook's sequence of sheets. The copy's name is generated by appending 
        "_1", "_2", ..., incrementing the number until a unique name is found. 
        Uniqueness is determined in a case-insensitive manner.

        The sheet name match is case-insensitive; the text must match but the 
        case does not have to. The copy is added to the end of the sequence of 
        sheets in the workbook. This function returns a tuple with two elements: 
        (0-based index of copy in workbook, copy sheet name), allowing the function 
        to report the new sheet's name and index in the sequence of sheets.

        If the specified sheet name is not found, a KeyError is raised."""

        if sheet_name.lower() not in self.sheets:
            raise KeyError(f"Sheet '{sheet_name}' not found.")

        # Generate a unique name for the copy
        index = 1
        copy_name = f"{sheet_name}_{index}"
        while copy_name.lower() in [sheet.display_name.lower() for sheet in
                                    self.sheet_order]:
            index += 1
            copy_name = f"{sheet_name}_{index}"

        # Copy the sheet and add to the workbook
        original_sheet = self.sheets[sheet_name.lower()]
        copied_sheet = deepcopy(original_sheet)
        copied_sheet.display_name = copy_name
        self.sheets[copy_name.lower()] = copied_sheet
        self.sheet_order.append(copied_sheet)

        changed_cells  = set()

        # Add all populated cells in the copied sheet to the interaction graph
        for cell in copied_sheet.get_cells():
            changed_cells.add((copy_name.lower(), cell.upper()))
            cell_obj = copied_sheet.get_cell(cell)
            if cell_obj.get_type() == CellType.FORMULA:
                self.interaction_graph.set_cell((copy_name.lower(), cell))
                dependencies = find_refs(cell_obj.get_content())
                for dep in dependencies[1]:
                    self.interaction_graph.add_dependency((copy_name.lower(),
                                                            cell), (dep[0].lower(),
                                                                    dep[1].upper()))
                for dep in dependencies[0]:
                    self.interaction_graph.add_dependency((copy_name.lower(),
                                                            cell), (copy_name.lower(),
                                                                    dep.upper()))

        # Update the cells in the graph in case a rename has repaired a bad ref
        self.update_cells(changed_cells, changed_cells)

        return len(self.sheet_order) - 1, copy_name


    def get_sheet_extent(self, sheet_name: str) -> tuple:
        """
        Returns a tuple (num-cols, num-rows) indicating the current extent of
        the specified spreadsheet.
        """
        return self.get_sheet(sheet_name).get_extent()

    def set_content_helper(self, sheet_name: str, location: str,
                           contents: str) -> None:
        """
        This method is used to set the contents of a cell without then evaluating
        the full workbook. This is used both for setting the contents of a particular
        cell and for setting the contents of cells during move copy and load 
        operations. In each instance, update_cells needs to be called after to 
        reevaluate the workbook.
        """
        # If the cell was previously a formula, we need to remove it from the
        # interaction graph
        if self.get_cell_type(sheet_name, location) == CellType.FORMULA:
            self.interaction_graph.remove_cell((sheet_name.lower(),
                                                 location.upper()))

        # Create a set to keep track of changed cells
        changed_cells = set()
        prev_val = self.get_cell_value(sheet_name, location)

        spreadsheet = self.get_sheet(sheet_name)
        spreadsheet.set_cell_contents(location.upper(), contents)

        if spreadsheet.get_cell_type(location.upper()) == CellType.FORMULA:
            cell = spreadsheet.get_cell(location.upper())

            # Cell is a formula, so add to the dependency graph
            self.interaction_graph.set_cell((sheet_name.lower(),
                                            location.upper()))

            # for functions with eval time dependencies (IF, IFERROR, CHOOSE, INDIRECT)
            # we only want to add the static dependencies
            if cell.get_content().split("(")[0].upper() in EVAL_TIME_DEP_FUNCS:
                # for all these functions, the static dependencies will be the first arg
                # cut off everything except first arg to be fed into regex
                contents = contents.split(",")[0]
            # Use regexps to find all static references in the formula
            inds, refs = find_refs(contents)

            # Add all visited locations to cell ref graph
            for ind in inds:
                self.interaction_graph.add_dependency((sheet_name.lower(),
                                                        location.upper()),
                                                        (cell.sheet.display_name.lower(),
                                                        ind.upper()))
            for ref in refs:
                self.interaction_graph.add_dependency((sheet_name.lower(),
                                                        location.upper()),
                                                        (ref[0].lower(),
                                                        ref[1].upper()))
        # If the value of the cell has changed, add to set of changed cells
        if prev_val != self.get_cell_value(sheet_name, location):
            changed_cells.add((sheet_name.lower(), location.upper()))
        return changed_cells

    def set_cell_contents(self, sheet_name: str, location: str,
                          contents: str) -> None:
        """
        Sets the contents of the specified cell on the specified sheet.
        """
        # Set the value of the cell
        changed_cells = self.set_content_helper(sheet_name, location, contents)
        # Update any cells whose values may have changed
        self.update_cells(set([(sheet_name.lower(), location.upper())]), changed_cells)

    def get_cell_contents(self, sheet_name: str, location: str) -> Optional[str]:
        """
        Returns the contents of the specified cell on the specified sheet.
        """
        spreadsheet = self.get_sheet(sheet_name)
        return spreadsheet.get_cell_contents(location.upper())

    def get_cell_value(self, sheet_name: str, location: str) -> Optional[str]:
        """
        Returns the value of the specified cell on the specified sheet.
        """
        spreadsheet = self.get_sheet(sheet_name)
        return spreadsheet[location.upper()]

    def get_cell_type(self, sheet_name: str, location: str) -> Optional[str]:
        """
        Returns the type of the specified cell on the specified sheet.
        """
        try:
            spreadsheet = self.get_sheet(sheet_name)
            return spreadsheet.get_cell_type(location.upper())
        except KeyError:
            return None

    def update_cells(self, changed_cont_cells, changed_val_cells) -> None:
        """
        This method is called any time when the value of cells may have 
        changed and all cells need to be updated accordingly.
        """
        # list of edges added at evaluation time to be removed after evaluation
        eval_time_edges = set()
        # this flag will be set to false once we don't observe any changes in the graph
        # i.e. no new edges are added at evaluation time

        continue_tarjan_and_eval = True
        num_while = 0
        while continue_tarjan_and_eval:
            num_while += 1
            #flag will be set to true if we add any new edges at evaluation time
            continue_tarjan_and_eval = False

        # Use Tarjans algorithm to compute ordering and check for cycles
            topo_order, nodes_in_cycle, scc_nodes = self.interaction_graph.tarjan()
            # This flag indicates whether we have found the first node in the
            # topological ordering which needs to be updated
            # Update cells in topological order
            found_first = False
            for cell_name in topo_order:

                # Try to find the specified cell
                try:
                    loc = cell_name[0]
                    index = cell_name[1]
                    cell = self.get_sheet(loc).get_cell(index.upper())

                # If fails, then cell doesn't exist
                except KeyError:
                    continue

                prev_value = cell.get_value() if cell is not None else None
                eval_deps = has_eval_dep(cell.get_content()) if cell is not None else False

                found_first = (found_first or len(changed_cont_cells) == 0
                           or cell_name in changed_cont_cells or
                           eval_deps)

                # If cell indicated as head of cycle or in and scc, set value to CIRCREF error
                if cell_name in nodes_in_cycle or cell_name in scc_nodes:
                    cell.set_value(CellError(CellErrorType.CIRCULAR_REFERENCE,
                                            "Cycle Detected"))
                    found_first = True

                # If cell is a formula, evaluate
                else:
                    # Only update if cells before in topo order are changed
                    if not cell is None:
                        if found_first:
                            if cell.get_type() == CellType.FORMULA:
                                evaluator = cached_evaluators(self, cell.sheet, cell)
                                val = evaluator.visit(cached_parse(cell.get_content()))
                                if val is None:
                                    val = Decimal(0)
                                cell.set_value(val)
                                # if the evaluator has new eval time
                                # dependencies, we need to continue
                                if len(evaluator.get_eval_dependencies()) > 0:
                                    eval_time_edges.update(
                                        evaluator.get_eval_dependencies())
                                    evaluator.reset_eval_dependencies()
                                    continue_tarjan_and_eval = True

                # If the value of the cell has changed, add to set of changed cells
                if cell is not None and prev_value != cell.get_value():
                    changed_val_cells.add((loc, index))

        # Call all registered notification functions on the updated cells
        if len(changed_val_cells) > 0:
            for func in self._notifs:
                try:
                    func(self, list(changed_val_cells))
                # Here we do not know what function a user may pass in and what
                # exceptions it may raise, so we catch all exceptions to protect
                # the state of the workbook
                except: # pylint: disable=bare-except
                    continue
        for cell, dependency in eval_time_edges:
            self.interaction_graph.remove_dependency(cell, dependency)

    @staticmethod
    def load_workbook(fp: TextIO) -> 'Workbook':
        """
        This is a static method (not an instance method) to load a workbook
        from a text file or file-like object in JSON format, and return the
        new Workbook instance.  Note that the _caller_ of this function is
        expected to have opened the file; this function merely reads the file.
        
        If the contents of the input cannot be parsed by the Python json
        module then a json.JSONDecodeError should be raised by the method.
        (Just let the json module's exceptions propagate through.)  Similarly,
        if an IO read error occurs (unlikely but possible), let any raised
        exception propagate through.
        
        If any expected value in the input JSON is missing (e.g. a sheet
        object doesn't have the "cell-contents" key), raise a KeyError with
        a suitably descriptive message.
        
        If any expected value in the input JSON is not of the proper type
        (e.g. an object instead of a list, or a number instead of a string),
        raise a TypeError with a suitably descriptive message.
        """
        json_data = json.load(fp)
        wb = Workbook()
        # make sure there is sheets is the only key
        if len(json_data) != 1 or "sheets" not in json_data:
            raise KeyError("There must be exactly one key in the json object, called \'sheets\' ")
        # make sure its a list
        if not isinstance(json_data["sheets"], list):
            raise TypeError("Collection of sheets in workbook must be represented as json list")
        # Collect changed cells
        changed_cells = set()
        for sheet in json_data["sheets"]:
            # make sure its a dictionary
            if not isinstance(sheet, dict):
                raise TypeError("Sheet must be represented as json dictionary")
             # make sure name and cell_contents are the only keys
            if len(sheet) != 2 or "name" not in sheet or "cell-contents" not in sheet:
                raise KeyError("Sheet must have exactly two keys, \'name\' and \'cell-contents\'")
            # make sure name is a string
            if not isinstance(sheet["name"], str):
                raise TypeError("Sheet name must be a string")
            #make sure cell-contents is a dictionary
            if not isinstance(sheet["cell-contents"], dict):
                raise TypeError("Cells must be represented must as a json object")
            wb.new_sheet(sheet["name"])
            for location, contents in sheet["cell-contents"].items():
                # make sure contents is a string
                if not isinstance(contents, str):
                    raise TypeError("Cell contents must be a string")
                # make sure location is a valid
                assert check_valid_location(location)
                changed_cells.update(wb.set_content_helper(sheet["name"],
                                                           location.upper(), contents))
        wb.update_cells(changed_cells, changed_cells)
        return wb

    def save_workbook(self, fp: TextIO) -> None:
        """
        Instance method (not a static/class method) to save a workbook to a
        text file or file-like object in JSON format.  Note that the _caller_
        of this function is expected to have opened the file; this function
        merely writes the file.
        
        If an IO write error occurs (unlikely but possible), let any raised
        exception propagate through.
        """
        to_json = {"sheets": []}
        for sheet in self.sheets.values():
            to_json["sheets"].append({"name": sheet.display_name, "cell-contents": {}})
            for location in sheet.get_cells():
                if not check_valid_location(location):
                    raise ValueError(f"Invalid cell location {location}")
                cell = sheet.get_cell(location)
                to_json["sheets"][-1]["cell-contents"][location.upper()] = cell.get_content()
        json.dump(to_json, fp)

    def _validate_cell_location(self, location: str) -> Tuple[int, int]:
        """
        Validates that a given cell location is valid within the given sheet.

        Args:
        sheet_name (str): The name of the sheet.
        location (str): The cell location to validate.

        Returns:
        Tuple[int, int]: A tuple containing the row and column index.

        Raises:
        ValueError: If the location is invalid.
        """
        if not check_valid_location(location):
            raise ValueError(f"Invalid cell location: {location}")

        # Convert the cell location into row and column indices
        row, col = get_row_number(location), column_label_to_number(get_column_label(location))

        return row, col

    def _validate_and_get_offset(self, sheet_name: str, start_location: str,
                                 end_location: str, to_location: str) -> Tuple[int, int]:
        """
        Validates the cell locations and calculates the offset for moving or copying cells,
        adjusting the sheet's extent if the target area is out of bounds.

        Args:
        sheet_name (str): The name of the sheet.
        start_location (str): The starting cell location of the block.
        end_location (str): The ending cell location of the block.
        to_location (str): The top-left cell location of the target block.

        Returns:
        Tuple[int, int]: The row and column offset.
        """
        # Validate the locations
        start_row, start_col = self._validate_cell_location(start_location)
        end_row, end_col = self._validate_cell_location(end_location)
        to_row, to_col = self._validate_cell_location(to_location)

        # Calculate the extent of the target location and adjust sheet's extent if necessary
        sheet = self.get_sheet(sheet_name)
        num_rows, num_cols = sheet.get_extent()

        target_end_row = to_row + (end_row - start_row)
        target_end_col = to_col + (end_col - start_col)

        # Adjust the sheet's max rows and columns if the target area is out of bounds
        if target_end_row > num_rows or target_end_col > num_cols:
            new_max_row = max(target_end_row, num_rows)
            new_max_col = max(target_end_col, num_cols)
            sheet.adjust_extent(new_max_row, new_max_col)

        # Compute the row and column offsets
        row_offset = to_row - start_row
        col_offset = to_col - start_col

        return row_offset, col_offset

    def _move_copy_cells_helper(self, sheet_name: str, start_location: str,
                                end_location: str, to_location: str,
                                to_sheet: Optional[str] = None,
                                is_move: Optional[bool] = True) -> None:
        """
        Helper function to move or copy a group of cells from the specified starting
        location to the specified ending location and updates the workbook accordingly.
        Handles cases where the start and end locations are reversed.
        """
        start_location = start_location.upper()
        end_location = end_location.upper()
        to_location = to_location.upper()

        # Validate and get offset
        row_offset, col_offset = self._validate_and_get_offset(sheet_name,
                                                            start_location,
                                                            end_location,
                                                            to_location)

        # Calculate the range of cells to move or copy
        start_row, start_col = (get_row_number(start_location),
                                column_label_to_number(get_column_label(start_location)))
        end_row, end_col = (get_row_number(end_location),
                            column_label_to_number(get_column_label(end_location)))

        # Ensure the start is top-left and the end is bottom-right
        top_left_row, bottom_right_row = min(start_row, end_row), max(start_row, end_row)
        top_left_col, bottom_right_col = min(start_col, end_col), max(start_col, end_col)

        # Adjust the target range based on the top-left cell
        to_row, to_col = (get_row_number(to_location),
                          column_label_to_number(get_column_label(to_location)))

        # Determine the target sheet (could be the same as source)
        target_sheet_name = to_sheet if to_sheet else sheet_name
        target_sheet = self.get_sheet(target_sheet_name)

        # Calculate the destination range
        dest_start_row = to_row
        dest_start_col = to_col
        dest_end_row = to_row + (bottom_right_row - top_left_row)
        dest_end_col = to_col + (bottom_right_col - top_left_col)

        # Check for overlap
        overlap = not (dest_end_row < top_left_row or
                       dest_start_row > bottom_right_row or
                        dest_end_col < top_left_col or
                        dest_start_col > bottom_right_col)

        # Store overlapping cells temporarily if there's an overlap
        temp_storage = {}
        if overlap:
            for row in range(max(top_left_row, dest_start_row),
                             min(bottom_right_row, dest_end_row) + 1):
                for col in range(max(top_left_col, dest_start_col),
                                 min(bottom_right_col, dest_end_col) + 1):
                    original_loc = get_column_label_from_number(col) + str(row)
                    temp_storage[original_loc] = self.get_cell_contents(sheet_name,
                                                                        original_loc)

        # Adjust the target sheet's extent if necessary
        target_sheet.adjust_extent(dest_end_row, dest_end_col)

        moved_cells = set()  # Keep track of moved cells to avoid clearing them

        # Keep track of changed cells
        changed_cells = set()

        # Move or copy cells, updating references and handling overlaps
        for row in range(top_left_row, bottom_right_row + 1):
            for col in range(top_left_col, bottom_right_col + 1):
                original_loc = get_column_label_from_number(col) + str(row)
                new_row = row + row_offset - (top_left_row - start_row)
                new_col = col + col_offset - (top_left_col - start_col)
                new_loc = get_column_label_from_number(new_col) + str(new_row)
                changed_cells.add((target_sheet_name.lower(), new_loc.upper()))

                if temp_storage.get(original_loc) is not None:
                    # Use stored data for overlapping cells
                    cell_content = temp_storage[original_loc]
                else:
                    cell_content = self.get_cell_contents(sheet_name, original_loc)

                if self.get_cell_type(sheet_name, original_loc) == CellType.FORMULA:
                    # Update formula references for all moved or copied cells
                    updated_formula = self.update_formula_references(cell_content,
                                                                     row_offset,
                                                                     col_offset)
                    self.set_content_helper(target_sheet_name, new_loc,
                                            updated_formula)
                else:
                    self.set_content_helper(target_sheet_name, new_loc,
                                            cell_content)
                moved_cells.add(original_loc)
        # Clear original cells, excluding overlapping cells if moving
        if is_move:
            for original_loc in moved_cells:
                if original_loc not in temp_storage:
                    changed_cells.update(self.set_content_helper(sheet_name,
                                                                 original_loc,
                                                                 None))
        # Update any cells whose values may have changed
        self.update_cells(changed_cells, changed_cells)


    def move_cells(self, sheet_name: str,
                   start_location: str, # pylint-ignore=too-many-arguments
                   end_location: str, to_location: str,
                   to_sheet: Optional[str] = None) -> None:
        """
        Moves a group of cells from the specified starting location to the 
        specified ending location and updates the workbook accordingly.
        """
        self._move_copy_cells_helper(sheet_name, start_location, end_location,
                                     to_location, to_sheet)

    def copy_cells(self, sheet_name: str, start_location: str,
                end_location: str, to_location: str,
                to_sheet: Optional[str] = None) -> None:
        """
        Copies a group of cells from the specified starting location to the
        specified ending location and updates the workbook accordingly.
        """
        self._move_copy_cells_helper(sheet_name, start_location, end_location,
                                    to_location, to_sheet, False)


    def update_cell_reference(self, cell_ref: str, row_offset: int,
                              col_offset: int) -> str:
        """
        Calculates the new cell reference based on the given offsets and returns
        either the updated reference or a #REF! if out of bounds.
        """
        error = "#REF!"
        match = re.match(r'(\$?)([A-Za-z]+)(\$?)(\d+)', cell_ref)
        if not match:
            return cell_ref  # Return the original ref if it doesn't match
        # expected pattern

        absolute_col, col_label, absolute_row, row_num = match.groups()
        # Convert column label to number, apply offset if not absolute, and
        # convert back to label
        if not absolute_col:
            col_num = column_label_to_number(col_label) + col_offset
        else:
            col_num = column_label_to_number(col_label)

        if not absolute_row:
            new_row_num = int(row_num) + row_offset
        else:
            new_row_num = int(row_num)

        # Check if the new location is out of bounds
        if (col_num > MAX_COLUMN or col_num < 1 or new_row_num > MAX_ROW or
            new_row_num < 1):
            return f'{error}'
        new_col_label = (get_column_label_from_number(col_num) if not
                         absolute_col else col_label)
        return f'{absolute_col}{new_col_label}{absolute_row}{new_row_num}'

    def update_formula_references(self, formula: str, row_offset: int,
                                  col_offset: int) -> str:
        """
        Updates all cell references within the given formula based on the
        provided row and column offsets.
        """
        # Find all references in the formula
        indices, _ = find_refs_absolute(formula)

        # Process each reference to calculate its new location
        updated_formula = formula
        for index in indices:
            # Calculate the new cell reference based on the offset
            new_ref = self.update_cell_reference(index, row_offset, col_offset)
            # Replace the old reference with the new one in the formula
            updated_formula = updated_formula.replace(index, new_ref)

        # Return the formula with updated references
        return updated_formula


    def sort_region(self, sheet_name: str, start_location: str,
                    end_location: str, sort_cols: List[int]):
        """
        Sort a region in the workbook based on the specified columns and updates
        the workbook accordingly.
        """
        # Validate the sheet name and get the sheet object
        if sheet_name.lower() not in self.sheets:
            raise KeyError(f"Sheet '{sheet_name}' not found.")
        sheet = self.get_sheet(sheet_name)

        # Validate start_location and end_location
        start_row, start_col = self._validate_cell_location(start_location)
        end_row, end_col = self._validate_cell_location(end_location)

        # Ensure start_location is the top-left and end_location is the
        # bottom-right
        top_left_row = min(start_row, end_row)
        bottom_right_row = max(start_row, end_row)
        top_left_col = min(start_col, end_col)
        bottom_right_col = max(start_col, end_col)

        # Validate sort_cols
        if not sort_cols or any(abs(col) == 0 or abs(col) >
                                (bottom_right_col - top_left_col + 1)
                                for col in sort_cols):
            raise ValueError("Invalid sort_cols list.")

        # Check for duplicate columns in sort_cols, considering absolute values
        # for sorting direction
        if len(set(abs(col) for col in sort_cols)) != len(sort_cols):
            raise ValueError("Duplicate columns in sort_cols list.")

        # Logic to handle the sorting, including error and blank cells
        temp_storage = []
        for row in range(top_left_row, bottom_right_row + 1):
            row_data = [self.get_cell_value(sheet_name,
                                            get_column_label_from_number(col)
                                            + str(row))
                        for col in range(top_left_col, bottom_right_col + 1)]
            temp_storage.append(SortableRow(row, row_data, sort_cols))

        sorted_rows = sorted(temp_storage)

        # Reinsert sorted rows
        changed_cells = set()
        for new_row_idx, sortable_row in enumerate(sorted_rows):
            _, row_data = sortable_row.row_index, sortable_row.row_data
            for col_idx, cell_value in enumerate(row_data):
                new_location = (get_column_label_from_number(top_left_col
                                                             + col_idx)
                                + str(top_left_row + new_row_idx))

                # Convert cell_value to a string if it's not already one
                if not isinstance(cell_value, str):
                    if isinstance(cell_value, CellError):
                        cell_value = rev_error_dict[cell_value.get_type()]
                    cell_value = str(cell_value)
                if cell_value == "None":
                    cell_value = ""
                changed_cells.update(self.set_content_helper(sheet.display_name,
                                                             new_location,
                                                             cell_value))

        # Update formulas in sorted rows
        for new_row_idx, sortable_row in enumerate(sorted_rows):
            original_row_idx = sortable_row.row_index
            for col_idx, cell_value in enumerate(sortable_row.row_data):
                original_location = (get_column_label_from_number(top_left_col +
                                                                  col_idx) +
                                                                  str(
                                                                    original_row_idx))
                new_location = (get_column_label_from_number(top_left_col +
                                                             col_idx) +
                                                             str(top_left_row +
                                                                 new_row_idx))

                # Calculate offsets for formula updates
                row_offset = new_row_idx - (original_row_idx - top_left_row)
                col_offset = 0

                original_formula = sheet.get_cell_contents(original_location)
                if original_formula is not None and original_formula.startswith("="):
                    updated_formula = self.update_formula_references(
                        original_formula, row_offset, col_offset)
                    changed_cells.update(self.set_content_helper(
                        sheet_name, new_location, updated_formula))

        self.update_cells(changed_cells, changed_cells)


@total_ordering
class SortableRow:
    """
    Defines a sortable row object for use in sorting a region of cells.
    """
    def __init__(self, row_index, row_data, sort_cols):
        """
        Initializes a SortableRow instance.
        :param row_index: The original index of the row in the spreadsheet.
        :param row_data: A list of evaluated cell values for the row.
        :param sort_cols: A list of column indices (1-based) and their sort order. 
                          Positive for ascending, negative for descending.
        :param sheet: The sheet object, to access cell values.
        """
        self.row_index = row_index
        self.sort_cols = sort_cols
        self.row_data = row_data


    def __lt__(self, other):
        """
        Less-than comparison method for sorting. Compares this row to another
        based on sort_cols.

        :param other: Another SortableRow instance to compare against.
        """
        for col in self.sort_cols:
            col_index = abs(col) - 1  # Convert to 0-based index
            ascending = col > 0
            self_val = self.row_data[col_index]
            other_val = other.row_data[col_index]

            comparison_result = self.compare_values(self_val, other_val,
                                                    ascending)
            if comparison_result != 0:
                return comparison_result < 0
        return False  # Rows are considered equal; maintain original order for
                        # stability

    def __eq__(self, other):
        """
        Equality comparison method. Considers rows equal if all sort column
        values are equal.

        :param other: Another SortableRow instance to compare against.
        """
        return all(self.row_data[abs(col) - 1] == other.row_data[abs(col) - 1]
                   for col in self.sort_cols)

    @staticmethod
    def compare_values(val1, val2, ascending=True):
        """
        Compares two values for sorting, handling None, empty string, and
        CellError values.
        """
        # Special handling for blank values (None or empty string)
        if (val1 is None or val1 == "") and (val2 is None or val2 == ""):
            return 0
        if val1 is None or val1 == "":
            return -1 if ascending else 1
        if val2 is None or val2 == "":
            return 1 if ascending else -1

        # Existing logic for handling error values
        if isinstance(val1, CellError) and isinstance(val2, CellError):
            return ((val1.get_type().value > val2.get_type().value) -
                    (val1.get_type().value < val2.get_type().value)
                    if ascending else (val2.get_type().value >
                                       val1.get_type().value) -
                                       (val2.get_type().value <
                                        val1.get_type().value))
        if isinstance(val1, CellError):
            return -1 if ascending else 1
        if isinstance(val2, CellError):
            return 1 if ascending else -1

        # Normal comparison logic for non-blank, non-error values
        try:
            return ((val1 > val2) - (val1 < val2) if ascending else
                    (val2 > val1) - (val2 < val1))
        except TypeError:
            # Fallback for comparing non-comparable types
            return ((str(val1) > str(val2)) -
                    (str(val1) < str(val2)) if ascending else
                    (str(val2) > str(val1)) - (str(val2) < str(val1)))
