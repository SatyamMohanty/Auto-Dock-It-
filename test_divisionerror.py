def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        10 / 0