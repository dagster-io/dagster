# turn off type signature tests by default, mirroring
# core_tests/resource_tests/conftest.py: they shell out to real type checkers, so
# they only run under `-m typesignature` (which the type_signature_tests tox env passes)
def pytest_configure(config):
    markexpr = getattr(config.option, "markexpr", None)
    if not markexpr or "typesignature" not in markexpr:
        setattr(
            config.option,
            "markexpr",
            markexpr + " and not typesignature" if markexpr else "not typesignature",
        )
