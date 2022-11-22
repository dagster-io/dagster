# start_repository_loads_all_definitions
from .hello_world_repository import hello_world_repository


def test_repository_loads_all_definitions():
    """
    Asserts that the repository can load all definitions (jobs, assets, schedules, etc)
    without errors.
    """

    hello_world_repository.load_all_definitions()


# end_repository_loads_all_definitions
