import {MockedResponse} from '@apollo/client/testing';

import {BulkActionStatus, RunStatus} from '../graphql/types';

import {
  SINGLE_BACKFILL_STATUS_COUNTS_QUERY,
  SINGLE_BACKFILL_STATUS_DETAILS_QUERY,
} from './BackfillRow';
import {SingleBackfillCountsQuery, SingleBackfillQuery} from './types/BackfillRow.types';
import {BackfillTableFragment} from './types/BackfillTable.types';

function buildTimePartitionNames(start: Date, count: number) {
  const results: string[] = [];
  for (let ii = 0; ii < count; ii++) {
    start.setMinutes(start.getMinutes() + 15);
    results.push(start.toISOString());
  }
  return results;
}

export const BackfillTableFragmentRequested2000AssetsPure: BackfillTableFragment = {
  backfillId: 'qtpussca',
  status: BulkActionStatus.REQUESTED,
  numPartitions: 2000,
  isValidSerialization: true,
  timestamp: 1675196684.587724,
  partitionSetName: null,
  partitionSet: null,
  error: null,
  numCancelable: 0,
  partitionNames: buildTimePartitionNames(new Date('2020-01-01'), 2000),
  assetSelection: [
    {
      path: ['global_graph_asset'],
      __typename: 'AssetKey',
    },
  ],
  __typename: 'PartitionBackfill',
};

export const BackfillTableFragmentRequested2000AssetsPureStatus: MockedResponse<SingleBackfillCountsQuery> = {
  request: {
    query: SINGLE_BACKFILL_STATUS_COUNTS_QUERY,
    variables: {
      backfillId: 'qtpussca',
    },
  },
  result: {
    data: {
      __typename: 'DagitQuery',
      partitionBackfillOrError: {
        backfillId: 'qtpussca',
        partitionStatusCounts: [
          {
            runStatus: RunStatus.NOT_STARTED,
            count: 108088,
            __typename: 'PartitionStatusCounts',
          },
          {
            runStatus: RunStatus.SUCCESS,
            count: 71,
            __typename: 'PartitionStatusCounts',
          },
          {
            runStatus: RunStatus.FAILURE,
            count: 10,
            __typename: 'PartitionStatusCounts',
          },
        ],
        __typename: 'PartitionBackfill',
      },
    },
  },
};

export const BackfillTableFragmentCancelledAssetsPartitionSet: BackfillTableFragment = {
  backfillId: 'tclwoggv',
  status: BulkActionStatus.CANCELED,
  isValidSerialization: true,
  numPartitions: 5000,
  timestamp: 1675106258.398993,
  partitionSetName: 'asset_job_partition_set',
  partitionSet: {
    id: '74c11a15d5d213176c83a7a71b50be0318103d8b',
    name: 'asset_job_partition_set',
    mode: 'default',
    pipelineName: 'asset_job',
    repositoryOrigin: {
      id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
      repositoryName: 'repo',
      repositoryLocationName: 'test.py',
      __typename: 'RepositoryOrigin',
    },
    __typename: 'PartitionSet',
  },
  error: null,
  numCancelable: 0,
  partitionNames: buildTimePartitionNames(new Date('2020-01-01'), 5000),
  assetSelection: [
    {
      path: ['whatever5'],
      __typename: 'AssetKey',
    },
    {
      path: ['multipartitioned_asset'],
      __typename: 'AssetKey',
    },
  ],
  __typename: 'PartitionBackfill',
};

export const BackfillTableFragmentCancelledAssetsPartitionSetStatus: MockedResponse<SingleBackfillCountsQuery> = {
  request: {
    query: SINGLE_BACKFILL_STATUS_COUNTS_QUERY,
    variables: {
      backfillId: 'tclwoggv',
    },
  },
  result: {
    data: {
      __typename: 'DagitQuery',
      partitionBackfillOrError: {
        backfillId: 'tclwoggv',
        partitionStatusCounts: [
          {runStatus: RunStatus.NOT_STARTED, count: 6524, __typename: 'PartitionStatusCounts'},
        ],
        __typename: 'PartitionBackfill',
      },
    },
  },
};

export const BackfillTableFragmentFailedError: BackfillTableFragment = {
  backfillId: 'sjqzcfhe',
  status: BulkActionStatus.FAILED,
  isValidSerialization: true,
  numPartitions: 100,
  timestamp: 1674774274.343382,
  partitionSetName: null,
  partitionSet: null,
  error: {
    __typename: 'PythonError',
    message:
      'dagster._core.errors.DagsterLaunchFailedError: Tried to start a run on a server after telling it to shut down\n',
    stack: ['OMITTED FROM MOCKS'],
    errorChain: [],
  },
  numCancelable: 0,
  partitionNames: buildTimePartitionNames(new Date('2020-01-01'), 100),
  assetSelection: [
    {
      path: ['multipartitioned_asset'],
      __typename: 'AssetKey',
    },
  ],
  __typename: 'PartitionBackfill',
};

export const BackfillTableFragmentFailedErrorStatus: MockedResponse<SingleBackfillQuery> = {
  request: {
    query: SINGLE_BACKFILL_STATUS_DETAILS_QUERY,
    variables: {
      backfillId: 'sjqzcfhe',
    },
  },
  result: {
    data: {
      __typename: 'DagitQuery',
      partitionBackfillOrError: {
        backfillId: 'sjqzcfhe',
        partitionStatuses: {
          results: BackfillTableFragmentFailedError.partitionNames!.map((n) => ({
            id: `__NO_PARTITION_SET__:${n}:ccpbwdbq`,
            partitionName: n,
            runId: null,
            runStatus: null,
            __typename: 'PartitionStatus',
          })),
          __typename: 'PartitionStatuses',
        },
        __typename: 'PartitionBackfill',
      },
    },
  },
};

export const BackfillTableFragmentCompletedAssetJob: BackfillTableFragment = {
  backfillId: 'pwgcpiwc',
  status: BulkActionStatus.COMPLETED,
  isValidSerialization: true,
  numPartitions: 11,
  timestamp: 1674660450.942305,
  partitionSetName: 'asset_job_partition_set',
  partitionSet: {
    id: '74c11a15d5d213176c83a7a71b50be0318103d8b',
    name: 'asset_job_partition_set',
    mode: 'default',
    pipelineName: 'asset_job',
    repositoryOrigin: {
      id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
      repositoryName: 'repo',
      repositoryLocationName: 'test.py',
      __typename: 'RepositoryOrigin',
    },
    __typename: 'PartitionSet',
  },
  error: null,
  numCancelable: 0,
  partitionNames: [
    'TN|2023-01-24',
    'VA|2023-01-24',
    'GA|2023-01-24',
    'KY|2023-01-24',
    'PA|2023-01-24',
    'NC|2023-01-24',
    'SC|2023-01-24',
    'FL|2023-01-24',
    'OH|2023-01-24',
    'IL|2023-01-24',
    'WV|2023-01-24',
  ],
  assetSelection: [
    {
      path: ['multipartitioned_asset'],
      __typename: 'AssetKey',
    },
  ],
  __typename: 'PartitionBackfill',
};

export const BackfillTableFragmentCompletedAssetJobStatus: MockedResponse<SingleBackfillQuery> = {
  request: {
    query: SINGLE_BACKFILL_STATUS_DETAILS_QUERY,
    variables: {
      backfillId: 'pwgcpiwc',
    },
  },
  result: {
    data: {
      __typename: 'DagitQuery',
      partitionBackfillOrError: {
        backfillId: 'pwgcpiwc',
        partitionStatuses: {
          results: [
            {
              id: 'asset_job_partition_set:TN|2023-01-24:pwgcpiwc',
              partitionName: 'TN|2023-01-24',
              runId: 'f9060b59-44aa-4cc1-aac2-f1365ed3c4da',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
            {
              id: 'asset_job_partition_set:VA|2023-01-24:pwgcpiwc',
              partitionName: 'VA|2023-01-24',
              runId: '719b32bc-d345-40f2-acf1-99d99bbd8b7f',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
            {
              id: 'asset_job_partition_set:GA|2023-01-24:pwgcpiwc',
              partitionName: 'GA|2023-01-24',
              runId: 'c85345e4-ad71-47b7-9add-f73b02f57c65',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
            {
              id: 'asset_job_partition_set:KY|2023-01-24:pwgcpiwc',
              partitionName: 'KY|2023-01-24',
              runId: 'f0b90d88-5b33-4287-92af-8b6b9e934ff4',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
            {
              id: 'asset_job_partition_set:PA|2023-01-24:pwgcpiwc',
              partitionName: 'PA|2023-01-24',
              runId: 'cfa8f88a-5b65-486b-ab2c-841dd8c711fa',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
            {
              id: 'asset_job_partition_set:NC|2023-01-24:pwgcpiwc',
              partitionName: 'NC|2023-01-24',
              runId: '1b59a3a2-98c7-495c-8758-6c689ac14f05',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
            {
              id: 'asset_job_partition_set:SC|2023-01-24:pwgcpiwc',
              partitionName: 'SC|2023-01-24',
              runId: '0ac8630e-5467-48db-8fd1-c9d45bad382d',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
            {
              id: 'asset_job_partition_set:FL|2023-01-24:pwgcpiwc',
              partitionName: 'FL|2023-01-24',
              runId: 'efb4a01d-4187-40b8-b9be-8b683173698e',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
            {
              id: 'asset_job_partition_set:OH|2023-01-24:pwgcpiwc',
              partitionName: 'OH|2023-01-24',
              runId: '98778750-c49a-4896-9d39-6b36554f41ab',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
            {
              id: 'asset_job_partition_set:IL|2023-01-24:pwgcpiwc',
              partitionName: 'IL|2023-01-24',
              runId: '8bab80df-571a-4dbc-9a08-9c3c33c962a6',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
            {
              id: 'asset_job_partition_set:WV|2023-01-24:pwgcpiwc',
              partitionName: 'WV|2023-01-24',
              runId: 'fc54444c-4c28-485b-b581-53ea5ce287f2',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
          ],
          __typename: 'PartitionStatuses',
        },
        __typename: 'PartitionBackfill',
      },
    },
  },
};

export const BackfillTableFragmentCompletedOpJob: BackfillTableFragment = {
  backfillId: 'pqdiepuf',
  status: BulkActionStatus.COMPLETED,
  isValidSerialization: true,
  numPartitions: 4,
  timestamp: 1674660356.340658,
  partitionSetName: 'op_job_partition_set',
  partitionSet: {
    id: 'a41b026cedcc5f871b4bf10db6e56ec1c63b8df0',
    name: 'op_job_partition_set',
    mode: 'default',
    pipelineName: 'op_job',
    repositoryOrigin: {
      id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
      repositoryName: 'repo',
      repositoryLocationName: 'test.py',
      __typename: 'RepositoryOrigin',
    },
    __typename: 'PartitionSet',
  },
  error: null,
  numCancelable: 0,
  partitionNames: ['2022-07-01', '2022-08-01', '2022-09-01', '2022-10-01'],
  assetSelection: null,
  __typename: 'PartitionBackfill',
};

export const BackfillTableFragmentCompletedOpJobStatus: MockedResponse<SingleBackfillQuery> = {
  request: {
    query: SINGLE_BACKFILL_STATUS_DETAILS_QUERY,
    variables: {
      backfillId: 'pqdiepuf',
    },
  },
  result: {
    data: {
      __typename: 'DagitQuery',
      partitionBackfillOrError: {
        backfillId: 'pqdiepuf',
        partitionStatuses: {
          results: [
            {
              id: 'op_job_partition_set:2022-07-01:pqdiepuf',
              partitionName: '2022-07-01',
              runId: '5cb9f428-1721-45d5-979e-64e0376aad1a',
              runStatus: RunStatus.FAILURE,
              __typename: 'PartitionStatus',
            },
            {
              id: 'op_job_partition_set:2022-08-01:pqdiepuf',
              partitionName: '2022-08-01',
              runId: '7d76bc38-db6c-4d77-b3c2-38b1a3b69ed9',
              runStatus: RunStatus.FAILURE,
              __typename: 'PartitionStatus',
            },
            {
              id: 'op_job_partition_set:2022-09-01:pqdiepuf',
              partitionName: '2022-09-01',
              runId: 'ca54267a-225c-491a-ad71-f6f3e0e868eb',
              runStatus: RunStatus.SUCCESS,
              __typename: 'PartitionStatus',
            },
            {
              id: 'op_job_partition_set:2022-10-01:pqdiepuf',
              partitionName: '2022-10-01',
              runId: '1baeadb4-7e7d-47e5-aeac-8a5f921cf27c',
              runStatus: RunStatus.QUEUED,
              __typename: 'PartitionStatus',
            },
          ],
          __typename: 'PartitionStatuses',
        },
        __typename: 'PartitionBackfill',
      },
    },
  },
};

export const BackfillTableFragmentInvalidPartitionSet: BackfillTableFragment = {
  backfillId: 'jzduiapb',
  status: BulkActionStatus.COMPLETED,
  isValidSerialization: false,
  numPartitions: 0,
  timestamp: 1676397948.698646,
  partitionSetName: null,
  partitionSet: null,
  error: null,
  numCancelable: 0,
  partitionNames: [],
  assetSelection: [
    {
      path: ['asset1'],
      __typename: 'AssetKey',
    },
    {
      path: ['asset2'],
      __typename: 'AssetKey',
    },
  ],
  __typename: 'PartitionBackfill',
};

export const BackfillTablePureAssetCountsOnly: BackfillTableFragment = {
  backfillId: 'likqkgna',
  status: BulkActionStatus.FAILED,
  isValidSerialization: true,
  numPartitions: 30,
  timestamp: 1677023094.435064,
  partitionSetName: null,
  partitionSet: null,
  error: {
    __typename: 'PythonError',
    message:
      'dagster._core.errors.DagsterUserCodeUnreachableError: Could not reach user code server. gRPC Error code: UNAVAILABLE\n',
    stack: ['OMITTED FROM MOCKS'],
    errorChain: [
      {
        isExplicitLink: true,
        error: {
          message:
            'grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:\n\tstatus = StatusCode.UNAVAILABLE\n\tdetails = "failed to connect to all addresses"\n\tdebug_error_string = "{"created":"@1677105084.883333000","description":"Failed to pick subchannel","file":"src/core/ext/filters/client_channel/client_channel.cc","file_line":3261,"referenced_errors":[{"created":"@1677105084.883332000","description":"failed to connect to all addresses","file":"src/core/lib/transport/error_utils.cc","file_line":167,"grpc_status":14}]}"\n>\n',
          stack: ['OMITTED FROM MOCKS'],
          __typename: 'PythonError',
        },
        __typename: 'ErrorChainLink',
      },
    ],
  },
  numCancelable: 0,
  partitionNames: null,
  assetSelection: [
    {
      path: ['asset_daily'],
      __typename: 'AssetKey',
    },
    {
      path: ['asset_weekly'],
      __typename: 'AssetKey',
    },
  ],
  __typename: 'PartitionBackfill',
};

const BackfillTablePureAssetNoCountsOrPartitionNames: BackfillTableFragment = {
  backfillId: 'vlpmimsl',
  status: BulkActionStatus.COMPLETED,
  isValidSerialization: true,
  numPartitions: null,
  timestamp: 1677078839.707758,
  partitionSetName: null,
  partitionSet: null,
  error: {
    __typename: 'PythonError',
    message:
      'dagster._core.errors.DagsterLaunchFailedError: Tried to start a run on a server after telling it to shut down\n',
    stack: ['OMITTED FROM MOCKS'],
    errorChain: [],
  },
  numCancelable: 0,
  partitionNames: null,
  assetSelection: [
    {
      path: ['asset_daily'],
      __typename: 'AssetKey',
    },
    {
      path: ['asset_weekly'],
      __typename: 'AssetKey',
    },
  ],
  __typename: 'PartitionBackfill',
};

export const BackfillTableFragments: BackfillTableFragment[] = [
  BackfillTableFragmentRequested2000AssetsPure,
  BackfillTableFragmentCancelledAssetsPartitionSet,
  BackfillTableFragmentFailedError,
  BackfillTableFragmentCompletedAssetJob,
  BackfillTableFragmentCompletedOpJob,
  BackfillTableFragmentInvalidPartitionSet,
  BackfillTablePureAssetCountsOnly,
  BackfillTablePureAssetNoCountsOrPartitionNames,
];
