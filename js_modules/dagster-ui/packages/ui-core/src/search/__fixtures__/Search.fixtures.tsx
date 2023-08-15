import {MockedResponse} from '@apollo/client/testing';
import faker from 'faker';

import {
  buildAsset,
  buildAssetConnection,
  buildAssetGroup,
  buildAssetKey,
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildSchedule,
  buildSensor,
  buildWorkspace,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {SearchPrimaryQuery, SearchSecondaryQuery} from '../types/useGlobalSearch.types';
import {SEARCH_PRIMARY_QUERY, SEARCH_SECONDARY_QUERY} from '../useGlobalSearch';

export const buildPrimarySearch = (delay = 0): MockedResponse<SearchPrimaryQuery> => {
  return {
    delay,
    request: {
      query: SEARCH_PRIMARY_QUERY,
      variables: {},
    },
    result: {
      data: {
        __typename: 'Query',
        workspaceOrError: buildWorkspace({
          locationEntries: [
            buildWorkspaceLocationEntry({
              locationOrLoadError: buildRepositoryLocation({
                id: 'my-location',
                name: 'my-location',
                repositories: [
                  buildRepository({
                    id: 'foo',
                    name: 'foo',
                    assetGroups: new Array(10).fill(null).map((_) =>
                      buildAssetGroup({
                        groupName: faker.random.word(),
                      }),
                    ),
                    pipelines: new Array(10).fill(null).map((_) => {
                      const id = faker.company.catchPhrase().toLowerCase();
                      return buildPipeline({
                        id,
                        name: id,
                        isJob: true,
                      });
                    }),
                    schedules: new Array(10).fill(null).map((_) => {
                      const id = faker.company.catchPhrase().toLowerCase();
                      return buildSchedule({
                        id,
                        name: id,
                      });
                    }),
                    sensors: new Array(10).fill(null).map((_) => {
                      const id = faker.company.catchPhrase().toLowerCase();
                      return buildSensor({
                        id,
                        name: id,
                      });
                    }),
                  }),
                ],
              }),
            }),
          ],
        }),
      },
    },
  };
};

export const buildPrimarySearchStatic = (delay = 0): MockedResponse<SearchPrimaryQuery> => {
  return {
    delay,
    request: {
      query: SEARCH_PRIMARY_QUERY,
      variables: {},
    },
    result: {
      data: {
        __typename: 'Query',
        workspaceOrError: buildWorkspace({
          locationEntries: [
            buildWorkspaceLocationEntry({
              locationOrLoadError: buildRepositoryLocation({
                id: 'my-location',
                name: 'my-location',
                repositories: [
                  buildRepository({
                    id: 'foo',
                    name: 'foo',
                    assetGroups: [
                      buildAssetGroup({
                        groupName: 'asset-group-one',
                      }),
                      buildAssetGroup({
                        groupName: 'asset-group-two',
                      }),
                    ],
                    pipelines: [
                      buildPipeline({
                        id: 'job-one',
                        name: 'job-one',
                        isJob: true,
                      }),
                      buildPipeline({
                        id: 'job-two',
                        name: 'job-two',
                        isJob: true,
                      }),
                    ],
                    schedules: [
                      buildSchedule({
                        id: 'schedule-one',
                        name: 'schedule-one',
                      }),
                      buildSchedule({
                        id: 'schedule-two',
                        name: 'schedule-two',
                      }),
                    ],
                    sensors: [
                      buildSensor({
                        id: 'sensor-one',
                        name: 'sensor-one',
                      }),
                      buildSensor({
                        id: 'sensor-two',
                        name: 'sensor-two',
                      }),
                    ],
                  }),
                ],
              }),
            }),
          ],
        }),
      },
    },
  };
};

export const buildSecondarySearch = (
  size = 100,
  delay = 0,
): MockedResponse<SearchSecondaryQuery> => {
  return {
    delay,
    request: {
      query: SEARCH_SECONDARY_QUERY,
      variables: {},
    },
    result: {
      data: {
        __typename: 'Query',
        assetsOrError: buildAssetConnection({
          // This array manually builds up `Asset` objects because it is too expensive
          // to run the builders for many thousands of objects.
          nodes: new Array(size).fill(null).map((_) => {
            const path = faker.random.words(3);
            const id = path.replace(' ', '-');
            return {
              __typename: 'Asset',
              id,
              definition: null,
              assetMaterializations: [],
              assetObservations: [],
              key: {
                __typename: 'AssetKey',
                path: path.split(' '),
              },
            };
          }),
        }),
      },
    },
  };
};

export const buildSecondarySearchStatic = (delay = 0): MockedResponse<SearchSecondaryQuery> => {
  return {
    delay,
    request: {
      query: SEARCH_SECONDARY_QUERY,
      variables: {},
    },
    result: {
      data: {
        __typename: 'Query',
        assetsOrError: buildAssetConnection({
          nodes: [
            buildAsset({
              id: 'asset-one',
              key: buildAssetKey({
                path: ['asset-one'],
              }),
            }),
            buildAsset({
              id: 'asset-two',
              key: buildAssetKey({
                path: ['asset-two'],
              }),
            }),
            buildAsset({
              id: 'asset-three',
              key: buildAssetKey({
                path: ['asset-three'],
              }),
            }),
            buildAsset({
              id: 'asset-four',
              key: buildAssetKey({
                path: ['asset-four'],
              }),
            }),
          ],
        }),
      },
    },
  };
};
