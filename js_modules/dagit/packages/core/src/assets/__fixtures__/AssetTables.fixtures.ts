import {MockedResponse} from '@apollo/client/testing';

import {MockStaleReasonData} from '../../asset-graph/__fixtures__/AssetNode.fixtures';
import {AssetGraphLiveQuery} from '../../asset-graph/types/useLiveDataForAssetKeys.types';
import {ASSETS_GRAPH_LIVE_QUERY} from '../../asset-graph/useLiveDataForAssetKeys';
import {
  StaleStatus,
  RunStatus,
  buildAssetNode,
  buildRepositoryLocation,
  buildRepository,
  buildAssetKey,
  buildPartitionDefinition,
} from '../../graphql/types';
import {SINGLE_NON_SDA_ASSET_QUERY} from '../../workspace/VirtualizedAssetRow';
import {SingleNonSdaAssetQuery} from '../../workspace/types/VirtualizedAssetRow.types';
import {ASSET_CATALOG_GROUP_TABLE_QUERY, ASSET_CATALOG_TABLE_QUERY} from '../AssetsCatalogTable';
import {
  AssetCatalogGroupTableQuery,
  AssetCatalogTableQuery,
} from '../types/AssetsCatalogTable.types';

export const AssetCatalogGroupTableMock: MockedResponse<AssetCatalogGroupTableQuery> = {
  request: {
    query: ASSET_CATALOG_GROUP_TABLE_QUERY,
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [],
    },
  },
};

export const SingleAssetQueryTrafficDashboard: MockedResponse<SingleNonSdaAssetQuery> = {
  request: {
    query: SINGLE_NON_SDA_ASSET_QUERY,
    variables: {input: {path: ['dashboards', 'traffic_dashboard']}},
  },
  result: {
    data: {
      __typename: 'Query',
      assetOrError: {
        id: '["dashboards", "traffic_dashboard"]',
        assetMaterializations: [
          {
            timestamp: '1674603883946',
            runId: 'db44ed48-0dca-4942-803b-5edc439c73eb',
            __typename: 'MaterializationEvent',
          },
        ],
        __typename: 'Asset',
      },
    },
  },
};

const repository = buildRepository({
  id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
  name: 'repo',
  location: buildRepositoryLocation({
    id: 'test.py',
    name: 'test.py',
    __typename: 'RepositoryLocation',
  }),
  __typename: 'Repository',
});

export const SingleAssetQueryMaterializedWithLatestRun: MockedResponse<AssetGraphLiveQuery> = {
  request: {
    query: ASSETS_GRAPH_LIVE_QUERY,
    variables: {assetKeys: [{path: ['good_asset']}]},
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [
        {
          id: 'test.py.repo.["good_asset"]',
          opNames: ['good_asset'],
          repository,
          partitionStats: null,
          assetKey: {
            path: ['good_asset'],
            __typename: 'AssetKey',
          },
          assetMaterializations: [
            {
              timestamp: '1674603883946',
              runId: 'db44ed48-0dca-4942-803b-5edc439c73eb',
              __typename: 'MaterializationEvent',
            },
          ],

          freshnessInfo: null,
          assetObservations: [
            {
              timestamp: '1674764717707',
              runId: 'ae107ad2-8827-44fb-bc62-a4cdacb78438',
              __typename: 'ObservationEvent',
            },
          ],
          staleStatus: StaleStatus.FRESH,
          staleCauses: [],
          __typename: 'AssetNode',
        },
      ],
      assetsLatestInfo: [
        {
          assetKey: {
            path: ['good_asset'],
            __typename: 'AssetKey',
          },
          unstartedRunIds: [],
          inProgressRunIds: [],
          latestRun: {
            id: 'db44ed48-0dca-4942-803b-5edc439c73eb',
            status: RunStatus.SUCCESS,
            endTime: 1674603891.34749,
            __typename: 'Run',
          },
          __typename: 'AssetLatestInfo',
        },
      ],
    },
  },
};

export const SingleAssetQueryMaterializedStaleAndLate: MockedResponse<AssetGraphLiveQuery> = {
  request: {
    query: ASSETS_GRAPH_LIVE_QUERY,
    variables: {assetKeys: [{path: ['late_asset']}]},
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [
        {
          id: 'test.py.repo.["late_asset"]',
          opNames: ['late_asset'],
          repository,
          partitionStats: null,
          assetKey: {
            path: ['late_asset'],
            __typename: 'AssetKey',
          },
          assetMaterializations: [
            {
              timestamp: '1674603891025',
              runId: 'db44ed48-0dca-4942-803b-5edc439c73eb',
              __typename: 'MaterializationEvent',
            },
          ],
          freshnessInfo: {
            currentMinutesLate: 21657.2618512,
            __typename: 'AssetFreshnessInfo',
          },
          assetObservations: [],
          staleStatus: StaleStatus.STALE,
          staleCauses: [MockStaleReasonData],
          __typename: 'AssetNode',
        },
      ],
      assetsLatestInfo: [
        {
          assetKey: {
            path: ['late_asset'],
            __typename: 'AssetKey',
          },
          unstartedRunIds: [],
          inProgressRunIds: [],
          latestRun: {
            id: 'db44ed48-0dca-4942-803b-5edc439c73eb',
            status: RunStatus.SUCCESS,
            endTime: 1674603891.34749,
            __typename: 'Run',
          },
          __typename: 'AssetLatestInfo',
        },
      ],
    },
  },
};

export const SingleAssetQueryLastRunFailed: MockedResponse<AssetGraphLiveQuery> = {
  request: {
    query: ASSETS_GRAPH_LIVE_QUERY,
    variables: {assetKeys: [{path: ['run_failing_asset']}]},
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [
        {
          id: 'test.py.repo.["run_failing_asset"]',
          opNames: ['run_failing_asset'],
          repository,
          partitionStats: {
            __typename: 'PartitionStats',
            numMaterialized: 8,
            numMaterializing: 0,
            numPartitions: 11,
            numFailed: 0,
          },
          assetKey: {
            path: ['run_failing_asset'],
            __typename: 'AssetKey',
          },
          assetMaterializations: [
            {
              timestamp: '1666373060112',
              runId: 'e23b2cd2-7a4e-43d2-bdc6-892125375e8f',
              __typename: 'MaterializationEvent',
            },
          ],

          freshnessInfo: null,
          assetObservations: [],
          staleStatus: StaleStatus.MISSING,
          staleCauses: [],
          __typename: 'AssetNode',
        },
      ],
      assetsLatestInfo: [
        {
          assetKey: {
            path: ['run_failing_asset'],
            __typename: 'AssetKey',
          },
          unstartedRunIds: [],
          inProgressRunIds: [],
          latestRun: {
            id: '4678865f-6191-4a35-bb47-2122d57ec9a6',
            status: RunStatus.FAILURE,
            endTime: 1669067250.48091,
            __typename: 'Run',
          },
          __typename: 'AssetLatestInfo',
        },
      ],
    },
  },
};

export const AssetCatalogTableMockAssets: Extract<
  AssetCatalogTableQuery['assetsOrError'],
  {__typename: 'AssetConnection'}
>['nodes'] = [
  {
    id: '["dashboards", "cost_dashboard"]',
    __typename: 'Asset',
    key: buildAssetKey({path: ['dashboards', 'cost_dashboard']}),
    definition: null,
  },
  {
    id: '["dashboards", "traffic_dashboard"]',
    __typename: 'Asset',
    key: buildAssetKey({path: ['dashboards', 'traffic_dashboard']}),
    definition: null,
  },
  {
    id: 'test.py.repo.["good_asset"]',
    __typename: 'Asset',
    key: buildAssetKey({path: ['good_asset']}),
    definition: buildAssetNode({
      id: 'test.py.repo.["good_asset"]',
      groupName: 'GROUP2',
      partitionDefinition: null,
      hasMaterializePermission: true,
      computeKind: 'snowflake',
      description:
        'This is a super long description that could involve some level of SQL and is just generally very long',
      repository,
    }),
  },
  {
    id: 'test.py.repo.["late_asset"]',
    __typename: 'Asset',
    key: buildAssetKey({path: ['late_asset']}),
    definition: buildAssetNode({
      id: 'test.py.repo.["late_asset"]',
      groupName: 'GROUP2',
      partitionDefinition: null,
      freshnessPolicy: {
        maximumLagMinutes: 2,
        cronSchedule: null,
        cronScheduleTimezone: null,
        __typename: 'FreshnessPolicy',
      },
      hasMaterializePermission: true,
      computeKind: null,
      description: null,
      repository,
    }),
  },
  {
    id: 'test.py.repo.["run_failing_asset"]',
    __typename: 'Asset',
    key: buildAssetKey({path: ['run_failing_asset']}),
    definition: buildAssetNode({
      id: 'test.py.repo.["run_failing_asset"]',
      groupName: 'GROUP4',
      partitionDefinition: buildPartitionDefinition({
        description:
          "Multi-partitioned, with dimensions: \nAstate: 'TN', 'VA', 'GA', 'KY', 'PA', 'NC', 'SC', 'FL', 'OH', 'IL', 'WV' \nDate: Daily, starting 2021-05-05 UTC.",
      }),
      description: 'This is a description!',
      hasMaterializePermission: true,
      computeKind: 'sql',
      repository,
    }),
  },
  {
    id: 'test.py.repo.["asset_with_a_very_long_key_that_will_require_truncation"]',
    __typename: 'Asset',
    key: buildAssetKey({path: ['asset_with_a_very_long_key_that_will_require_truncation']}),
    definition: buildAssetNode({
      id: 'test.py.repo.["asset_with_a_very_long_key_that_will_require_truncation"]',
      groupName: 'GROUP4',
      partitionDefinition: null,
      description: 'This one should be in a loading state to demo that view',
      hasMaterializePermission: true,
      computeKind: 'ipynb',
      repository,
    }),
  },
];

export const AssetCatalogTableMock: MockedResponse<AssetCatalogTableQuery> = {
  request: {
    query: ASSET_CATALOG_TABLE_QUERY,
  },
  result: {
    data: {
      __typename: 'Query',
      assetsOrError: {
        __typename: 'AssetConnection',
        nodes: AssetCatalogTableMockAssets,
      },
    },
  },
};
