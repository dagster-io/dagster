import tempfile
import uuid
from abc import abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Callable, Optional

from typing_extensions import TypeAlias

from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.decorators.op_decorator import op
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_load_context import (
    DefinitionsLoadContext,
    DefinitionsLoadType,
)
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.storage.state import StateStorage
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import JobSpec
from dagster.components.resolved.model import Model, Resolver


@contextmanager
def _temp_state_path() -> Iterator[Path]:
    """Context manager that creates a temporary path to hold local state for a component."""
    with tempfile.TemporaryDirectory() as temp_dir:
        state_path = Path(temp_dir) / "state"
        yield state_path


class StateRefreshDefsModel(Model):
    job: JobSpec


def _resolve_state_refresh_defs(
    resolution_context: ResolutionContext, model: StateRefreshDefsModel
) -> Callable[[ComponentLoadContext, "StateBackedComponent"], Definitions]:
    def _fn(context: ComponentLoadContext, component: "StateBackedComponent") -> Definitions:
        return build_state_refresh_defs(
            context,
            component,
            resolution_context.resolve_value(model.job, as_type=Optional[JobSpec]),
        )

    return _fn


ResolvedStateRefreshDefs: TypeAlias = Optional[
    Annotated[
        Callable[[ComponentLoadContext, "StateBackedComponent"], Definitions],
        Resolver(
            fn=_resolve_state_refresh_defs,
            model_field_type=StateRefreshDefsModel,
        ),
    ]
]


def build_state_refresh_defs(
    context: ComponentLoadContext,
    component: "StateBackedComponent",
    job_spec: Optional[JobSpec] = None,
) -> Definitions:
    """Utility method to build a Definitions object that contains a job that refreshes the state for a component.

    Args:
        context (ComponentLoadContext): The context associated with this component load.
        component (StateBackedComponent): The component to refresh the state for.
        job_spec (Optional[JobSpec]): Configuration parameters for the generated job

    Returns:
        Definitions: A Definitions object that contains a job that refreshes the state for the component.
    """
    defs_key = component.get_state_key(context)

    @op(name=f"refresh_state_{defs_key}")
    def refresh_state() -> None:
        component.refresh_state(context)

    @job(
        name=job_spec.name if job_spec else f"refresh_state_job_{defs_key}",
        description=job_spec.description
        if job_spec
        else f"Job to refresh the state for {defs_key}",
        tags=job_spec.tags if job_spec else {},
    )
    def refresh_state_job():
        refresh_state()

    return Definitions(jobs=[refresh_state_job])


class StateBackedComponent(Component):
    def get_state_key(self, context: ComponentLoadContext) -> str:
        return context.path.relative_to(context.defs_module_path).as_posix().replace("/", "_")

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        key = self.get_state_key(context)

        defs_load_context = DefinitionsLoadContext.get()
        version = defs_load_context.get_state_version(key)

        state_storage = StateStorage.get_current()
        if state_storage and version:
            # if we have a state storage and a version, then we can load that state
            # into a tempdir and build definitions from it
            with _temp_state_path() as state_path:
                state_storage.load_state_to_path(key, version, state_path)
                defs = self.build_defs_from_state(context, state_path=state_path)
        else:
            # otherwise, we pass in None to allow indicate that no state is available
            defs = self.build_defs_from_state(context, state_path=None)

        return defs

    @abstractmethod
    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Optional[Path]
    ) -> Definitions:
        """Given a state_path, builds a Definitions object based on the state
        contained at that path.

        Args:
            context (ComponentLoadContext): The context associated with this component load.
            state_path (Optional[Path]): The path to the state file. If no state has been
                previously written to the state store, this will be set to None.

        Returns:
            Definitions: The Definitions object built from the state.
        """

    @abstractmethod
    def write_state_to_path(self, state_path: Path):
        """Fetches and writes required state to a local file."""
        raise NotImplementedError()

    def _get_state_version(self, key: str) -> Optional[str]:
        """Retrieves the version of the state that should be used for the given key.
        If no state is available, returns None.

        Args:
            state_storage (Optional[StateStorage]): The state storage to use to retrieve the state.
            key (str): The key of the component to retrieve the state for.

        Returns:
            Optional[str]: The version of the state that should be used for the given key.
        """
        context = DefinitionsLoadContext.get()
        if context.load_type == DefinitionsLoadType.RECONSTRUCTION:
            # if you're in reconstruction mode, you can grab the version from the metadata
            return context.reconstruction_metadata.get(key)
        else:
            # reconstruction metadata is not available in initialization mode, so we need
            # to fetch the version
            # key, then it will already be available on the DefinitionsLoadContext
            return context.reconstruction_metadata.get(key)

    def refresh_state(self, context: ComponentLoadContext) -> None:
        """Rebuilds the state for this component and persists it to the current StateStore."""
        key = self.get_state_key(context)
        state_storage = StateStorage.get_current()
        if state_storage is None:
            raise DagsterInvalidInvocationError(
                f"Attempted to refresh state of {key} without a StateStorage in context. "
                "This is likely the result of an internal framework error."
            )
        with _temp_state_path() as state_path:
            self.write_state_to_path(state_path)
            state_storage.store_state(key, version=str(uuid.uuid4()), path=state_path)
