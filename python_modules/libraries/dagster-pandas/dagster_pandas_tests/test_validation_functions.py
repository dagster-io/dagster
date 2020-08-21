from dagster_pandas.constraints import (
    all_unique_validator,
    categorical_column_validator_factory,
    column_range_validation_factory,
    dtype_in_set_validation_factory,
    non_null_validation,
    nonnull,
)
from numpy import nan as NaN


def test_unique():
    testlst = [0, 1, 2]
    assert all_unique_validator(testlst)[0]
    faillst = [0, 0, 1]
    assert not all_unique_validator(faillst)[0]


def test_ignore_vals():
    faillst = [0, NaN, NaN]
    assert all_unique_validator(faillst, ignore_missing_vals=True)[0]


def test_null():
    testval = NaN
    assert not non_null_validation(testval)[0]


def test_range():
    testfunc = column_range_validation_factory(minim=0, maxim=10)
    assert testfunc(1)[0]
    assert not (testfunc(20)[0])


def test_dtypes():
    testfunc = dtype_in_set_validation_factory((int, float))
    assert testfunc(1)[0]
    assert testfunc(1.5)[0]
    assert not testfunc("a")[0]


def test_nonnull():
    testfunc = dtype_in_set_validation_factory((int, float))
    assert testfunc(NaN)[0]
    ntestfunc = nonnull(testfunc)
    assert not ntestfunc(NaN)[0]


def test_categorical():
    testfunc = categorical_column_validator_factory(["a", "b"], ignore_missing_vals=True)
    assert testfunc("a")[0]
    assert testfunc("b")[0]
    assert testfunc(NaN)[0]
    assert not testfunc("c")[0]
