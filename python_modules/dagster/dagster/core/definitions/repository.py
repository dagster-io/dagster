from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.utils import merge_dicts

from .partition import PartitionScheduleDefinition, PartitionSetDefinition
from .pipeline import PipelineDefinition
from .schedule import ScheduleDefinition
from .sensor import SensorDefinition
from .utils import check_valid_name

VALID_REPOSITORY_DATA_DICT_KEYS = {
    "pipelines",
    "partition_sets",
    "schedules",
    "sensors",
}


class _CacheingDefinitionIndex:
    def __init__(
        self,
        definition_class,
        definition_class_name,
        definition_kind,
        definitions,
        validation_fn,
    ):

        for key, definition in definitions.items():
            check.invariant(
                isinstance(definition, definition_class) or callable(definition),
                "Bad definition for {definition_kind} {key}: must be {definition_class_name} or "
                "callable, got {type_}".format(
                    definition_kind=definition_kind,
                    key=key,
                    definition_class_name=definition_class_name,
                    type_=type(definition),
                ),
            )

        self._definition_class = definition_class
        self._definition_class_name = definition_class_name
        self._definition_kind = definition_kind
        self._validation_fn = validation_fn

        self._definitions = definitions
        self._definition_cache = {}
        self._definition_names = None
        self._all_definitions = None

    def get_definition_names(self):
        if self._definition_names:
            return self._definition_names

        self._definition_names = list(self._definitions.keys())
        return self._definition_names

    def has_definition(self, definition_name):
        check.str_param(definition_name, "definition_name")

        return definition_name in self.get_definition_names()

    def get_all_definitions(self):
        if self._all_definitions is not None:
            return self._all_definitions

        self._all_definitions = list(
            sorted(
                map(self.get_definition, self.get_definition_names()),
                key=lambda definition: definition.name,
            )
        )
        return self._all_definitions

    def get_definition(self, definition_name):
        check.str_param(definition_name, "definition_name")

        if definition_name in self._definition_cache:
            return self._definition_cache[definition_name]

        if definition_name not in self._definitions:
            raise DagsterInvariantViolationError(
                "Could not find {definition_kind} '{definition_name}'. Found: "
                "{found_names}.".format(
                    definition_kind=self._definition_kind,
                    definition_name=definition_name,
                    found_names=", ".join(
                        [
                            "'{found_name}'".format(found_name=found_name)
                            for found_name in self.get_definition_names()
                        ]
                    ),
                )
            )

        definition_source = self._definitions[definition_name]

        if isinstance(definition_source, self._definition_class):
            self._definition_cache[definition_name] = self._validation_fn(definition_source)
            return definition_source
        else:
            definition = definition_source()
            check.invariant(
                isinstance(definition, self._definition_class),
                "Bad constructor for {definition_kind} {definition_name}: must return "
                "{definition_class_name}, got value of type {type_}".format(
                    definition_kind=self._definition_kind,
                    definition_name=definition_name,
                    definition_class_name=self._definition_class_name,
                    type_=type(definition),
                ),
            )
            check.invariant(
                definition.name == definition_name,
                "Bad constructor for {definition_kind} '{definition_name}': name in "
                "{definition_class_name} does not match: got '{definition_def_name}'".format(
                    definition_kind=self._definition_kind,
                    definition_name=definition_name,
                    definition_class_name=self._definition_class_name,
                    definition_def_name=definition.name,
                ),
            )
            self._definition_cache[definition_name] = self._validation_fn(definition)
            return definition


class RepositoryData:
    """Contains definitions belonging to a repository.

    Users should usually rely on the :py:func:`@repository <repository>` decorator to create new
    repositories, which will in turn call the static constructors on this class. However, users may
    subclass RepositoryData for fine-grained control over access to and lazy creation
    of repository members.
    """

    def __init__(self, pipelines, partition_sets, schedules, sensors):
        """Constructs a new RepositoryData object.

        You may pass pipeline, partition_set, and schedule definitions directly, or you may pass
        callables with no arguments that will be invoked to lazily construct definitions when
        accessed by name. This can be helpful for performance when there are many definitions in a
        repository, or when constructing the definitions is costly.

        Note that when lazily constructing a definition, the name of the definition must match its
        key in its dictionary index, or a :py:class:`DagsterInvariantViolationError` will be thrown
        at retrieval time.

        Args:
            pipelines (Dict[str, Union[PipelineDefinition, Callable[[], PipelineDefinition]]]):
                The pipeline definitions belonging to the repository.
            partition_sets (Dict[str, Union[PartitionSetDefinition, Callable[[], PartitionSetDefinition]]]):
                The partition sets belonging to the repository.
            schedules (Dict[str, Union[ScheduleDefinition, Callable[[], ScheduleDefinition]]]):
                The schedules belonging to the repository.
            sensors (Dict[str, Union[SensorDefinition, Callable[[], SensorDefinition]]]):
                The sensors belonging to a repository.

        """
        check.dict_param(pipelines, "pipelines", key_type=str)
        check.dict_param(partition_sets, "partition_sets", key_type=str)
        check.dict_param(schedules, "schedules", key_type=str)
        check.dict_param(sensors, "sensors", key_type=str)

        self._pipelines = _CacheingDefinitionIndex(
            PipelineDefinition, "PipelineDefinition", "pipeline", pipelines, self._validate_pipeline
        )

        self._schedules = _CacheingDefinitionIndex(
            ScheduleDefinition,
            "ScheduleDefinition",
            "schedule",
            schedules,
            self._validate_schedule,
        )
        schedule_partition_sets = [
            schedule.get_partition_set()
            for schedule in self._schedules.get_all_definitions()
            if isinstance(schedule, PartitionScheduleDefinition)
        ]
        self._partition_sets = _CacheingDefinitionIndex(
            PartitionSetDefinition,
            "PartitionSetDefinition",
            "partition set",
            merge_dicts(
                {partition_set.name: partition_set for partition_set in schedule_partition_sets},
                partition_sets,
            ),
            self._validate_partition_set,
        )
        self._sensors = _CacheingDefinitionIndex(
            SensorDefinition,
            "SensorDefinition",
            "sensor",
            sensors,
            self._validate_sensor,
        )
        # load all sensors to force validation
        self._sensors.get_all_definitions()

        self._all_pipelines = None
        self._solids = None
        self._all_solids = None

    @staticmethod
    def from_dict(repository_definitions):
        """Static constructor.

        Args:
            repository_definition (Dict[str, Dict[str, ...]]): A dict of the form:

                {
                    'pipelines': Dict[str, Callable[[], PipelineDefinition]],
                    'partition_sets': Dict[str, Callable[[], PartitionSetDefinition]],
                    'schedules': Dict[str, Callable[[], ScheduleDefinition]]
                }

            This form is intended to allow definitions to be created lazily when accessed by name,
            which can be helpful for performance when there are many definitions in a repository, or
            when constructing the definitions is costly.
        """
        check.dict_param(repository_definitions, "repository_definitions", key_type=str)
        check.invariant(
            set(repository_definitions.keys()).issubset(VALID_REPOSITORY_DATA_DICT_KEYS),
            "Bad dict: must not contain keys other than {{{valid_keys}}}: found {bad_keys}.".format(
                valid_keys=", ".join(
                    ["'{key}'".format(key=key) for key in VALID_REPOSITORY_DATA_DICT_KEYS]
                ),
                bad_keys=", ".join(
                    [
                        "'{key}'"
                        for key in repository_definitions.keys()
                        if key not in VALID_REPOSITORY_DATA_DICT_KEYS
                    ]
                ),
            ),
        )

        for key in VALID_REPOSITORY_DATA_DICT_KEYS:
            if key not in repository_definitions:
                repository_definitions[key] = {}

        duplicate_keys = set(repository_definitions.get("schedules", {}).keys()).intersection(
            set(repository_definitions.get("sensors", {}).keys())
        )
        if duplicate_keys:
            raise DagsterInvalidDefinitionError(
                f"Duplicate definitions found for keys: {duplicate_keys.join(', ')}"
            )

        return RepositoryData(**repository_definitions)

    @classmethod
    def from_list(cls, repository_definitions):
        """Static constructor.

        Args:
            repository_definition (List[Union[PipelineDefinition, PartitionSetDefinition, ScheduleDefinition]]):
                Use this constructor when you have no need to lazy load pipelines or other
                definitions.
        """
        pipelines = {}
        partition_sets = {}
        schedules = {}
        sensors = {}
        jobs = {}
        for definition in repository_definitions:
            if isinstance(definition, PipelineDefinition):
                if definition.name in pipelines:
                    raise DagsterInvalidDefinitionError(
                        "Duplicate pipeline definition found for pipeline {pipeline_name}".format(
                            pipeline_name=definition.name
                        )
                    )
                pipelines[definition.name] = definition
            elif isinstance(definition, PartitionSetDefinition):
                if definition.name in partition_sets:
                    raise DagsterInvalidDefinitionError(
                        "Duplicate partition set definition found for partition set "
                        "{partition_set_name}".format(partition_set_name=definition.name)
                    )
                partition_sets[definition.name] = definition
            elif isinstance(definition, SensorDefinition):
                if definition.name in jobs:
                    raise DagsterInvalidDefinitionError(
                        f"Duplicate definition found for {definition.name}"
                    )
                jobs[definition.name] = definition
                sensors[definition.name] = definition
            elif isinstance(definition, ScheduleDefinition):
                if definition.name in jobs:
                    raise DagsterInvalidDefinitionError(
                        f"Duplicate definition found for {definition.name}"
                    )
                jobs[definition.name] = definition
                schedules[definition.name] = definition

                if isinstance(definition, PartitionScheduleDefinition):
                    partition_set_def = definition.get_partition_set()
                    if (
                        partition_set_def.name in partition_sets
                        and partition_set_def != partition_sets[partition_set_def.name]
                    ):
                        raise DagsterInvalidDefinitionError(
                            "Duplicate partition set definition found for partition set "
                            "{partition_set_name}".format(partition_set_name=partition_set_def.name)
                        )
                    partition_sets[partition_set_def.name] = partition_set_def

        return RepositoryData(
            pipelines=pipelines,
            partition_sets=partition_sets,
            schedules=schedules,
            sensors=sensors,
        )

    def get_pipeline_names(self):
        """Get the names of all pipelines in the repository.

        Returns:
            List[str]
        """
        return self._pipelines.get_definition_names()

    def has_pipeline(self, pipeline_name):
        """Check if a pipeline with a given name is present in the repository.

        Args:
            pipeline_name (str): The name of the pipeline.

        Returns:
            bool
        """
        check.str_param(pipeline_name, "pipeline_name")
        return self._pipelines.has_definition(pipeline_name)

    def get_all_pipelines(self):
        """Return all pipelines in the repository as a list.

        Note that this will construct any pipeline that has not yet been constructed.

        Returns:
            List[PipelineDefinition]: All pipelines in the repository.
        """
        if self._all_pipelines is not None:
            return self._all_pipelines

        self._all_pipelines = self._pipelines.get_all_definitions()
        self.get_all_solid_defs()
        return self._all_pipelines

    def get_pipeline(self, pipeline_name):
        """Get a pipeline by name.

        If this pipeline has not yet been constructed, only this pipeline is constructed, and will
        be cached for future calls.

        Args:
            pipeline_name (str): Name of the pipeline to retrieve.

        Returns:
            PipelineDefinition: The pipeline definition corresponding to the given name.
        """

        check.str_param(pipeline_name, "pipeline_name")

        return self._pipelines.get_definition(pipeline_name)

    def get_partition_set_names(self):
        """Get the names of all partition sets in the repository.

        Returns:
            List[str]
        """
        return self._partition_sets.get_definition_names()

    def has_partition_set(self, partition_set_name):
        """Check if a partition set with a given name is present in the repository.

        Args:
            partition_set_name (str): The name of the partition set.

        Returns:
            bool
        """
        check.str_param(partition_set_name, "partition_set_name")
        return self._partition_sets.has_definition(partition_set_name)

    def get_all_partition_sets(self):
        """Return all partition sets in the repository as a list.

        Note that this will construct any partition set that has not yet been constructed.

        Returns:
            List[PartitionSetDefinition]: All partition sets in the repository.
        """
        return self._partition_sets.get_all_definitions()

    def get_partition_set(self, partition_set_name):
        """Get a partition set by name.

        If this partition set has not yet been constructed, only this partition set is constructed,
        and will be cached for future calls.

        Args:
            partition_set_name (str): Name of the partition set to retrieve.

        Returns:
            PartitionSetDefinition: The partition set definition corresponding to the given name.
        """

        check.str_param(partition_set_name, "partition_set_name")

        return self._partition_sets.get_definition(partition_set_name)

    def get_schedule_names(self):
        """Get the names of all schedules in the repository.

        Returns:
            List[str]
        """
        return self._schedules.get_definition_names()

    def get_all_schedules(self):
        """Return all schedules in the repository as a list.

        Note that this will construct any schedule that has not yet been constructed.

        Returns:
            List[ScheduleDefinition]: All pipelines in the repository.
        """
        return self._schedules.get_all_definitions()

    def get_schedule(self, schedule_name):
        """Get a schedule by name.

        if this schedule has not yet been constructed, only this schedule is constructed, and will
        be cached for future calls.

        args:
            schedule_name (str): name of the schedule to retrieve.

        Returns:
            ScheduleDefinition: The schedule definition corresponding to the given name.
        """

        check.str_param(schedule_name, "schedule_name")

        return self._schedules.get_definition(schedule_name)

    def has_schedule(self, schedule_name):
        check.str_param(schedule_name, "schedule_name")

        return self._schedules.has_definition(schedule_name)

    def get_all_sensors(self):
        return self._sensors.get_all_definitions()

    def get_sensor(self, name):
        return self._sensors.get_definition(name)

    def has_sensor(self, name):
        return self._sensors.has_definition(name)

    def get_all_solid_defs(self):
        if self._all_solids is not None:
            return self._all_solids

        self._all_solids = self._construct_solid_defs()
        return list(self._all_solids.values())

    def has_solid(self, solid_name):
        if self._all_solids is not None:
            return solid_name in self._all_solids

        self._all_solids = self._construct_solid_defs()
        return solid_name in self._all_solids

    def _construct_solid_defs(self):
        solid_defs = {}
        solid_to_pipeline = {}
        # This looks like it should infinitely loop but the
        # memoization of _all_pipelines and _all_solids short
        # circuits that
        for pipeline in self.get_all_pipelines():
            for solid_def in pipeline.all_solid_defs:
                if solid_def.name not in solid_defs:
                    solid_defs[solid_def.name] = solid_def
                    solid_to_pipeline[solid_def.name] = pipeline.name

                if not solid_defs[solid_def.name] is solid_def:
                    first_name, second_name = sorted(
                        [solid_to_pipeline[solid_def.name], pipeline.name]
                    )
                    raise DagsterInvalidDefinitionError(
                        (
                            "Duplicate solids found in repository with name '{solid_def_name}'. "
                            "Solid definition names must be unique within a repository. Solid is "
                            "defined in pipeline '{first_pipeline_name}' and in pipeline "
                            "'{second_pipeline_name}'."
                        ).format(
                            solid_def_name=solid_def.name,
                            first_pipeline_name=first_name,
                            second_pipeline_name=second_name,
                        )
                    )

        return solid_defs

    def solid_def_named(self, name):
        """Get the solid with the given name in the repository.

        Args:
            name (str): The name of the solid for which to retrieve the solid definition.

        Returns:
            SolidDefinition: The solid with the given name.
        """
        check.str_param(name, "name")

        if not self.has_solid(name):
            check.failed("could not find solid_def for solid {name}".format(name=name))

        return self._all_solids[name]

    def _validate_pipeline(self, pipeline):
        return pipeline

    def _validate_schedule(self, schedule):
        pipelines = self.get_pipeline_names()

        if schedule.pipeline_name not in pipelines:
            raise DagsterInvalidDefinitionError(
                f'ScheduleDefinition "{schedule.name}" targets pipeline "{schedule.pipeline_name}" '
                "which was not found in this repository."
            )

        return schedule

    def _validate_sensor(self, sensor):
        pipelines = self.get_pipeline_names()

        if sensor.pipeline_name not in pipelines:
            raise DagsterInvalidDefinitionError(
                f'SensorDefinition "{sensor.name}" targets pipeline "{sensor.pipeline_name}" '
                "which was not found in this repository."
            )

        return sensor

    def _validate_partition_set(self, partition_set):
        return partition_set


class RepositoryDefinition:
    """Define a repository that contains a collection of definitions.

    Users should typically not create objects of this class directly. Instead, use the
    :py:func:`@repository` decorator.

    Args:
        name (str): The name of the repository.
        repository_data (RepositoryData): Contains the definitions making up the repository.
        description (Optional[str]): A string description of the repository.
    """

    def __init__(
        self,
        name,
        repository_data,
        description=None,
    ):
        self._name = check_valid_name(name)
        self._description = check.opt_str_param(description, "description")
        self._repository_data = check.inst_param(repository_data, "repository_data", RepositoryData)

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def pipeline_names(self):
        """List[str]: Names of all pipelines in the repository"""
        return self._repository_data.get_pipeline_names()

    def has_pipeline(self, name):
        """Check if a pipeline with a given name is present in the repository.

        Args:
            name (str): The name of the pipeline.

        Returns:
            bool
        """
        return self._repository_data.has_pipeline(name)

    def get_pipeline(self, name):
        """Get a pipeline by name.

        If this pipeline is present in the lazily evaluated ``pipeline_dict`` passed to the
        constructor, but has not yet been constructed, only this pipeline is constructed, and will
        be cached for future calls.

        Args:
            name (str): Name of the pipeline to retrieve.

        Returns:
            PipelineDefinition: The pipeline definition corresponding to the given name.
        """
        return self._repository_data.get_pipeline(name)

    def get_all_pipelines(self):
        """Return all pipelines in the repository as a list.

        Note that this will construct any pipeline in the lazily evaluated ``pipeline_dict`` that
        has not yet been constructed.

        Returns:
            List[PipelineDefinition]: All pipelines in the repository.
        """
        return self._repository_data.get_all_pipelines()

    def get_all_solid_defs(self):
        """Get all the solid definitions in a repository.

        Returns:
            List[SolidDefinition]: All solid definitions in the repository.
        """
        return self._repository_data.get_all_solid_defs()

    def solid_def_named(self, name):
        """Get the solid with the given name in the repository.

        Args:
            name (str): The name of the solid for which to retrieve the solid definition.

        Returns:
            SolidDefinition: The solid with the given name.
        """
        check.str_param(name, "name")
        return self._repository_data.solid_def_named(name)

    @property
    def partition_set_defs(self):
        return self._repository_data.get_all_partition_sets()

    def get_partition_set_def(self, name):
        return self._repository_data.get_partition_set(name)

    @property
    def schedule_defs(self):
        return self._repository_data.get_all_schedules()

    def get_schedule_def(self, name):
        return self._repository_data.get_schedule(name)

    def has_schedule_def(self, name):
        return self._repository_data.has_schedule(name)

    @property
    def sensor_defs(self):
        return self._repository_data.get_all_sensors()

    def get_sensor_def(self, name):
        return self._repository_data.get_sensor(name)

    def has_sensor_def(self, name):
        return self._repository_data.has_sensor(name)

    # If definition comes from the @repository decorator, then the __call__ method will be
    # overwritten. Therefore, we want to maintain the call-ability of repository definitions.
    def __call__(self, *args, **kwargs):
        return self
