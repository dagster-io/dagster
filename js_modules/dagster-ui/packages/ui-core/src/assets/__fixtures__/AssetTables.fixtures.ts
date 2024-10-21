import {ASSETS_GRAPH_LIVE_QUERY} from '../../asset-data/AssetBaseDataProvider';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
} from '../../asset-data/types/AssetBaseDataProvider.types';
import {MockStaleReasonData} from '../../asset-graph/__fixtures__/AssetNode.fixtures';
import {
  Asset,
  RunStatus,
  StaleStatus,
  buildAsset,
  buildAssetChecks,
  buildAssetConnection,
  buildAssetFreshnessInfo,
  buildAssetKey,
  buildAssetLatestInfo,
  buildAssetNode,
  buildFreshnessPolicy,
  buildMaterializationEvent,
  buildObservationEvent,
  buildPartitionDefinition,
  buildPartitionStats,
  buildRepository,
  buildRepositoryLocation,
  buildRun,
} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {SINGLE_NON_SDA_ASSET_QUERY} from '../../workspace/VirtualizedAssetRow';
import {
  SingleNonSdaAssetQuery,
  SingleNonSdaAssetQueryVariables,
} from '../../workspace/types/VirtualizedAssetRow.types';
import {ASSET_CATALOG_GROUP_TABLE_QUERY, ASSET_CATALOG_TABLE_QUERY} from '../AssetsCatalogTable';
import {
  AssetCatalogGroupTableQuery,
  AssetCatalogGroupTableQueryVariables,
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables,
} from '../types/AssetsCatalogTable.types';

export const AssetCatalogGroupTableMock = buildQueryMock<
  AssetCatalogGroupTableQuery,
  AssetCatalogGroupTableQueryVariables
>({
  query: ASSET_CATALOG_GROUP_TABLE_QUERY,
  data: {
    assetNodes: [],
  },
});

export const SingleAssetQueryTrafficDashboard = buildQueryMock<
  SingleNonSdaAssetQuery,
  SingleNonSdaAssetQueryVariables
>({
  query: SINGLE_NON_SDA_ASSET_QUERY,
  variables: {input: {path: ['dashboards', 'traffic_dashboard']}},
  data: {
    assetOrError: buildAsset({
      id: '["dashboards", "traffic_dashboard"]',
      assetMaterializations: [
        buildMaterializationEvent({
          timestamp: '1674603883946',
          runId: 'db44ed48-0dca-4942-803b-5edc439c73eb',
        }),
      ],
    }),
  },
});

const repository = buildRepository({
  id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
  name: 'repo',
  location: buildRepositoryLocation({
    id: 'test.py',
    name: 'test.py',
  }),
});

export const SingleAssetQueryMaterializedWithLatestRun = buildQueryMock<
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables
>({
  query: ASSETS_GRAPH_LIVE_QUERY,
  variables: {assetKeys: [{path: ['good_asset']}]},
  data: {
    assetNodes: [
      buildAssetNode({
        id: 'test.py.repo.["good_asset"]',
        opNames: ['good_asset'],
        repository,
        partitionStats: null,
        assetKey: buildAssetKey({
          path: ['good_asset'],
        }),
        assetMaterializations: [
          buildMaterializationEvent({
            timestamp: '1674603883946',
            runId: 'db44ed48-0dca-4942-803b-5edc439c73eb',
          }),
        ],
        assetChecksOrError: buildAssetChecks(),
        freshnessInfo: null,
        assetObservations: [
          buildObservationEvent({
            timestamp: '1674764717707',
            runId: 'ae107ad2-8827-44fb-bc62-a4cdacb78438',
          }),
        ],
        staleStatus: StaleStatus.FRESH,
        staleCauses: [],
      }),
    ],
    assetsLatestInfo: [
      buildAssetLatestInfo({
        id: 'test.py.repo.["good_asset"]',
        assetKey: buildAssetKey({
          path: ['good_asset'],
        }),
        unstartedRunIds: [],
        inProgressRunIds: [],
        latestRun: buildRun({
          id: 'db44ed48-0dca-4942-803b-5edc439c73eb',
          status: RunStatus.SUCCESS,
          endTime: 1674603891.34749,
        }),
      }),
    ],
  },
});

export const SingleAssetQueryMaterializedStaleAndLate = buildQueryMock<
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables
>({
  query: ASSETS_GRAPH_LIVE_QUERY,
  variables: {assetKeys: [{path: ['late_asset']}]},
  data: {
    assetNodes: [
      buildAssetNode({
        id: 'test.py.repo.["late_asset"]',
        opNames: ['late_asset'],
        repository,
        partitionStats: null,
        assetKey: {
          path: ['late_asset'],
          __typename: 'AssetKey',
        },
        assetChecksOrError: buildAssetChecks(),
        assetMaterializations: [
          buildMaterializationEvent({
            timestamp: '1674603891025',
            runId: 'db44ed48-0dca-4942-803b-5edc439c73eb',
          }),
        ],
        freshnessInfo: buildAssetFreshnessInfo({
          currentMinutesLate: 21657.2618512,
        }),
        assetObservations: [],
        staleStatus: StaleStatus.STALE,
        staleCauses: [MockStaleReasonData],
      }),
    ],
    assetsLatestInfo: [
      buildAssetLatestInfo({
        id: 'test.py.repo.["late_asset"]',
        assetKey: buildAssetKey({
          path: ['late_asset'],
        }),
        unstartedRunIds: [],
        inProgressRunIds: [],
        latestRun: buildRun({
          id: 'db44ed48-0dca-4942-803b-5edc439c73eb',
          status: RunStatus.SUCCESS,
          endTime: 1674603891.34749,
        }),
      }),
    ],
  },
});

export const SingleAssetQueryLastRunFailed = buildQueryMock<
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables
>({
  query: ASSETS_GRAPH_LIVE_QUERY,
  variables: {assetKeys: [{path: ['run_failing_asset']}]},
  data: {
    assetNodes: [
      buildAssetNode({
        id: 'test.py.repo.["run_failing_asset"]',
        opNames: ['run_failing_asset'],
        repository,
        partitionStats: buildPartitionStats({
          numMaterialized: 8,
          numMaterializing: 0,
          numPartitions: 11,
          numFailed: 0,
        }),
        assetKey: buildAssetKey({
          path: ['run_failing_asset'],
        }),
        assetChecksOrError: buildAssetChecks(),
        assetMaterializations: [
          buildMaterializationEvent({
            timestamp: '1666373060112',
            runId: 'e23b2cd2-7a4e-43d2-bdc6-892125375e8f',
          }),
        ],

        freshnessInfo: null,
        assetObservations: [],
        staleStatus: StaleStatus.MISSING,
        staleCauses: [],
      }),
    ],
    assetsLatestInfo: [
      buildAssetLatestInfo({
        id: 'test.py.repo.["run_failing_asset"]',
        assetKey: buildAssetKey({
          path: ['run_failing_asset'],
        }),
        unstartedRunIds: [],
        inProgressRunIds: [],
        latestRun: buildRun({
          id: '4678865f-6191-4a35-bb47-2122d57ec9a6',
          status: RunStatus.FAILURE,
          endTime: 1669067250.48091,
        }),
      }),
    ],
  },
});

export const AssetCatalogTableMockAssets: Asset[] = [
  buildAsset({
    id: '["dashboards", "cost_dashboard"]',
    key: buildAssetKey({path: ['dashboards', 'cost_dashboard']}),
    definition: null,
  }),
  buildAsset({
    id: '["dashboards", "traffic_dashboard"]',
    key: buildAssetKey({path: ['dashboards', 'traffic_dashboard']}),
    definition: null,
  }),
  buildAsset({
    id: 'test.py.repo.["good_asset"]',
    key: buildAssetKey({path: ['good_asset']}),
    definition: buildAssetNode({
      id: 'test.py.repo.["good_asset"]',
      groupName: 'GROUP2',
      isExecutable: true,
      partitionDefinition: null,
      hasMaterializePermission: true,
      computeKind: 'snowflake',
      description:
        'This is a super long description that could involve some level of SQL and is just generally very long',
      repository,
    }),
  }),
  buildAsset({
    id: 'test.py.repo.["late_asset"]',
    key: buildAssetKey({path: ['late_asset']}),
    definition: buildAssetNode({
      id: 'test.py.repo.["late_asset"]',
      groupName: 'GROUP2',
      partitionDefinition: null,
      freshnessPolicy: buildFreshnessPolicy({
        maximumLagMinutes: 2,
        cronSchedule: null,
        cronScheduleTimezone: null,
      }),
      hasMaterializePermission: true,
      isExecutable: true,
      computeKind: null,
      description: null,
      repository,
    }),
  }),
  buildAsset({
    id: 'test.py.repo.["run_failing_asset"]',
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
  }),
  buildAsset({
    id: 'test.py.repo.["asset_with_a_very_long_key_that_will_require_truncation"]',
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
  }),
];

export const AssetCatalogTableMock = buildQueryMock<
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables
>({
  query: ASSET_CATALOG_TABLE_QUERY,
  variableMatcher: () => true,
  data: {
    assetsOrError: buildAssetConnection({
      nodes: AssetCatalogTableMockAssets,
    }),
  },
});
