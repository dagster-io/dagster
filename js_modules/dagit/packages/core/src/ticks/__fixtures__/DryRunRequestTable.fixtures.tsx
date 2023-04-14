import {buildRepositoryLocation, buildRepository} from '../../graphql/types';

export const mockRepository = {
  repository: buildRepository({
    id: '343870956dd1f7d356e4ea564a099f360cf330b4',
    name: 'toys_repository',
    pipelines: [],
    schedules: [],
    sensors: [],
    partitionSets: [],
    assetGroups: [],
    location: buildRepositoryLocation({
      id: 'dagster_test.toys.repo',
      name: 'dagster_test.toys.repo',
    }),
    displayMetadata: [],
  }),
  repositoryLocation: buildRepositoryLocation({
    id: 'dagster_test.toys.repo',
    isReloadSupported: true,
    serverId: 'bfac18f3-5dba-464b-a563-3b89b775dd2f',
    name: 'dagster_test.toys.repo',
    repositories: [],
  }),
};
