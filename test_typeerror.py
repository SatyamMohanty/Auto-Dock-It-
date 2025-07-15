def test_add_string_and_int():
    with pytest.raises(TypeError):
        "abc" + 5