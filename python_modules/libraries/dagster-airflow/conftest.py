# See: https://stackoverflow.com/a/31526934/324449
def pytest_addoption(parser):
    # Use kind or some other cluster provider?
    parser.addoption('--cluster-provider', action='store', default='kind')

    # Specify an existing kind cluster name to use
    parser.addoption('--kind-cluster', action='store')

    # Keep resources around after tests are done
    parser.addoption('--no-cleanup', action='store_true', default=False)
