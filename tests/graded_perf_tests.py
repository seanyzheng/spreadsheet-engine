"""
Replicates the graded CS130 performance tests described on the website and runs 
them with a profiler to understand and predict the performance of the engine 
on the test cases.
"""

import time
import cProfile
import pstats
import io
from io import StringIO
import sys
from decimal import Decimal

# pylint: disable=wrong-import-position
# Add sheets directory to Python Search PATH
sys.path.append("..")
sys.path.append(".")

# import modules to be tested
import sheets
from sheets import Workbook
# pylint: enable=wrong-import-position

# Preallocate string IO to collect all performance outputs
OUT = io.StringIO()

# Utility functions
def generate_column_keys(n):
    """
    Generates the first n spreadsheet column keys.

    Args:
    - n (int): Number of column keys to generate.

    Returns:
    - list: List of column keys.
    """
    keys = []
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    # Generate column keys up to 'Z'
    for i in range(min(n, 26)):
        keys.append(alphabet[i])

    if n <= 26:
        return keys

    # Generate column keys beyond 'Z'
    for i in range(26, n):
        key = ''
        quotient = i // 26
        remainder = i % 26

        if quotient == 0:
            key += alphabet[remainder - 1]
        else:
            key += alphabet[quotient - 1] + alphabet[remainder]
        keys.append(key)

    return keys


def fibonnaci_num(n):
    """
    Computes the nth fibonnaci number
    """
    a, b = Decimal(0), Decimal(1)
    for _ in range(n):
        a, b = b, a + b
    return a


def long_chain(num: int = 1000, to_set: str = "=1", expected: int = 1000):
    """
    creates a single long row of cells, each dependent on the prior cell. For
    example, A2 is set to =A1+1, A3 is set to =A2+1, and so forth. Then we set
    cell A1 to some value, and verify that the values have successfully
    propagated through the chain. This kind of test is good for both cell
    updates and cycles, depending on what you set A1 to.
    """
    # Pre-generate formulas to store in chained cells
    formulas = []
    for i in range(2, num+1):
        formulas.append(("Sheet1", f"A{i}", f"=A{i-1}+1"))

    # Setup the profiler
    profiler = cProfile.Profile()
    profiler.enable()


    # Setup by creating a workbook and setting the generated formulas
    start_t = time.time()
    wb = Workbook()
    wb.new_sheet()
    for formula in formulas:
        wb.set_cell_contents(*formula)

    # Set the head of the chain and time/verify the propagation
    wb.set_cell_contents("Sheet1", "A1", to_set)
    end_t = time.time()
    profiler.disable()

    profiler_save = cProfile.Profile()
    profiler_save.enable()
    start_t_save = time.time()
    file = StringIO()
    wb.save_workbook(file)
    file.seek(0)
    wb2 = sheets.Workbook.load_workbook(file)
    end_t_save = time.time()
    profiler_save.disable()

    # Verify the value propagated
    assert wb.get_cell_value("Sheet1", f"A{num}") == expected
    assert wb2.get_cell_value("Sheet1", f"A{num}") == expected

    # Output the performance results
    OUT.write("---------- LONG CHAIN RESULTS ----------\n")
    OUT.write(f"Total Time: {end_t - start_t}\n")
    sortby = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=OUT).sort_stats(sortby)
    ps.print_stats()

    OUT.write("---------- SAVE/LOAD RESULTS ----------\n")
    OUT.write(f"Total Time: {end_t_save - start_t_save}\n")
    sortby_save = pstats.SortKey.CUMULATIVE
    ps_save = pstats.Stats(profiler_save, stream=OUT).sort_stats(sortby_save)
    ps_save.print_stats()



def m_n_row_mesh(m: int = 20, n: int = 50, to_set: str = "5", expected: int = 54):
    """
    sets up an M-row mesh, where each row has an N-cell-long chain of cells.
    Each chain starts with a formula that reads A1, and each cell in the chain
    does some simple operation like = _previous_cell_ + 1. At the end of all the
    rows, a single cell sums the outputs of all rows. This can be used for
    testing both updates and cycles, depending on what A1 is set to.
    """
    # Pre-generate formulas to store in chained cells
    formulas = []
    n_cols = generate_column_keys(n)
    for i in range(1, m+1):
        for col_num, col in enumerate(n_cols):
            if col == "A":
                formulas.append(("Sheet1", f"{col}{i}", "=A1"))
            else:
                formulas.append(("Sheet1", f"{col}{i}",
                                 f"={n_cols[col_num - 1]}{i}+1"))

    # Setup the profiler
    profiler = cProfile.Profile()
    profiler.enable()

    # Setup by creating a workbook and setting the generated formulas
    start_t = time.time()
    wb = Workbook()
    wb.new_sheet()
    for formula in formulas:
        wb.set_cell_contents(*formula)

    # Set A1 and propagate values through the mesh
    wb.set_cell_contents("Sheet1", "A1", to_set)

    end_t = time.time()
    profiler.disable()

    profiler_copy = cProfile.Profile()
    profiler_copy.enable()
    for i in range(1, m+1):
        assert wb.get_cell_value("Sheet1", f"{n_cols[-1]}{i}") == expected

    start_t_copy = time.time()
    _, name = wb.copy_sheet('Sheet1')
    end_t_copy = time.time()
    profiler_copy.disable()

    profiler_rename = cProfile.Profile()
    profiler_rename.enable()
    start_t_rename = time.time()
    wb.rename_sheet("Sheet1", "renamed_sheet")
    end_t_rename = time.time()
    profiler_rename.disable()

    # Verify the value propagated in each chain

    for i in range(1, m+1):
        assert wb.get_cell_value(f"{name}", f"{n_cols[-1]}{i}") == expected

    for i in range(1, m+1):
        assert wb.get_cell_value("renamed_sheet", f"{n_cols[-1]}{i}") == expected


    # Output the performance results
    OUT.write("---------- MxN ROW MESH RESULTS ----------\n")
    OUT.write(f"Total Time: {end_t - start_t}\n")
    sortby = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=OUT).sort_stats(sortby)
    ps.print_stats()

    OUT.write("---------- COPY SHEET RESULTS ----------\n")
    OUT.write(f"Total Time: {end_t_copy - start_t_copy}\n")
    sortby_copy = pstats.SortKey.CUMULATIVE
    ps_copy = pstats.Stats(profiler_copy, stream=OUT).sort_stats(sortby_copy)
    ps_copy.print_stats()

    OUT.write("---------- RENAME SHEET RESULTS ----------\n")
    OUT.write(f"Total Time: {end_t_rename - start_t_rename}\n")
    sortby_rename = pstats.SortKey.CUMULATIVE
    ps_rename = pstats.Stats(profiler_rename, stream=OUT).sort_stats(sortby_rename)
    ps_rename.print_stats()

#pylint: disable=too-many-statements
def fibonacci(n:int = 1000):
    """
    A1 is set to 1, A2 is set to 1, A3 is set to =A1+A2, A4 is set to =A2+A3,
    and so forth, as long as we want.
    """
    # Pre-compute the expected nth fibonnacci number
    expected = fibonnaci_num(n)

    # Pre-generate formulas to store in chained cells
    formulas = [("Sheet1", "A2", "1")]
    for i in range(3, n+1):
        formulas.append(("Sheet1", f"A{i}", f"=A{i-2}+A{i-1}"))

    # Setup the profiler
    profiler = cProfile.Profile()
    profiler.enable()

    # Setup by creating a workbook and setting the generated formulas
    start_t = time.time()
    wb = Workbook()
    wb.new_sheet()
    for formula in formulas:
        wb.set_cell_contents(*formula)

    # Set A1 and propagate values through the sequence
    wb.set_cell_contents("Sheet1", "A1", "1")
    end_t = time.time()
    profiler.disable()

    # Verify the value propagated correctly through the chain
    try:
        assert wb.get_cell_value("Sheet1", f"A{n}") == expected
    except AssertionError:
        print(f"Expected: {expected}, Got: {wb.get_cell_value('Sheet1', f'A{n}')}")
        raise

    profiler_move = cProfile.Profile()
    profiler_move.enable()
    start_t_move = time.time()
    wb.move_cells("Sheet1", "A1", "A1000", "B1", "Sheet1")
    end_t_move = time.time()
    profiler_move.disable()

    try:
        assert wb.get_cell_value("Sheet1", f"B{n}") == expected
        assert wb.get_cell_value("sheet1", "A1") is None
    except AssertionError:
        print(f"Expected: {expected}, Got: {wb.get_cell_value('Sheet1', f'B{n}')}")
        raise

    profiler_copy = cProfile.Profile()
    profiler_copy.enable()
    start_t_copy = time.time()
    wb.copy_cells("Sheet1", "B1", "B1000", "C1", "Sheet1")
    end_t_copy = time.time()
    profiler_copy.disable()

    try:
        assert wb.get_cell_value("Sheet1", f"C{n}") == expected
        assert wb.get_cell_value("sheet1", "B1") == 1
        assert wb.get_cell_value("sheet1", f"B{n}") == expected
    except AssertionError:
        print(f"Expected: {expected}, Got: {wb.get_cell_value('Sheet1', f'C{n}')}")
        raise



    # Output the performance results
    OUT.write("---------- FIBONACCI SEQUENCE RESULTS ----------\n")
    OUT.write(f"Total Time: {end_t - start_t}\n")
    sortby = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=OUT).sort_stats(sortby)
    ps.print_stats()

    OUT.write("---------- MOVE CELLS RESULTS ----------\n")
    OUT.write(f"Total Time: {end_t_move - start_t_move}\n")
    sortby_move = pstats.SortKey.CUMULATIVE
    ps_move = pstats.Stats(profiler_move, stream=OUT).sort_stats(sortby_move)
    ps_move.print_stats()

    OUT.write("---------- COPY CELLS RESULTS ----------\n")
    OUT.write(f"Total Time: {end_t_copy - start_t_copy}\n")
    sortby_copy = pstats.SortKey.CUMULATIVE
    ps_copy = pstats.Stats(profiler_copy, stream=OUT).sort_stats(sortby_copy)
    ps_copy.print_stats()



def pascal_tr(n:int = 50):
    """
    Sets up Pascal's triangle in a spreadsheet, and then creates formulas that
    sum up the numbers in each row to verify values are correct.
    """
    formulas = [("Sheet1", "A2", "1"), ("Sheet1", "B2", "1")]
    for row in range(3, n+1):
        # Each row starts with 1
        formulas.append(("Sheet1", f"A{row}", "1"))
        # Each row has n+1 elements - compute n-1 of them
        for element in range(2, row):
            formulas.append(("Sheet1", f"{generate_column_keys(element)[element-1]}{row}",
                             f"={generate_column_keys(element+1)[element-2]}" +
                             f"{row-1}+{generate_column_keys(element)[element-1]}" +
                             f"{row-1}"))
        # Each row ends with 1
        formulas.append(("Sheet1", f"{generate_column_keys(row)[row-1]}{row}", "1"))

    # Set a sum formula for each row
    for row in range(1, n+1):
        formula = "=" + ("+").join([f"{generate_column_keys(i)[i-1]}{row}"
                                    for i in range(1, row+1)])
        formulas.append(("Sheet1", f"ZZZZ{row}", formula))

    # Setup the profiler
    profiler = cProfile.Profile()
    profiler.enable()

    # Setup by creating a workbook and setting the generated formulas
    start_t = time.time()
    wb = Workbook()
    wb.new_sheet()
    for formula in formulas:
        wb.set_cell_contents(*formula)

    # Set A1 and propagate values through the mesh
    wb.set_cell_contents("Sheet1", "A1", "1")

    end_t = time.time()
    profiler.disable()
    # Verify the values are correct using the sum of each row.
    for row in range(1, n+1):
        assert wb.get_cell_value("Sheet1", f"ZZZZ{row}") == 2**(row-1)

    # Output the performance results
    OUT.write("---------- PASCAL'S TRIANGLE RESULTS ----------\n")
    OUT.write(f"Total Time: {end_t - start_t}\n")
    sortby = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=OUT).sort_stats(sortby)
    ps.print_stats()



# Run Tests
long_chain()
m_n_row_mesh()
fibonacci()
pascal_tr()



with open("tests/performance_results.txt", "w", encoding="utf-8") as f:
    f.write(OUT.getvalue())
