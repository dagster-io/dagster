from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, FrozenSet, List, Optional

import dagster._check as check
from dagster.core.definitions.events import AssetKey
from dagster.core.errors import DagsterInvalidSubsetError
from dagster.core.selector import parse_solid_selection

if TYPE_CHECKING:
    from .pipeline_definition import PipelineDefinition


class IPipeline(ABC):
    """
    IPipeline is a wrapper interface for PipelineDefinitions to be used as parameters to Dagster's
    core execution APIs.  This enables these execution APIs to operate on both in memory pipeline
    definitions to be executed in the current process (InMemoryPipeline) as well as definitions that
    can be reconstructed and executed in a different process (ReconstructablePipeline).
    """

    @abstractmethod
    def get_definition(self) -> "PipelineDefinition":
        pass

    @abstractmethod
    def subset_for_execution(
        self,
        solid_selection: Optional[List[str]] = None,
        asset_selection: Optional[FrozenSet[AssetKey]] = None,
    ) -> "IPipeline":
        pass

    @property
    @abstractmethod
    def solids_to_execute(self) -> Optional[FrozenSet[str]]:
        pass

    @abstractmethod
    def subset_for_execution_from_existing_pipeline(
        self,
        solids_to_execute: Optional[FrozenSet[str]] = None,
        asset_selection: Optional[FrozenSet[AssetKey]] = None,
    ) -> "IPipeline":
        pass


class InMemoryPipeline(IPipeline, object):
    def __init__(
        self, pipeline_def, solid_selection=None, solids_to_execute=None, asset_selection=None
    ):
        self._pipeline_def = pipeline_def
        self._solid_selection = solid_selection
        self._solids_to_execute = solids_to_execute
        self._asset_selection = asset_selection

    def get_definition(self):
        return self._pipeline_def

    def _resolve_solid_selection(self, solid_selection):
        # resolve a list of solid selection queries to a frozenset of qualified solid names
        # e.g. ['foo_solid+'] to {'foo_solid', 'bar_solid'}
        check.list_param(solid_selection, "solid_selection", of_type=str)
        solids_to_execute = parse_solid_selection(self.get_definition(), solid_selection)
        if len(solids_to_execute) == 0:
            node_type = "ops" if self._pipeline_def.is_job else "solids"
            selection_type = "op_selection" if self._pipeline_def.is_job else "solid_selection"
            raise DagsterInvalidSubsetError(
                "No qualified {node_type} to execute found for {selection_type}={requested}".format(
                    node_type=node_type, requested=solid_selection, selection_type=selection_type
                )
            )
        return solids_to_execute

    def _subset_for_execution(self, solids_to_execute, solid_selection=None, asset_selection=None):
        if asset_selection:
            return InMemoryPipeline(
                self._pipeline_def.get_job_def_for_subset_selection(
                    asset_selection=asset_selection
                ),
                asset_selection=asset_selection,
            )
        if self._pipeline_def.is_subset_pipeline:
            return InMemoryPipeline(
                self._pipeline_def.parent_pipeline_def.get_pipeline_subset_def(solids_to_execute),
                solid_selection=solid_selection,
                solids_to_execute=solids_to_execute,
            )

        return InMemoryPipeline(
            self._pipeline_def.get_pipeline_subset_def(solids_to_execute),
            solid_selection=solid_selection,
            solids_to_execute=solids_to_execute,
        )

    def subset_for_execution(
        self,
        solid_selection: Optional[List[str]] = None,
        asset_selection: Optional[FrozenSet[AssetKey]] = None,
    ):
        # take a list of solid queries and resolve the queries to names of solids to execute
        solid_selection = check.opt_list_param(solid_selection, "solid_selection", of_type=str)
        check.opt_set_param(asset_selection, "asset_selection", of_type=AssetKey)

        check.invariant(
            not (solid_selection and asset_selection),
            "solid_selection and asset_selection cannot both be provided as arguments",
        )

        solids_to_execute = (
            self._resolve_solid_selection(solid_selection) if solid_selection else None
        )
        return self._subset_for_execution(solids_to_execute, solid_selection, asset_selection)

    def subset_for_execution_from_existing_pipeline(
        self,
        solids_to_execute: Optional[FrozenSet[str]] = None,
        asset_selection: Optional[FrozenSet[AssetKey]] = None,
    ):
        # take a frozenset of resolved solid names from an existing pipeline run
        # so there's no need to parse the selection
        check.opt_set_param(solids_to_execute, "solids_to_execute", of_type=str)
        check.opt_set_param(asset_selection, "asset_selection", of_type=AssetKey)

        check.invariant(
            not (solids_to_execute and asset_selection),
            "solids_to_execute and asset_selection cannot both be provided as arguments",
        )

        return self._subset_for_execution(solids_to_execute, asset_selection=asset_selection)

    @property
    def solid_selection(self) -> List[str]:
        # a list of solid queries provided by the user
        return self._solid_selection  # List[str]

    @property
    def solids_to_execute(self) -> FrozenSet[str]:
        # a frozenset which contains the names of the solids to execute
        return self._solids_to_execute  # FrozenSet[str]

    @property
    def asset_selection(self) -> FrozenSet[AssetKey]:
        return self._asset_selection
