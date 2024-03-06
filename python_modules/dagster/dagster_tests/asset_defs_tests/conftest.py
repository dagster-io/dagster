import pytest


@pytest.fixture()
def rapidfuzz_installed():
    try:
        import rapidfuzz
    except ImportError as e:
        raise Exception(
            "This test depends on having the optional `rapidfuzz` dep installed, "
            "you may need to `pip install rapidfuzz`."
        ) from e
