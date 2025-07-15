def test_division_by_zero():
    try:
        result = 1 / 0
    except ZeroDivisionError:
        pass
    else:
        raise AssertionError("Expected ZeroDivisionError")
