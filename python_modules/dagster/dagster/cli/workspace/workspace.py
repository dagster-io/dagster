from dagster import check
from dagster.core.host_representation import RepositoryLocationHandle, RepositoryLocationOrigin


class Workspace:
    def __init__(self, repository_location_origins):
        check.list_param(
            repository_location_origins,
            "repository_location_origins",
            of_type=RepositoryLocationOrigin,
        )

        self._location_handle_dict = {}
        for origin in repository_location_origins:
            check.invariant(
                self._location_handle_dict.get(origin.location_name) is None,
                'Cannot have multiple locations with the same name, got multiple "{name}"'.format(
                    name=origin.location_name,
                ),
            )

            self._location_handle_dict[
                origin.location_name
            ] = RepositoryLocationHandle.create_from_repository_location_origin(origin)

    @property
    def repository_location_handles(self):
        return list(self._location_handle_dict.values())

    @property
    def repository_location_names(self):
        return list(self._location_handle_dict.keys())

    def has_repository_location_handle(self, location_name):
        check.str_param(location_name, "location_name")
        return location_name in self._location_handle_dict

    def get_repository_location_handle(self, location_name):
        check.str_param(location_name, "location_name")
        return self._location_handle_dict[location_name]

    def reload_repository_location(self, location_name):
        existing_handle = self.get_repository_location_handle(location_name)
        reloaded_handle = existing_handle.create_reloaded_handle()

        # Release any resources used by the old handle
        existing_handle.cleanup()
        self._location_handle_dict[location_name] = reloaded_handle
        return reloaded_handle

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        for handle in self.repository_location_handles:
            handle.cleanup()
