"""
This module contains logic and compiled regular expressions for working with 
formulas and sheet names. Regular expressions are used to find certain
occurrences within formulas and manipulate them. For example, when renaming a 
sheet, we need to find all references to that sheet in formulas and update them
to reflect the new sheet name.
"""

import re

# Compiled regular expressions for working with sheet names

# All characters allowed in a sheet name
ALL_SHT_CHAR = r"[a-zA-Z0-9\.\?!,:;!@#\$%\^&\*()-_ ]"

# Sheet name beginings and endings (No white space!)
SHT_BEG_END = r"[a-zA-Z0-9\.\?!,:;!@#\$%\^&\*()-_]"

# Characters allowed in an unquoted sheet name in a formula (No symbols!)
UNQ_SHT_CHAR = r"[a-zA-Z0-9_]"

# Characters allowed to begin an unquoted sheet name in a formula (No numbers!)
UNQ_SHT_BEG = r"[a-zA-Z_]"

# Single quoted sheet name
SQ_SHT_NAME = fr"'{SHT_BEG_END}{ALL_SHT_CHAR}*{SHT_BEG_END}'|'{SHT_BEG_END}'"

# Unquoted sheet name
UNQ_SHT_NAME = fr"{UNQ_SHT_BEG}{UNQ_SHT_CHAR}*"

# Multi-character sheet name
MUL_SHT_NAME = fr"^{SHT_BEG_END}{ALL_SHT_CHAR}*{SHT_BEG_END}$"

# Valid sheet name
VALID_SHEET_NAME = re.compile(fr"^{MUL_SHT_NAME}|^{SHT_BEG_END}")

# Find all string literals in a formula
ALL_STR = re.compile(r'"[^"]+"')

# Sheet names which require single quoting
RQ_QUOTE = re.compile(r"(^[^a-zA-Z_]|\W)")

# Valid cell locations
VALID_CELL = r'[A-Za-z]{1,4}[1-9]\d{0,3}'

# Cell location in formula (can be absolute ref)
FORM_CELL = r'\${0,1}[A-Za-z]{1,4}\${0,1}[1-9][0-9]{0,3}'

VALID_LOC = re.compile(VALID_CELL)

# Matches any reference in a formulas with dbl quotes removed from it. i.e
# Sheet1!A1, 'Sheet1'!A1, A1
MULTI_SQ_REF = rf"'{SHT_BEG_END}{ALL_SHT_CHAR}*{SHT_BEG_END}'!{FORM_CELL}"
SINGLE_SQ_REF = rf"'{SHT_BEG_END}'!{FORM_CELL}"
UNQ_REF = rf"{UNQ_SHT_NAME}!{FORM_CELL}"
REF = re.compile(rf"({MULTI_SQ_REF}|{SINGLE_SQ_REF}|{UNQ_REF})|({FORM_CELL})")

# Match sheet names in cell ref formulas. These are either valid single quoted
# sheet names, or valid unquoted sheet names that are not preceded by a number
# or word character (Should be an operator or opening parenthesis) and are
# followed by an exclamation point.
SHT_REF = re.compile(fr"(?<![\d\w\"]){SQ_SHT_NAME}(?=!)|(?<![\d\w\"])" +
                     fr"{UNQ_SHT_NAME}(?=!)")

# Match any funtion with evaluation time dependencies
HAS_EVAL_DEP = re.compile(r'if|iferror|choose|indirect', re.IGNORECASE)

def require_sq(sheet_name: str) -> str:
    """
    Determines whether the given sheet name requires single quotes to be
    included in a formula, and either returns the single quotes sheet name if
    so, or the original sheet name if not.
    """
    # if the passed string is enclosed in SQ, strip them
    sheet_name = sheet_name.strip("'")
    if RQ_QUOTE.search(sheet_name):
        return "'" + sheet_name + "'"
    return sheet_name


def rpl_dbl_quotes(string: str) -> str:
    """
    Replaces all double quoted strings in the given string with '.' and matains 
    the length of the string
    """
    quoteds = ALL_STR.finditer(string)
    for m in quoteds:
        start, end = m.start(), m.end()
        string = string[:start] + '.' * (end - start) + string[end:]
    return string


def find_refs(formula: str):
    """
    Finds all references to other cells in the given formula and returns them 
    as a list of strings. This should include both cell references in the form
    "A1" (local to the sheet) and references in the form "Sheet1!A1".
    """
    #handle cases where there are evaluation time depdendencies
    refs =  REF.findall(rpl_dbl_quotes(formula))
    inds, sheetsrefs = [], []
    for ref in refs:
        if ref[0] != "":
            # Separate the sheet name from the location
            if ref[0][0] == "'":
                # Find all single quotes in the string
                ind = [i for i, ltr in enumerate(ref[0]) if ltr == "'"]
                sheetsrefs.append((ref[0][ind[0]+1:ind[1]], ref[0][ind[1]+2:].replace("$", "")))
            else:
                sheetsrefs.append((ref[0][0:ref[0].index("!")],
                                   ref[0][ref[0].index("!")+1:].replace("$", "")))
        else:
            inds.append(ref[1].replace("$", ""))
    return inds, sheetsrefs

def find_refs_absolute(formula: str):
    """
    Finds all references to other cells in the given formula and returns them 
    as a list of strings. This version preserves the "$" sign to distinguish
    absolute and mixed references. This should include both cell references in the form
    "A1" (local to the sheet) and references in the form "Sheet1!A1".
    """
    refs = REF.findall(rpl_dbl_quotes(formula))
    inds, sheetsrefs = [], []
    for ref in refs:
        if ref[0] != "":
            # Separate the sheet name from the location
            if ref[0][0] == "'":
                # Find all single quotes in the string
                ind = [i for i, ltr in enumerate(ref[0]) if ltr == "'"]
                sheetsrefs.append((ref[0][ind[0]+1:ind[1]], ref[0][ind[1]+2:]))  # Keep the "$"
            else:
                sheetsrefs.append((ref[0][0:ref[0].index("!")],
                                   ref[0][ref[0].index("!")+1:]))  # Keep the "$"
        else:
            inds.append(ref[1])  # Keep the "$"
    return inds, sheetsrefs



def replace_names(formula: str, old_name: str, new_name: str) -> str:
    """
    Replaces all occurrences of the old sheet name with the new sheet name in
    the given formula. Replaces all occurrences of any other sheet names with 
    their properly single quoted versions. Returns the original formula with
    only those replacements made
    """
    # First replace all double quoted strings in the formula with '.' in a new
    # copy so that we don't match sheet names in them, but preserve the overall
    # length of the str
    new_formula = rpl_dbl_quotes(formula)
    # Now find all sheet names in the formula and iterate over them. Build up
    # the formula with the replacements made
    prev_idx = 0
    final_form = ""
    old_names = set([f"'{old_name.lower()}'", old_name.lower()])
    for sheet_name in SHT_REF.finditer(new_formula):
        final_form += formula[prev_idx:sheet_name.start()]
        sheet_name_str = sheet_name.group()
        to_add = (new_name if sheet_name_str.lower() in old_names else
                  sheet_name_str)
        final_form += require_sq(to_add)
        prev_idx = sheet_name.end()
    return final_form + formula[prev_idx:]


def is_ref(string: str) -> bool:
    """
    Returns true if the given string is a valid cell reference of any type, and
    false otherwise.
    """
    return REF.fullmatch(string) is not None

def has_eval_dep(string: str) -> bool:
    """
    Returns true if the given string contains a function with evaluation time 
    dependencies, and false otherwise.
    """
    return HAS_EVAL_DEP.findall(rpl_dbl_quotes(string)) != []
