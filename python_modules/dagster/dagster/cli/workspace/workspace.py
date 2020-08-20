from dagster import check
from dagster.core.host_representation import RepositoryLocationHandle


class Workspace:
    def __init__(self, repository_location_handles):
        check.list_param(
            repository_location_handles,
            'repository_location_handles',
            of_type=RepositoryLocationHandle,
        )
        self._location_handle_dict = {rlh.location_name: rlh for rlh in repository_location_handles}

    @property
    def repository_location_handles(self):
        return list(self._location_handle_dict.values())

    @property
    def repository_location_names(self):
        return list(self._location_handle_dict.keys())

    def has_repository_location_handle(self, location_name):
        check.str_param(location_name, 'location_name')
        return location_name in self._location_handle_dict

    def get_repository_location_handle(self, location_name):
        check.str_param(location_name, 'location_name')
        return self._location_handle_dict[location_name]

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        for handle in self.repository_location_handles:
            handle.cleanup()
