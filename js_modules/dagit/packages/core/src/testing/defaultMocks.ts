import {MockList} from '@graphql-tools/mock';
import faker from 'faker';

const hyphenatedName = () => faker.random.words(2).replace(/ /g, '-').toLowerCase();
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
  RepositoryLocationOrLoadFailure: () => ({
    __typename: 'RepositoryLocation',
  }),
  RepositoryLocationsOrError: () => ({
    __typename: 'RepositoryLocationConnection',
  }),
  Schedule: () => ({
    id: hyphenatedName,
    name: hyphenatedName,
  }),
  Sensor: () => ({
    id: hyphenatedName,
    name: hyphenatedName,
  }),
  Solid: () => ({
    name: hyphenatedName,
  }),
};
