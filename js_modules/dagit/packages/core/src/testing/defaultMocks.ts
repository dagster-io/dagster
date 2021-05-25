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
  AssetOrError: () => ({
    __typename: 'Asset',
  }),
  ISolidDefinition: () => ({
    __typename: 'SolidDefinition',
  }),
  PartitionSetOrError: () => ({
    __typename: 'PartitionSetOrError',
  }),
  PartitionSetsOrError: () => ({
    __typename: 'PartitionSets',
  }),
  Pipeline: () => ({
    id: randomId,
    name: hyphenatedName,
    pipelineSnapshotId: randomId,
    solids: () => new MockList(2),
  }),
  PipelineOrError: () => ({
    __typename: 'Pipeline',
  }),
  PipelineRunOrError: () => ({
    __typename: 'PipelineRun',
  }),
  PipelineRunStatsOrError: () => ({
    __typename: 'PipelineRunStatsSnapshot',
  }),
  PipelineSnapshotOrError: () => ({
    __typename: 'PipelineSnapshot',
  }),
  Query: () => ({
    version: () => 'x.y.z',
  }),
  RepositoriesOrError: () => ({
    __typename: 'RepositoryConnection',
  }),
  Repository: () => ({
    id: randomId,
    name: hyphenatedName,
  }),
  RepositoryOrError: () => ({
    __typename: 'Repository',
  }),
  RepositoryLocation: () => ({
    id: randomId,
    name: hyphenatedName,
  }),
  RepositoryLocationConnection: () => ({
    nodes: () => new MockList(1),
  }),
  Workspace: () => ({
    locationEntries: () => new MockList(1),
  }),
  RepositoryLocationOrLoadError: () => ({
    __typename: 'RepositoryLocation',
  }),
  RepositoryLocationOrLoadFailure: () => ({
    __typename: 'RepositoryLocation',
  }),
  RepositoryLocationsOrError: () => ({
    __typename: 'RepositoryLocationConnection',
  }),
  Schedule: () => ({
    id: hyphenatedName,
    name: hyphenatedName,
    results: () => new MockList(1),
  }),
  SchedulesOrError: () => ({
    __typename: 'Schedules',
  }),
  Sensor: () => ({
    id: hyphenatedName,
    name: hyphenatedName,
    results: () => new MockList(1),
  }),
  SensorsOrError: () => ({
    __typename: 'Sensors',
  }),
  Solid: () => ({
    name: hyphenatedName,
  }),
};
