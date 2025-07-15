def test_string_concat_with_int():
    with pytest.raises(TypeError):
        "Total: " + 10