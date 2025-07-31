import tempfile
from abc import abstractmethod
from collections.abc import Sequence
from pathlib import Path

# class Translator[Generic[T]]:
#     def get_asset_spec(self, input_obj: T) -> AssetSpec:
#         pass
from typing import Annotated, Callable, Generic, Union, cast

from dagster_shared.serdes.serdes import deserialize_value, serialize_value
from typing_extensions import TypeAlias, TypeVar

from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.decorators.op_decorator import op
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_load_context import (
    DefinitionsLoadContext,
    DefinitionsLoadType,
)
from dagster._core.instance import DagsterInstance
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetAttributesModel
from dagster.components.resolved.model import Resolver

T = TypeVar("T")

TranslationFn: TypeAlias = Callable[[AssetSpec, T], AssetSpec]


def resolve_translation(context: ResolutionContext, model):
    pass


ResolvedTranslationFn: TypeAlias = Annotated[
    TranslationFn[T],
    Resolver(
        resolve_translation,
        inject_before_resolve=False,
        model_field_type=Union[str, AssetAttributesModel],
    ),
]


class StateBackedComponent(Component):
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        instance = DefinitionsLoadContext.get_dagster_instance()
        defs_key = context.path.relative_to(context.defs_module_path).as_posix()

        state_file_path = Path("/tmp") / defs_key
        self.retrieve_state_to_path(state_file_path, instance, defs_key)

        @op(name=f"rebuild_state_and_store_in_blobstore_{defs_key}")
        def rebuild_state_and_store_in_blobstore():
            self.build_state_and_persist(instance, defs_key)

        @job(name=f"rebuild_state_and_store_in_blobstore_job_{defs_key}")
        def rebuild_state_and_store_in_blobstore_job():
            rebuild_state_and_store_in_blobstore()

        return Definitions.merge(
            self.build_defs_with_state(context, state_file_path),
            Definitions(jobs=[rebuild_state_and_store_in_blobstore_job]),
        )

    @abstractmethod
    def build_defs_with_state(
        self, context: ComponentLoadContext, state_file_path: Path
    ) -> Definitions:
        raise NotImplementedError()

    @abstractmethod
    def write_state_to_path(self, file_path: Path) -> str:
        """Fetches and writes the state needed by this component to `file_path`.
        Returns a unique identifier for the state file, e.g. a SHA hash.

        Args:
            file_path (Path): The path to write the state to.

        Returns:
            str: A unique identifier for the state file, e.g. a SHA hash.
        """
        raise NotImplementedError()

    def retrieve_state_to_path(
        self, file_path: Path, instance: DagsterInstance, defs_key: str
    ) -> bool:
        """Retrieves saved state for this component to the specified path, if state has been previously
        loaded. Returns True if state was loaded, False otherwise.

        Args:
            path (Path): The path to write the state to.
            instance (DagsterInstance): The instance to use to retrieve the state.
            defs_key (str): The key of the component to retrieve the state for.

        Returns:
            bool: True if state was loaded to the passed file path, False otherwise.
        """
        context = DefinitionsLoadContext.get()

        version = (
            cast("str", deserialize_value(context.reconstruction_metadata[defs_key]))
            if (
                context.load_type == DefinitionsLoadType.RECONSTRUCTION
                and defs_key in context.reconstruction_metadata
            )
            else instance.get_latest_state_version_for_defs(defs_key)
        )
        context.add_to_pending_reconstruction_metadata(defs_key, serialize_value(version))

        return instance.load_state_file(defs_key, version, file_path) if version else False

    def build_state_and_persist(self, instance: DagsterInstance, defs_key: str) -> None:
        """Builds the state for this component and persists it to storage.

        Args:
            instance (DagsterInstance): The instance to use to store the state.
            defs_key (str): The key of the component to store the state for.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            version_id = self.write_state_to_path(path)

            instance.persist_state_from_file(defs_key, version_id, path)


class ApiFetchComponent(StateBackedComponent, Generic[T]):
    translation: ResolvedTranslationFn[T]

    @abstractmethod
    def get_asset_spec(self, input_obj: T) -> AssetSpec:
        pass

    @abstractmethod
    def read_objects_from_path(self, path: Path) -> Sequence[T]:
        return []

    def build_defs_with_state(
        self, context: ComponentLoadContext, state_file_path: Path
    ) -> Definitions:
        objects = self.read_objects_from_path(state_file_path)
        specs = [self.translation(self.get_asset_spec(data), data) for data in objects]
        return Definitions(assets=specs)


class MyComponent(Component):
    translation: ResolvedTranslationFn[str]

    def get_asset_spec(self, input_obj: str) -> AssetSpec:
        return ...

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        data = ["foo", "bar", "baz"]
        specs = [self.translation(self.get_asset_spec(data), data) for data in data]

        return Definitions(assets=specs)
