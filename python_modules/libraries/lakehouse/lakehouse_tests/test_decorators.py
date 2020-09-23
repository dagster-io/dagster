from lakehouse import Column, computed_asset, computed_table, source_asset, source_table


def test_computed_asset_no_deps():
    @computed_asset(storage_key="filesystem")
    def casset() -> str:
        return "a"

    assert casset.computation
    assert casset.path == ("casset",)
    assert casset.computation.output_in_memory_type == str
    assert len(casset.computation.deps.keys()) == 0


def test_computed_asset_no_deps_default_storage():
    @computed_asset()
    def casset() -> str:
        return "a"

    assert casset.storage_key == "default_storage"
    assert casset.computation
    assert casset.path == ("casset",)
    assert casset.computation.output_in_memory_type == str
    assert len(casset.computation.deps.keys()) == 0


def test_computed_asset_path():
    @computed_asset(storage_key="filesystem", path=("z", "d"))
    def casset() -> str:
        return "a"

    assert casset.path == ("z", "d")


def test_computed_asset_one_dep():
    source_asset1 = source_asset(storage_key="filesystem", path=("a", "b"))

    @computed_asset(storage_key="filesystem", input_assets={"a_": source_asset1})
    def casset(a_: int) -> str:
        return str(a_)

    assert casset.computation
    assert casset.path == ("casset",)
    assert casset.computation.output_in_memory_type == str
    assert list(casset.computation.deps.keys()) == ["a_"]
    assert casset.computation.deps["a_"].in_memory_type == int
    assert casset.computation.deps["a_"].asset == source_asset1


def test_computed_asset_multiple_deps_dict():
    source_asset1 = source_asset(storage_key="filesystem", path=("a", "b"))
    source_asset2 = source_asset(storage_key="filesystem", path=("a", "c"))

    @computed_asset(
        storage_key="filesystem", input_assets={"b_": source_asset1, "c_": source_asset2}
    )
    def casset(b_: int, c_: float) -> str:
        return str(b_) + str(c_)

    assert casset.computation
    assert casset.path == ("casset",)
    assert casset.computation.output_in_memory_type == str
    assert set(casset.computation.deps.keys()) == set(["b_", "c_"])
    assert casset.computation.deps["b_"].in_memory_type == int
    assert casset.computation.deps["b_"].asset == source_asset1
    assert casset.computation.deps["c_"].in_memory_type == float
    assert casset.computation.deps["c_"].asset == source_asset2


def test_computed_asset_multiple_deps_list():
    source_asset1 = source_asset(storage_key="filesystem", path=("a", "b"))
    source_asset2 = source_asset(storage_key="filesystem", path=("a", "c"))

    @computed_asset(storage_key="filesystem", input_assets=[source_asset1, source_asset2])
    def casset(b_: int, c_: float) -> str:
        return str(b_) + str(c_)

    assert casset.computation
    assert casset.path == ("casset",)
    assert casset.computation.output_in_memory_type == str
    assert set(casset.computation.deps.keys()) == set(["b_", "c_"])
    assert casset.computation.deps["b_"].in_memory_type == int
    assert casset.computation.deps["b_"].asset == source_asset1
    assert casset.computation.deps["c_"].in_memory_type == float
    assert casset.computation.deps["c_"].asset == source_asset2


COLUMNS = [Column("a", str), Column("bb", int)]


def test_computed_table_no_deps():
    @computed_table(storage_key="filesystem", columns=COLUMNS)
    def casset() -> str:
        return "a"

    assert casset.computation
    assert casset.path == ("casset",)
    assert casset.computation.output_in_memory_type == str
    assert len(casset.computation.deps.keys()) == 0
    assert casset.columns == COLUMNS


def test_computed_table_path():
    @computed_table(storage_key="filesystem", path=("z", "d"), columns=COLUMNS)
    def casset() -> str:
        return "a"

    assert casset.path == ("z", "d")
    assert casset.columns == COLUMNS


def test_computed_table_one_dep():
    source_table1 = source_table(storage_key="filesystem", path=("a", "b"), columns=COLUMNS)

    @computed_table(storage_key="filesystem", input_assets={"a_": source_table1}, columns=COLUMNS)
    def casset(a_: int) -> str:
        return str(a_)

    assert casset.computation
    assert casset.path == ("casset",)
    assert casset.computation.output_in_memory_type == str
    assert list(casset.computation.deps.keys()) == ["a_"]
    assert casset.computation.deps["a_"].in_memory_type == int
    assert casset.computation.deps["a_"].asset == source_table1
    assert casset.columns == COLUMNS


def test_computed_table_multiple_deps_dict():
    source_asset1 = source_asset(storage_key="filesystem", path=("a", "b"))
    source_asset2 = source_asset(storage_key="filesystem", path=("a", "c"))

    @computed_table(
        storage_key="filesystem",
        input_assets={"b_": source_asset1, "c_": source_asset2},
        columns=COLUMNS,
    )
    def casset(b_: int, c_: float) -> str:
        return str(b_) + str(c_)

    assert casset.computation
    assert casset.path == ("casset",)
    assert casset.computation.output_in_memory_type == str
    assert set(casset.computation.deps.keys()) == set(["b_", "c_"])
    assert casset.computation.deps["b_"].in_memory_type == int
    assert casset.computation.deps["b_"].asset == source_asset1
    assert casset.computation.deps["c_"].in_memory_type == float
    assert casset.computation.deps["c_"].asset == source_asset2
    assert casset.columns == COLUMNS


def test_computed_table_multiple_deps_list():
    source_asset1 = source_asset(storage_key="filesystem", path=("a", "b"))
    source_asset2 = source_asset(storage_key="filesystem", path=("a", "c"))

    @computed_table(
        storage_key="filesystem", input_assets=[source_asset1, source_asset2], columns=COLUMNS
    )
    def casset(b_: int, c_: float) -> str:
        return str(b_) + str(c_)

    assert casset.computation
    assert casset.path == ("casset",)
    assert casset.computation.output_in_memory_type == str
    assert set(casset.computation.deps.keys()) == set(["b_", "c_"])
    assert casset.computation.deps["b_"].in_memory_type == int
    assert casset.computation.deps["b_"].asset == source_asset1
    assert casset.computation.deps["c_"].in_memory_type == float
    assert casset.computation.deps["c_"].asset == source_asset2
    assert casset.columns == COLUMNS


def test_version():
    @computed_asset(version="some_version")
    def casset() -> str:
        return "a"

    assert casset.computation.version == "some_version"
