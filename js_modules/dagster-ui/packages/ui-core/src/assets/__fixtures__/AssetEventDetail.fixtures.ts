import {MockedResponse} from '@apollo/client/testing';

import {
  buildAsset,
  buildAssetNode,
  buildAssetResultEventHistoryConnection,
  buildEventTag,
  buildIntMetadataEntry,
  buildMaterializationEvent,
  buildObservationEvent,
  buildPathMetadataEntry,
  buildQuery,
  buildRepositoryOrigin,
  buildRun,
  RunStatus,
  StaleStatus,
} from '../../graphql/types';
import {ASSET_MATERIALIZATION_UPSTREAM_QUERY} from '../AssetMaterializationUpstreamData';
import {ASSET_PARTITION_DETAIL_QUERY, ASSET_PARTITION_STALE_QUERY} from '../AssetPartitionDetail';
import {AssetMaterializationUpstreamQuery} from '../types/AssetMaterializationUpstreamData.types';
import {
  AssetPartitionDetailQuery,
  AssetPartitionStaleQuery,
} from '../types/AssetPartitionDetail.types';

export const Partition = '2022-02-02';
export const MaterializationTimestamp = 1673996425523;

const ONE_MIN = 60 * 1000;

export const MaterializationEventOlder = buildMaterializationEvent({
  partition: Partition,
  tags: [
    buildEventTag({
      key: 'dagster/code_version',
      value: '0b847814-4e03-82a6-cfab-d9431369974d',
    }),
    buildEventTag({
      key: 'dagster/logical_version',
      value: '5133d9b282809abd0d1ae6ab5c1b6175af7cc4d91d7543bfa7141aef71fba39e',
    }),
  ],
  runOrError: buildRun({
    id: '0b847814-4e03-82a6-cfab-d9431369974d',
    mode: 'default',
    repositoryOrigin: buildRepositoryOrigin({
      id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
      repositoryName: 'repo',
      repositoryLocationName: 'test.py',
    }),
    status: RunStatus.SUCCESS,
    pipelineName: 'yoyoyoyoyojob',
    pipelineSnapshotId: '33078455c88e4062615dabcbaf40773392470fc9',
  }),
  runId: '0b847814-4e03-82a6-cfab-d9431369974d',
  timestamp: `${MaterializationTimestamp - 60 * ONE_MIN}`,
  stepKey: 'asset_1',
  label: 'asset_1',
  description: null,
  metadataEntries: [
    buildPathMetadataEntry({
      label: 'path',
      description: null,
      path: '/dagster-home/storage/storage/asset_1_old_path_bad',
    }),
    buildPathMetadataEntry({
      label: 'deprecated_key',
      description: null,
      path: '/should/not/appear/except/in/detailed/history',
    }),
    buildIntMetadataEntry({
      label: 'num_rows',
      description: null,
      intValue: 20,
      intRepr: '20',
    }),
  ],
  assetLineage: [],
});

export const MaterializationEventMinimal = buildMaterializationEvent({
  partition: null,
  tags: [],
  runOrError: buildRun({
    id: '1369974d-cfab-4e03-82a6-d9430b847814',
    mode: 'default',
    repositoryOrigin: buildRepositoryOrigin({
      id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
      repositoryName: 'repo',
      repositoryLocationName: 'test.py',
    }),
    status: RunStatus.FAILURE,
    pipelineName: '__ASSET_JOB_0',
    pipelineSnapshotId: '6e17dbde04cd1c5e3cec66a7d4d8a3e244bf27a6',
  }),
  runId: '1369974d-cfab-4e03-82a6-d9430b847814',
  timestamp: `${MaterializationTimestamp}`,
  stepKey: 'asset_1',
  label: 'asset_1',
  description: null,
  metadataEntries: [],
  assetLineage: [],
});

export const MaterializationEventFull = buildMaterializationEvent({
  partition: Partition,
  tags: [
    buildEventTag({
      key: 'dagster/backfill',
      value: 'difhnmkt',
    }),
    buildEventTag({
      key: 'dagster/code_version',
      value: '1369974d-cfab-4e03-82a6-d9430b847814',
    }),
    buildEventTag({
      key: 'dagster/input_event_pointer/whatever4',
      value: '197333',
    }),
    buildEventTag({
      key: 'dagster/input_logical_version/whatever4',
      value: '8bf9bc307d655884c50036d758d74fdfa475f00a73df4ba95d9903a218cb827d',
    }),
    buildEventTag({
      key: 'dagster/logical_version',
      value: '5133d9b282809abd0d1ae6ab5c1b6175af7cc4d91d7543bfa7141aef71fba39e',
    }),
  ],
  runOrError: buildRun({
    id: '1369974d-cfab-4e03-82a6-d9430b847814',
    mode: 'default',
    repositoryOrigin: buildRepositoryOrigin({
      id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
      repositoryName: 'repo',
      repositoryLocationName: 'test.py',
    }),
    status: RunStatus.SUCCESS,
    pipelineName: 'yoyoyoyoyojob',
    pipelineSnapshotId: '33078455c88e4062615dabcbaf40773392470fc9',
  }),
  runId: '1369974d-cfab-4e03-82a6-d9430b847814',
  timestamp: `${MaterializationTimestamp}`,
  stepKey: 'asset_1',
  label: 'asset_1',
  description: null,
  metadataEntries: [
    buildPathMetadataEntry({
      label: 'path',
      description: null,
      path: '/dagster-home/storage/storage/asset_1',
    }),
    buildIntMetadataEntry({
      label: 'num_rows',
      description: null,
      intValue: 50,
      intRepr: '50',
    }),
  ],
  assetLineage: [],
});

export const BasicObservationEvent = buildObservationEvent({
  partition: Partition,
  tags: [
    buildEventTag({
      key: 'dagster/code_version',
      value: '1369974d-cfab-4e03-82a6-d9430b847814',
    }),
    buildEventTag({
      key: 'dagster/logical_version',
      value: '5133d9b282809abd0d1ae6ab5c1b6175af7cc4d91d7543bfa7141aef71fba39e',
    }),
  ],
  runOrError: buildRun({
    id: '01e455fc-9ea5-4d45-92d6-a997b9e4bf60',
    mode: 'default',
    repositoryOrigin: buildRepositoryOrigin({
      id: 'cc94e313d9025bbc796a3e7e46487eb305969b68',
      repositoryName: 'repo',
      repositoryLocationName: 'test.py',
    }),
    status: RunStatus.FAILURE,
    pipelineName: '__ASSET_JOB_0',
    pipelineSnapshotId: '6e17dbde04cd1c5e3cec66a7d4d8a3e244bf27a6',
  }),
  runId: '01e455fc-9ea5-4d45-92d6-a997b9e4bf60',
  timestamp: `${MaterializationTimestamp + 5 * ONE_MIN}`,
  stepKey: 'hobbyproject',
  label: 'raw_country_populations',
  description: null,
  metadataEntries: [
    buildIntMetadataEntry({
      label: 'correct_rows',
      description: null,
      intValue: 48,
      intRepr: '48',
    }),
  ],
});

export const MaterializationUpstreamDataFullMock: MockedResponse<AssetMaterializationUpstreamQuery> =
  {
    request: {
      operationName: 'AssetMaterializationUpstreamQuery',
      variables: {assetKey: {path: ['asset_1']}, timestamp: '1673996425523'},
      query: ASSET_MATERIALIZATION_UPSTREAM_QUERY,
    },
    result: {
      data: {
        __typename: 'Query',
        assetNodeOrError: {
          __typename: 'AssetNode',
          id: 'test.py.repo.["asset_1"]',
          assetMaterializationUsedData: [
            {
              __typename: 'MaterializationUpstreamDataVersion',
              timestamp: `${MaterializationTimestamp - 2 * ONE_MIN}`,
              assetKey: {
                path: ['inp2'],
                __typename: 'AssetKey',
              },
              downstreamAssetKey: {
                path: ['asset_1'],
                __typename: 'AssetKey',
              },
            },
            {
              __typename: 'MaterializationUpstreamDataVersion',
              timestamp: `${MaterializationTimestamp - 4 * ONE_MIN}`,
              assetKey: {
                path: ['inp3'],
                __typename: 'AssetKey',
              },
              downstreamAssetKey: {
                path: ['asset_1'],
                __typename: 'AssetKey',
              },
            },
          ],
        },
      },
    },
  };

export const MaterializationUpstreamDataEmptyMock: MockedResponse<AssetMaterializationUpstreamQuery> =
  {
    request: {
      operationName: 'AssetMaterializationUpstreamQuery',
      variables: {assetKey: {path: ['asset_1']}, timestamp: '1673996425523'},
      query: ASSET_MATERIALIZATION_UPSTREAM_QUERY,
    },
    result: {
      data: {
        __typename: 'Query',
        assetNodeOrError: {
          __typename: 'AssetNode',
          id: 'test.py.repo.["asset_1"]',
          assetMaterializationUsedData: [],
        },
      },
    },
  };

export const buildAssetPartitionDetailMock = (
  currentRunStatus?: RunStatus,
): MockedResponse<AssetPartitionDetailQuery> => ({
  request: {
    operationName: 'AssetPartitionDetailQuery',
    variables: {assetKey: {path: ['asset_1']}, partitionKey: Partition},
    query: ASSET_PARTITION_DETAIL_QUERY,
  },
  result: {
    data: buildQuery({
      assetOrError: buildAsset({
        __typename: 'Asset',
        id: 'test.py.repo.["asset_1"]',
        assetEventHistory: buildAssetResultEventHistoryConnection({
          results: [
            BasicObservationEvent,
            MaterializationEventFull,
            MaterializationEventOlder,
            {
              ...BasicObservationEvent,
              stepKey: 'a_different_step',
              timestamp: `${Number(BasicObservationEvent.timestamp) + 2 * 60 * 1000}`,
            },
          ],
        }),
        definition: buildAssetNode({
          opNames: ['a_different_step'],
          latestRunForPartition: currentRunStatus
            ? buildRun({
                id: '123456',
                status: currentRunStatus,
                endTime: null,
              })
            : null,
        }),
      }),
    }),
  },
});

export const buildAssetPartitionStaleMock = (
  staleCauses: Extract<
    AssetPartitionStaleQuery['assetNodeOrError'],
    {__typename: 'AssetNode'}
  >['staleCauses'] = [],
): MockedResponse<AssetPartitionStaleQuery> => ({
  request: {
    operationName: 'AssetPartitionStaleQuery',
    variables: {assetKey: {path: ['asset_1']}, partitionKey: Partition},
    query: ASSET_PARTITION_STALE_QUERY,
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodeOrError: {
        __typename: 'AssetNode',
        id: 'test.py.repo.["asset_1"]',
        staleCauses,
        staleStatus: staleCauses.length ? StaleStatus.STALE : StaleStatus.FRESH,
      },
    },
  },
});
