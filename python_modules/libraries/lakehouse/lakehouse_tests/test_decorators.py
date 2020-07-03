from lakehouse import computed_asset, source_asset


def test_computed_asset_no_deps():
    @computed_asset(storage_key='filesystem')
    def casset() -> str:
        return 'a'

    assert casset.computation
    assert casset.path == ('casset',)
    assert casset.computation.output_in_memory_type == str
    assert len(casset.computation.deps.keys()) == 0


def test_computed_asset_path():
    @computed_asset(storage_key='filesystem', path=('z', 'd'))
    def casset() -> str:
        return 'a'

    assert casset.path == ('z', 'd')


def test_computed_asset_one_dep():
    source_asset1 = source_asset(storage_key='filesystem', path=('a', 'b'))

    @computed_asset(storage_key='filesystem', input_assets={'a_': source_asset1})
    def casset(a_: int) -> str:
        return str(a_)

    assert casset.computation
    assert casset.path == ('casset',)
    assert casset.computation.output_in_memory_type == str
    assert list(casset.computation.deps.keys()) == ['a_']
    assert casset.computation.deps['a_'].in_memory_type == int
    assert casset.computation.deps['a_'].asset == source_asset1


def test_computed_asset_multiple_deps_dict():
    source_asset1 = source_asset(storage_key='filesystem', path=('a', 'b'))
    source_asset2 = source_asset(storage_key='filesystem', path=('a', 'c'))

    @computed_asset(
        storage_key='filesystem', input_assets={'b_': source_asset1, 'c_': source_asset2}
    )
    def casset(b_: int, c_: float) -> str:
        return str(b_) + str(c_)

    assert casset.computation
    assert casset.path == ('casset',)
    assert casset.computation.output_in_memory_type == str
    assert set(casset.computation.deps.keys()) == set(['b_', 'c_'])
    assert casset.computation.deps['b_'].in_memory_type == int
    assert casset.computation.deps['b_'].asset == source_asset1
    assert casset.computation.deps['c_'].in_memory_type == float
    assert casset.computation.deps['c_'].asset == source_asset2


def test_computed_asset_multiple_deps_list():
    source_asset1 = source_asset(storage_key='filesystem', path=('a', 'b'))
    source_asset2 = source_asset(storage_key='filesystem', path=('a', 'c'))

    @computed_asset(storage_key='filesystem', input_assets=[source_asset1, source_asset2])
    def casset(b_: int, c_: float) -> str:
        return str(b_) + str(c_)

    assert casset.computation
    assert casset.path == ('casset',)
    assert casset.computation.output_in_memory_type == str
    assert set(casset.computation.deps.keys()) == set(['b_', 'c_'])
    assert casset.computation.deps['b_'].in_memory_type == int
    assert casset.computation.deps['b_'].asset == source_asset1
    assert casset.computation.deps['c_'].in_memory_type == float
    assert casset.computation.deps['c_'].asset == source_asset2
