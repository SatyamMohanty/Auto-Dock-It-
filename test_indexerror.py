def test_list_index_out_of_range():
    items = [1, 2, 3]
    with pytest.raises(IndexError):
        items[5]