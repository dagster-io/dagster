# turn off type signature tests by default
# they are slow when run locally
# you can specify the -m "typesignature" flag to run them (& tox will run them in CI)
def pytest_configure(config):
    markexpr = getattr(config.option, "markexpr", None)
    if not markexpr or "typesignature" not in markexpr:
        setattr(
            config.option,
            "markexpr",
            markexpr + " and not typesignature" if markexpr else "not typesignature",
        )
