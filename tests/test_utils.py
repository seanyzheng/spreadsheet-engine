"""Utility functions and constants for testing spreadsheet functionality"""

# Tersting utilities
import random
import importlib
import string
import decimal as dec
import pytest

# Import from modules being tested
from sheets.cell import Cell, CellType


# Constants
RAND_CASES = 100

def generate_random_string() -> str:
    """ 
    Generates a random string of length 1-100.
    """
    return ''.join(random.choice(string.ascii_letters)
                   for _ in range(random.randint(10, 100)))

def ref_loc(location: str) -> str:
    """
    Converts a location from a format like 'a9', 'aa19', 'aaa999' to '$A-Z$1-9999'.
    """
    alpha_part = ""
    num_part = ""
    for char in location:
        if char.isalpha():
            alpha_part += char
        elif char.isdigit():
            num_part += char

    alpha_part = alpha_part.upper()
    formatted_location = f"${alpha_part}${num_part}"

    return formatted_location


def generate_random_number() -> int:
    """ 
    Generates a random number between -100 and 100.
    """
    return int(random.uniform(-100, 100))


def get_random_cell(cell_type: CellType) -> Cell:
    """ 
    Generates a random cell of the given type and return it along with the input 
    content to the cell constructor.
    """
    if cell_type == CellType.STRING:
        ran_str = generate_random_string()
        return Cell(ran_str), ran_str
    if cell_type == CellType.NUMBER:
        ran_num = str(generate_random_number())
        return Cell(ran_num), ran_num
    if cell_type == CellType.FORMULA:
        raise NotImplementedError
    raise ValueError("Invalid cell type")


def run_rand(func, args: list):
    """ 
    Runs the given function with random input num_cases times.
    """
    for _ in range(RAND_CASES):
        func(*args)


def check_dec_equal(dec1, dec2):
    """ 
    Checks if two decimals are equal.
    """
    return (pytest.approx(dec1, rel=dec.Decimal(1e-6))
            == dec.Decimal(dec2))

def rand_loc():
    """
    Generates a random spreadsheet location
    """
    # Generate random uppercase letters (between A and Z)
    letters = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for
                      _ in range(random.randint(1, 4)))
    return f"{letters}{random.randint(1, 9999)}"


def rand_symbol():
    """
    Generates a random symbol
    """
    return random.choice(['!', '@', '#', '$', '%', '^', '&', '|', '\\',
                           ';', ':', '"', "'", ',','.', '?', '`', '~'])

def rand_operator():
    """
    Generates a random operator
    """
    return random.choice(['+', '-', '*', '/'])


def run_all_rand(module_name):
    """
    This runs random trials of all the random test functions in a testing file.
    All test functions in the global context of a test file are run RAND_CASES
    times. This may later need to be modified to only run tests marked as random
    multiple times or to allow args to be passed in to the test functions.
    """
    try:
        # Import the module dynamically
        module = importlib.import_module(module_name)

        # Get all functions in the module
        functions = [func for name, func in vars(module).items() if callable(func)
                     and name.startswith("test_rand_")]

        # Run each function
        for func in functions:
            for _ in range(RAND_CASES):
                func()

    except ModuleNotFoundError:
        print(f"Module {module_name} not found")


def run_non_rand(module_name):
    """
    This runs all the non-random test functions in a testing file.
    """
    try:
        # Import the module dynamically
        module = importlib.import_module(module_name)

        # Get all functions in the module
        functions = [func for name, func in vars(module).items() if callable(func)
                     and name.startswith("test_") and not name.startswith("test_rand_")]

        # Run each function
        for func in functions:
            func()

    except ModuleNotFoundError:
        print(f"Module {module_name} not found")


def run_all(module_name):
    """
    Runs all tests in a module.
    """
    run_all_rand(module_name)
    run_non_rand(module_name)
