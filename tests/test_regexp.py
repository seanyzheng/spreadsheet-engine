"""
These are extensive tests for all of the regexps used in the spreadsheet
implementation. This includes checking for valid sheet namesand finding/
replacing sheet names in formulas.
"""

import sheets.regexp


def test_valid_sheet_name():
    """
    Tests the VALID_SHEET_NAME regexp for valid sheet names.
    Sheet names can be any combination of letters, numbers, and the following
    symbols: .?!,:;!@#$%^&*()-_ (including whitespace). Sheet names may not
    include single or double quotes, and may not start or end with whitespace. 
    They also may not be the empty string.
    """
    invalid = ["", "'", '"', " ", "  ", " a", "a ", "a'b", 'a"b', "a'b'c",
               " Sheet1", "Sheet1 ", "Sheet'1"]
    valid = ["Sheet1", "Sheet 1", "Sheet 1.2", "Sheet 1.2!3", "Sheet 1.2!3:4",
             "_Sheet1", "Sheet_1!", "Sheet1?", "Sheet1;", "Sheet1@", "Sheet1#",
             "Sheet1$", "Sheet1%", "Sheet1^", "Sheet1&", "Sheet1*", "Sheet1(",
            "Sheet1)", "Sheet1-", "Sheet1_", "Sheet1+", "Sheet1=", "Sheet1,",
            "Sheet1.", "Sheet1:", "0", "9", "0,9", "a", "0 9", "a b", "a 1",
            "a 1.2", "a 1.2!3", "a 1.2!3:4", "a_1", "a_1!", "a1?", "a1;", "a1@",
            "_ _"]
    for name in invalid:
        assert not sheets.regexp.VALID_SHEET_NAME.fullmatch(name)
    for name in valid:
        assert sheets.regexp.VALID_SHEET_NAME.fullmatch(name) is not None


def test_unit_rename_regexp():
    """
    Tests that regular expressions work appropriately when finding and replacing
    sheet names in formulas.
    """
    # Test simple replacement of unquoted sheet name
    assert (sheets.regexp.replace_names("=Sheet1!A1", "Sheet1", "Sheet2") ==
            "=Sheet2!A1")
    # Test simple replacement of quoted sheet name
    assert (sheets.regexp.replace_names("='Sheet1'!A1", "Sheet1", "Sheet 2") ==
            "='Sheet 2'!A1")
    # Test replacement of unquoted sheet name with sheet name which needs quoting
    assert (sheets.regexp.replace_names("=Sheet1!A1", "Sheet1", "9999") ==
            "='9999'!A1")
    # Test replacement of quoted sheet name with sheet name which needs quoting
    assert (sheets.regexp.replace_names("='991'!A1", "991", "9999") ==
            "='9999'!A1")
    # Test replacement of a quoted sheet name which is not renamed but needs to
    # be unquoted
    assert (sheets.regexp.replace_names("='Sheet1'!A1", "NAN", "WHATEV") ==
            "=Sheet1!A1")
    # Test replacement of a sheet name which is in a string literal does nothing
    assert (sheets.regexp.replace_names('="Sheet1!A1"', "Sheet1", "Sheet2") ==
            '="Sheet1!A1"')
    # Test replacement of a sheet name and quoted sheet name that needs to be
    # unquoted are both handled simultaneously
    assert (sheets.regexp.replace_names("='Sheet1'!A1&'Sheet2'!B12", "Sheet1", "9999") ==
            "='9999'!A1&Sheet2!B12")
    # Test some replacements and some string literals together
    assert (sheets.regexp.replace_names('="Sheet1!A1"&Sheet1!B12', "Sheet1", "9999") ==
            '="Sheet1!A1"&\'9999\'!B12')
    # Test replacement of sheet names within parentheses
    assert (sheets.regexp.replace_names("=(MySheet!A1+MySheet!B1 - (MySheet!C1))",
                                         "MySheet", "9999") ==
            "=('9999'!A1+'9999'!B1 - ('9999'!C1))")


def test_weird_rename():
    """
    Tests that regular expressions work appropriately when finding and replacing 
    really odd sheet names (single characters, symbols, etc.)
    """
    # Test replacement of really odd sheet names
    to_replace = ["6", "!", "12", "a      z", "? / .", "_? ?_"]
    replace_with = ["_", "0 0 .", "NOQUOTE", "a b", "!", "S h e e t 1"]
    formulas = [
        "='6'!A1 + 6 * 6 & \"6\" & '6'!B12",
        "='!'!A1 + ! * ! & \"!\" & '!'!B12",
        "='12'!A1 + 12 * 12 & \"12\" & '12'!B12",
        "='a      z'!A1 + \"a      z\" * \"a      z\" & \"a      z\" & " +
        "'a      z'!B12",
        "='? / .'!A1 + ? / . * ? / . & \"? / .\" & '? / .'!B12",
        "='_? ?_'!A1 + _? ?_ * _? ?_ & \"_? ?_\" & '_? ?_'!B12",
    ]
    replaced = [
        "=_!A1 + 6 * 6 & \"6\" & _!B12",
        "='0 0 .'!A1 + ! * ! & \"!\" & '0 0 .'!B12",
        "=NOQUOTE!A1 + 12 * 12 & \"12\" & NOQUOTE!B12",
        "='a b'!A1 + \"a      z\" * \"a      z\" & \"a      z\" & 'a b'!B12",
        "='!'!A1 + ? / . * ? / . & \"? / .\" & '!'!B12",
        "='S h e e t 1'!A1 + _? ?_ * _? ?_ & \"_? ?_\" & 'S h e e t 1'!B12",
    ]
    for i, formula in enumerate(formulas):
        assert (sheets.regexp.replace_names(formula, to_replace[i],
                                            replace_with[i]) ==
                replaced[i])


def test_complex_rename():
    """
    Tests the renaming operation using regexps on complex examples, where the 
    formulas have many sheet name refs which need their quoting repaired,
    multiple instances of the sheet to be renamed, and multiple string literals 
    which could be confused for an incorrectly quoted sheet name or the sheet 
    name to be replaced.
    """
    # Test replacement of many references
    assert (sheets.regexp.replace_names("=Sheet1!A1&Sheet1!B12&Sheet1!C123&Sheet1!D1234",
                                        "Sheet1", "9999") ==
            "='9999'!A1&'9999'!B12&'9999'!C123&'9999'!D1234")

    # Test many possibly confusing string literals
    assert (sheets.regexp.replace_names('="\'My sheet?/!\'!A1"', "My sheet?/!", "9999") ==
            '="\'My sheet?/!\'!A1"')
    assert (sheets.regexp.replace_names('="A1 + A2 + Shet!A1 - A2 - A1"', "Shet", "9999") ==
            '="A1 + A2 + Shet!A1 - A2 - A1"')
    assert (sheets.regexp.replace_names('=A1 + A2 & "Shet!A1 & A2" & Shet!B12 - ' +
                                        '\'Shet\'!C26 + \'Sheet2\'!N45', "Shet", "_shet")
            == '=A1 + A2 & "Shet!A1 & A2" & _shet!B12 - _shet!C26 + Sheet2!N45')
