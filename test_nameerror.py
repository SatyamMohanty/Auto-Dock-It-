def test_undefined_variable():
    with pytest.raises(NameError):
        print(undefined_var)