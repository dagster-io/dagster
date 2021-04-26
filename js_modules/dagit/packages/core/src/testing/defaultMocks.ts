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
  Pipeline: () => ({
    id: randomId,
    name: hyphenatedName,
    pipelineSnapshotId: randomId,
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
