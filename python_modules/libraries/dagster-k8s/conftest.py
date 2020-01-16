# See: https://stackoverflow.com/a/31526934/324449
def pytest_addoption(parser):
    parser.addoption("--cluster", action="store")
