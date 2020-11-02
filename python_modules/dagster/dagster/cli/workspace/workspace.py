import sys
import warnings
from collections import OrderedDict

from dagster import check
from dagster.core.host_representation import RepositoryLocationHandle, RepositoryLocationOrigin
from dagster.utils.error import serializable_error_info_from_exc_info


class Workspace:
    def __init__(self, repository_location_origins):
        self._location_origin_dict = OrderedDict()
        check.list_param(
            repository_location_origins,
            "repository_location_origins",
            of_type=RepositoryLocationOrigin,
        )

        self._location_handle_dict = {}
        self._location_error_dict = {}
        for origin in repository_location_origins:
            check.invariant(
                self._location_origin_dict.get(origin.location_name) is None,
                'Cannot have multiple locations with the same name, got multiple "{name}"'.format(
                    name=origin.location_name,
                ),
            )

            self._location_origin_dict[origin.location_name] = origin
            self._load_handle(origin.location_name)

    def _load_handle(self, location_name):
        existing_handle = self._location_handle_dict.get(location_name)
        if existing_handle:
            existing_handle.cleanup()
            del self._location_handle_dict[location_name]

        if self._location_error_dict.get(location_name):
            del self._location_error_dict[location_name]

        origin = self._location_origin_dict[location_name]
        try:
            handle = RepositoryLocationHandle.create_from_repository_location_origin(origin)
            self._location_handle_dict[location_name] = handle
        except Exception:  # pylint: disable=broad-except
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            self._location_error_dict[location_name] = error_info
            warnings.warn(
                "Error loading repository location {location_name}:{error_string}".format(
                    location_name=location_name, error_string=error_info.to_string()
                )
            )

    @property
    def repository_location_handles(self):
        return list(self._location_handle_dict.values())

    @property
    def repository_location_names(self):
        return list(self._location_origin_dict.keys())

    @property
    def repository_location_errors(self):
        return list(self._location_error_dict.values())

    def has_repository_location_handle(self, location_name):
        check.str_param(location_name, "location_name")
        return location_name in self._location_handle_dict

    def get_repository_location_handle(self, location_name):
        check.str_param(location_name, "location_name")
        return self._location_handle_dict[location_name]

    def has_repository_location_error(self, location_name):
        check.str_param(location_name, "location_name")
        return location_name in self._location_error_dict

    def get_repository_location_error(self, location_name):
        check.str_param(location_name, "location_name")
        return self._location_error_dict[location_name]

    def reload_repository_location(self, location_name):
        self._load_handle(location_name)

    def is_reload_supported(self, location_name):
        return self._location_origin_dict[location_name].is_reload_supported

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        for handle in self.repository_location_handles:
            handle.cleanup()
