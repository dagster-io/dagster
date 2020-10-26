import faker from 'faker';

const hyphenatedName = () => faker.random.words(2).replace(' ', '-').toLowerCase();
const randomId = () => faker.random.uuid();

/**
 * A set of default values to use for Jest GraphQL mocks.
 *
 * MyType: () => ({
 *   someField: () => 'some_value',
 * }),
 */
export const defaultMocks = {
  Pipeline: () => ({
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
    name: hyphenatedName,
  }),
  ScheduleDefinition: () => ({
    name: hyphenatedName,
  }),
  Solid: () => ({
    name: hyphenatedName,
  }),
};
