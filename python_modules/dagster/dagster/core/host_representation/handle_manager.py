from dagster import check

from .origin import RepositoryLocationOrigin


class RepositoryLocationHandleManager:
    """
    Holds repository location handles for reuse
    """

    def __init__(self):
        self._location_handles = {}

    def __enter__(self):
        return self

    def get_handle(self, repository_location_origin):
        check.inst_param(
            repository_location_origin, "repository_location_origin", RepositoryLocationOrigin
        )
        origin_id = repository_location_origin.get_id()

        if origin_id not in self._location_handles:
            self._location_handles[origin_id] = repository_location_origin.create_handle()

        return self._location_handles[origin_id]

    def cleanup(self):
        for handle in self._location_handles.values():
            handle.cleanup()

    def __exit__(self, exception_type, exception_value, traceback):
        self.cleanup()
