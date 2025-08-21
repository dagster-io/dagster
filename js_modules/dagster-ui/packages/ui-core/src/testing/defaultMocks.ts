import faker from 'faker';

import {RepositoryLocationLoadStatus, RunStatus} from '../graphql/types';

export const hyphenatedName = (wordCount = 2) =>
  faker.random.words(wordCount).replace(/ /g, '-').toLowerCase();
const randomId = () => faker.datatype.uuid();

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
  AssetKey: () => ({
    path: faker.random.words(faker.datatype.number({min: 1, max: 3})).split(' '),
  }),
  AssetCheck: () => ({
    name: hyphenatedName(),
    assetKey: {
      path: faker.random.words(faker.datatype.number({min: 1, max: 3})).split(' '),
    },
  }),
  AssetNode: () => ({
    id: randomId,
    opName: hyphenatedName,
    metadataEntries: () => [],
  }),
  AssetGroup: () => ({
    groupName: hyphenatedName,
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
    isAssetJob: () => false,
    name: hyphenatedName,
    pipelineSnapshotId: randomId,
    schedules: () => [],
    sensors: () => [],
    solids: () => [...new Array(2)],
    modes: () => [...new Array(1)],
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
    id: 'workspace',
    locationEntries: () => [...new Array(1)],
  }),
  WorkspaceLocationEntry: () => ({
    id: randomId,
    loadStatus: () => RepositoryLocationLoadStatus.LOADED,
  }),
  WorkspaceLocationStatusEntries: () => ({
    entries: () => [...new Array(1)],
  }),
  WorkspaceLocationStatusEntry: () => ({
    id: randomId,
    loadStatus: () => RepositoryLocationLoadStatus.LOADED,
    updateTimestamp: () => 0,
  }),
  Schedule: () => ({
    id: hyphenatedName,
    name: hyphenatedName,
    results: () => [...new Array(1)],
  }),
  Sensor: () => ({
    id: hyphenatedName,
    name: hyphenatedName,
    results: () => [...new Array(1)],
  }),
  Solid: () => ({
    name: hyphenatedName,
  }),
  PythonError: () => ({
    message: () => 'A wild python error appeared!',
    stack: () => [],
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
  RunStatsSnapshotOrError: () => ({
    __typename: 'RunStatsSnapshot',
  }),
  PipelineRunOrError: () => ({
    __typename: 'PipelineRun',
  }),
  RunOrError: () => ({
    __typename: 'Run',
  }),
  RunsFeedEntry: () => ({
    __typename: 'Run',
    assetSelection: () => {
      const count = faker.datatype.number({min: 0, max: 8});
      return [...new Array(count)].map(() => ({
        path: faker.random.words(faker.datatype.number({min: 1, max: 3})).split(' '),
      }));
    },
    assetCheckSelection: () => {
      const count = faker.datatype.number({min: 0, max: 5});
      return [...new Array(count)].map(() => ({
        name: hyphenatedName(),
        assetKey: {
          path: faker.random.words(faker.datatype.number({min: 1, max: 3})).split(' '),
        },
      }));
    },
  }),
  Run: () => ({
    id: randomId,
    jobName: hyphenatedName,
    runStatus: faker.random.arrayElement([
      RunStatus.SUCCESS,
      RunStatus.SUCCESS, // Weight SUCCESS more heavily
      RunStatus.STARTED,
      RunStatus.FAILURE,
      RunStatus.QUEUED,
      RunStatus.STARTING,
      RunStatus.NOT_STARTED,
      RunStatus.CANCELING,
      RunStatus.CANCELED,
    ]),
    creationTime: Date.now() / 1000 - faker.datatype.number({min: 60, max: 86400}),
    startTime: faker.datatype.boolean()
      ? Date.now() / 1000 - faker.datatype.number({min: 60, max: 3600})
      : null,
    endTime: faker.datatype.boolean()
      ? Date.now() / 1000 - faker.datatype.number({min: 30, max: 1800})
      : null,
    tags: () => {
      const baseTags = [...new Array(faker.datatype.number({min: 5, max: 12}))].map(() => ({
        key: faker.random.arrayElement([
          'dagster/agent_id',
          'dagster/git_commit_hash',
          'dagster/image',
          'dagster/from_ui',
          'environment',
          'team',
          'partition_date',
          'retry_count',
          'priority',
          'source_system',
          'file_size',
          'materialization_count',
          'backfill_range',
          'total_partitions',
          'trigger_file',
          'data_version',
        ]),
        value: faker.random.arrayElement([
          faker.datatype.uuid().slice(0, 8),
          faker.git.commitSha().slice(0, 12),
          `${faker.internet.domainName()}/${hyphenatedName()}:${faker.system.semver()}`,
          faker.datatype.boolean().toString(),
          faker.random.arrayElement(['production', 'staging', 'development']),
          faker.random.arrayElement(['data-engineering', 'analytics', 'ml-ops']),
          faker.date.recent().toISOString().slice(0, 10),
          faker.datatype.number({min: 0, max: 3}).toString(),
          faker.random.arrayElement(['high', 'medium', 'low']),
          faker.random.arrayElement(['external_api', 'file_system', 'database']),
          faker.datatype.number({min: 1024, max: 10485760}).toString(),
          faker.datatype.number({min: 1, max: 100}).toString(),
          `${faker.date.past().toISOString().slice(0, 10)}:${faker.date.recent().toISOString().slice(0, 10)}`,
          faker.datatype.number({min: 1, max: 50}).toString(),
          faker.system.filePath(),
          faker.datatype.number().toString(),
        ]),
      }));

      // 80% chance to add launch type tags for realistic distribution
      const launchTags = [];
      if (faker.datatype.number({min: 1, max: 10}) <= 8) {
        const launchType = faker.random.arrayElement([
          'user',
          'schedule',
          'sensor',
          'automation',
          'backfill',
        ]);

        switch (launchType) {
          case 'user':
            launchTags.push({key: 'user', value: faker.internet.email()});
            break;
          case 'schedule':
            launchTags.push({key: 'dagster/schedule_name', value: `${hyphenatedName()}_schedule`});
            break;
          case 'sensor':
            launchTags.push({key: 'dagster/sensor_name', value: `${hyphenatedName()}_sensor`});
            break;
          case 'automation':
            launchTags.push(
              {key: 'dagster/auto_materialize', value: 'true'},
              {key: 'dagster/from_automation_condition', value: 'true'},
              {key: 'dagster/sensor_name', value: 'default_automation_condition_sensor'},
            );
            break;
          case 'backfill':
            launchTags.push(
              {key: 'dagster/backfill', value: faker.datatype.uuid().slice(0, 8)},
              {key: 'user', value: faker.internet.email()},
            );
            break;
        }
      }

      return [...baseTags, ...launchTags];
    },
    assetSelection: () => {
      const count = faker.datatype.number({min: 0, max: 8});
      return [...new Array(count)].map(() => ({
        path: faker.random.words(faker.datatype.number({min: 1, max: 3})).split(' '),
      }));
    },
    assetCheckSelection: () => {
      const count = faker.datatype.number({min: 0, max: 5});
      return [...new Array(count)].map(() => ({
        name: hyphenatedName(),
        assetKey: {
          path: faker.random.words(faker.datatype.number({min: 1, max: 3})).split(' '),
        },
      }));
    },
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
  RunsOrError: () => ({
    __typename: 'Runs',
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
  InstigationStatesOrError: () => ({
    __typename: 'InstigationStates',
  }),
  LocationStatusesOrError: () => ({
    __typename: 'WorkspaceLocationStatusEntries',
  }),
};
