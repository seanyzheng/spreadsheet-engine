"""
This file contains the performance tests of the workbook. 
"""

# import performance testing packages
import cProfile
import pstats
import io
from pstats import SortKey

# import testing packages
import sys

# pylint: disable=wrong-import-position
# Add sheets directory to Python Search PATH
sys.path.append("..")
sys.path.append(".")

# import modules to be tested
from sheets import Workbook
# pylint: enable=wrong-import-position


def test_chain(length):
    """
    Tests the performance of the workbook when the first cell of a chain of 
    cells is changed.
    """
    profiler = cProfile.Profile()
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=1")
    for i in range(2, length):
        wb.new_sheet()
        wb.set_cell_contents(f"Sheet{i}", "A1", f"=Sheet{i-1}!A1+1")
    profiler.enable()
    wb.set_cell_contents("Sheet1", "A1", "=2")
    profiler.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


def test_references_one(length):
    """
    Tests the performance of the workbook when many cells references one cell
    and the one cell is changed. 
    """
    profiler = cProfile.Profile()
    wb = Workbook()
    wb.new_sheet()
    wb.set_cell_contents("Sheet1", "A1", "=1")
    for i in range(2, length):
        wb.new_sheet()
        wb.set_cell_contents(f"Sheet{i}", "A1", "=Sheet1!A1")
    profiler.enable()
    wb.set_cell_contents("Sheet1", "A1", "=2")
    profiler.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


def test_many_references():
    """
    Tests the performance of the workbook when a lot of cells reference other cells
    and one the values of one sheet is changed. 
    """
    profiler = cProfile.Profile()
    wb = Workbook()
    cols = [chr(65 + i) for i in range(26)]
    wb.new_sheet("Sheet1")
    wb.new_sheet("Sheet2")
    cells = []
    for col in cols:
        for row in range(1, 26):
            wb.set_cell_contents("Sheet1", f"{col}{row}", f"= Sheet2!{col}{row}")
            cells.append(f"{col}{row}")
    profiler.enable()
    for cell in cells:
        wb.set_cell_contents("Sheet2", f"{cell}", "100")
    profiler.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


def test_cycle(length):
    """
    Tests the performance of the workbook when a cycle is created.
    """
    profiler = cProfile.Profile()
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "=1")
    for i in range(2, length):
        wb.new_sheet(f"Sheet{i}")
        wb.set_cell_contents(f"Sheet{i}", "A1", f"=Sheet{i-1}!A1")
    profiler.enable()
    wb.set_cell_contents("Sheet1", "A1", f"=Sheet{length}!A1")
    profiler.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


def test_make_break_cycle(length, num_breaks):
    """
    Tests the performance of the workbook when a cycle is made and broken. 
    """
    profiler = cProfile.Profile()
    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "=1")
    for i in range(2, length):
        wb.new_sheet(f"Sheet{i}")
        wb.set_cell_contents(f"Sheet{i}", "A1", f"=Sheet{i-1}!A1")
    profiler.enable()
    wb.set_cell_contents(f"Sheet{length-1}", "A1", "=Sheet1!A1")
    for _ in range(num_breaks):
        wb.set_cell_contents(f"Sheet{length-1}", "A1", "1")
        wb.set_cell_contents(f"Sheet{length-1}", "A1", "=Sheet1!A1")
    profiler.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


def test_rename():
    """
    Tests the performance of the workbook when a sheet is renamed and
    cells that reference cells in the renamed sheet are updated.
    """
    profiler = cProfile.Profile()
    wb = Workbook()
    cols = [chr(65 + i) for i in range(26)]
    wb.new_sheet("Sheet1")
    wb.new_sheet("Sheet2")
    cells = []
    for col in cols:
        for row in range(1, 26):
            wb.set_cell_contents("Sheet1", f"{col}{row}", f"= Sheet2!{col}{row}")
            cells.append(f"{col}{row}")
    profiler.enable()
    wb.rename_sheet("Sheet2", "renamed_sheet")
    profiler.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


# test_chain(10)
test_chain(100)
# test_chain(1000)

# test_references_one(10)
test_references_one(100)
# test_references_one(1000)

test_many_references()

# test_cycle(10)
test_cycle(100)
# test_cycle(1000)

# test_make_break_cycle(10, 5)
test_make_break_cycle(100, 50)
# test_make_break_cycle(1000, 500)

test_rename()
