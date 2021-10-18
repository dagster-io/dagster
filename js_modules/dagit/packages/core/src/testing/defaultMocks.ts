import {MockList} from '@graphql-tools/mock';
import faker from 'faker';

export const hyphenatedName = () => faker.random.words(2).replace(/ /g, '-').toLowerCase();
const randomId = () => faker.random.uuid();

/**
 * A set of default values to use for Jest GraphQL mocks.
 *
 * MyType: () => ({
 *   someField: () => 'some_value',
 * }),
 */
export const defaultMocks = {
  Asset: () => ({
    id: randomId,
  }),
  ISolidDefinition: () => ({
    __typename: 'SolidDefinition',
  }),
  Mode: () => ({
    name: () => 'default',
  }),
  Pipeline: () => ({
    id: randomId,
    isJob: () => false,
    name: hyphenatedName,
    pipelineSnapshotId: randomId,
    schedules: () => new MockList(0),
    sensors: () => new MockList(0),
    solids: () => new MockList(2),
    modes: () => new MockList(1),
  }),
  Query: () => ({
    version: () => 'x.y.z',
  }),
  Repository: () => ({
    id: randomId,
    name: hyphenatedName,
  }),
  RepositoryLocation: () => ({
    id: randomId,
    name: hyphenatedName,
  }),
  Workspace: () => ({
    locationEntries: () => new MockList(1),
  }),
  Schedule: () => ({
    id: hyphenatedName,
    name: hyphenatedName,
    results: () => new MockList(1),
  }),
  Sensor: () => ({
    id: hyphenatedName,
    name: hyphenatedName,
    results: () => new MockList(1),
  }),
  Solid: () => ({
    name: hyphenatedName,
  }),

  // Disambiguate error unions. If you'd like to mock an error, define a custom mock
  // for the type.
  RepositoriesOrError: () => ({
    __typename: 'RepositoryConnection',
  }),
  DagsterTypeOrError: () => ({
    __typename: 'RegularDagsterType',
  }),
  PipelineRunStatsOrError: () => ({
    __typename: 'PipelineRunStatsSnapshot',
  }),
  PipelineRunOrError: () => ({
    __typename: 'PipelineRun',
  }),
  PartitionsOrError: () => ({
    __typename: 'Partitions',
  }),
  PartitionRunConfigOrError: () => ({
    __typename: 'PartitionRunConfig',
  }),
  PartitionTagsOrError: () => ({
    __typename: 'PartitionTags',
  }),
  PartitionStatusesOrError: () => ({
    __typename: 'PartitionStatuses',
  }),
  RepositoryOrError: () => ({
    __typename: 'Repository',
  }),
  WorkspaceOrError: () => ({
    __typename: 'Workspace',
  }),
  RepositoryLocationOrLoadError: () => ({
    __typename: 'RepositoryLocation',
  }),
  PipelineOrError: () => ({
    __typename: 'Pipeline',
  }),
  PipelineSnapshotOrError: () => ({
    __typename: 'PipelineSnapshot',
  }),
  SchedulerOrError: () => ({
    __typename: 'Scheduler',
  }),
  ScheduleOrError: () => ({
    __typename: 'Schedule',
  }),
  SchedulesOrError: () => ({
    __typename: 'Schedules',
  }),
  SensorOrError: () => ({
    __typename: 'Sensor',
  }),
  SensorsOrError: () => ({
    __typename: 'Sensors',
  }),
  JobStateOrError: () => ({
    __typename: 'JobState',
  }),
  JobStatesOrError: () => ({
    __typename: 'JobStates',
  }),
  PartitionSetsOrError: () => ({
    __typename: 'PartitionSets',
  }),
  PartitionSetOrError: () => ({
    __typename: 'PartitionSet',
  }),
  PipelineRunsOrError: () => ({
    __typename: 'PipelineRuns',
  }),
  RunGroupOrError: () => ({
    __typename: 'RunGroup',
  }),
  ExecutionPlanOrError: () => ({
    __typename: 'ExecutionPlan',
  }),
  RunConfigSchemaOrError: () => ({
    __typename: 'RunConfigSchema',
  }),
  AssetsOrError: () => ({
    __typename: 'AssetConnection',
  }),
  AssetOrError: () => ({
    __typename: 'Asset',
  }),
  AssetNodeOrError: () => ({
    __typename: 'AssetNode',
  }),
  PartitionBackfillOrError: () => ({
    __typename: 'PartitionBackfill',
  }),
  PartitionBackfillsOrError: () => ({
    __typename: 'PartitionBackfills',
  }),
  StopSensorMutationResultOrError: () => ({
    __typename: 'StopSensorMutationResult',
  }),
  ConfigTypeOrError: () => ({
    __typename: 'EnumConfigType',
  }),
};
