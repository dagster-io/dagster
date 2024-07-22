import {MockedResponse} from '@apollo/client/testing';

import {
  BulkActionStatus,
  RunStatus,
  buildAssetKey,
  buildErrorChainLink,
  buildPartitionBackfill,
  buildPartitionSet,
  buildPartitionStatus,
  buildPartitionStatusCounts,
  buildPartitionStatuses,
  buildPythonError,
  buildRepositoryOrigin,
  buildRun,
} from '../../../graphql/types';
import {DagsterTag} from '../../../runs/RunTag';
import {
  SINGLE_BACKFILL_CANCELABLE_RUNS_QUERY,
} from '../BackfillRow';
import {SingleBackfillQuery} from '../types/BackfillRow.types';
import {BackfillTableFragment} from '../types/BackfillTable.types';

function buildTimePartitionNames(start: Date, count: number) {
  const results: string[] = [];
  for (let ii = 0; ii < count; ii++) {
    start.setMinutes(start.getMinutes() + 15);
    results.push(start.toISOString());
  }
  return results;
}

export const BackfillTableFragmentRequested2000AssetsPure: BackfillTableFragment =
  buildPartitionBackfill({
    id: 'qtpussca',
    status: BulkActionStatus.REQUESTED,
    numPartitions: 2000,
    hasCancelPermission: true,
    hasResumePermission: true,
    isValidSerialization: true,
    timestamp: 1675196684.587724,
    partitionSetName: null,
    partitionSet: null,
    error: null,
    numCancelable: 0,
    partitionNames: buildTimePartitionNames(new Date('2020-01-01'), 2000),
    assetSelection: [
      buildAssetKey({
        path: ['global_graph_asset'],
      }),
    ],
  });

export const BackfillTableFragmentCancelledAssetsPartitionSet: BackfillTableFragment =
  buildPartitionBackfill({
    id: 'tclwoggv',
    status: BulkActionStatus.CANCELED,
    isValidSerialization: true,
    numPartitions: 5000,
    hasCancelPermission: true,
    hasResumePermission: true,
    timestamp: 1675106258.398993,
    partitionSetName: 'asset_job_partition_set',
    partitionSet: buildPartitionSet({
      id: '74c11a15d5d213176c83a7a71b50be0318103d8b',
      name: 'asset_job_partition_set',
      mode: 'default',
      pipelineName: 'asset_job',
      repositoryOrigin: buildRepositoryOrigin({
        id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
        repositoryName: 'repo',
        repositoryLocationName: 'test.py',
      }),
    }),
    error: null,
    numCancelable: 0,
    partitionNames: buildTimePartitionNames(new Date('2020-01-01'), 5000),
    assetSelection: [
      buildAssetKey({
        path: ['whatever5'],
      }),
      buildAssetKey({
        path: ['multipartitioned_asset'],
      }),
    ],
    tags: [
      {
        __typename: 'PipelineTag',
        key: DagsterTag.SensorName,
        value: 'MySensor',
      },
    ],
  });

export const BackfillTableFragmentFailedError: BackfillTableFragment = buildPartitionBackfill({
  id: 'sjqzcfhe',
  status: BulkActionStatus.FAILED,
  isValidSerialization: true,
  numPartitions: 100,
  hasCancelPermission: true,
  hasResumePermission: true,
  timestamp: 1674774274.343382,
  partitionSetName: null,
  partitionSet: null,
  error: buildPythonError({
    message:
      'dagster._core.errors.DagsterLaunchFailedError: Tried to start a run on a server after telling it to shut down\n',
    stack: ['OMITTED FROM MOCKS'],
    errorChain: [],
  }),
  numCancelable: 0,
  partitionNames: buildTimePartitionNames(new Date('2020-01-01'), 100),
  assetSelection: [
    buildAssetKey({
      path: ['multipartitioned_asset'],
    }),
  ],
});

export const BackfillTableFragmentFailedErrorStatus: MockedResponse<SingleBackfillQuery> = {
  request: {
    query: SINGLE_BACKFILL_CANCELABLE_RUNS_QUERY,
    variables: {
      backfillId: 'sjqzcfhe',
    },
  },
  result: {
    data: {
      __typename: 'Query',
      partitionBackfillOrError: buildPartitionBackfill({
        id: 'sjqzcfhe',
        cancelableRuns: [],
      }),
    },
  },
};

export const BackfillTableFragmentCompletedAssetJob: BackfillTableFragment = buildPartitionBackfill(
  {
    id: 'pwgcpiwc',
    status: BulkActionStatus.COMPLETED,
    isValidSerialization: true,
    numPartitions: 11,
    hasCancelPermission: true,
    hasResumePermission: true,
    timestamp: 1674660450.942305,
    isAssetBackfill: true,
    partitionSetName: 'asset_job_partition_set',
    partitionSet: buildPartitionSet({
      id: '74c11a15d5d213176c83a7a71b50be0318103d8b',
      name: 'asset_job_partition_set',
      mode: 'default',
      pipelineName: 'asset_job',
      repositoryOrigin: buildRepositoryOrigin({
        id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
        repositoryName: 'repo',
        repositoryLocationName: 'test.py',
      }),
    }),
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
      buildAssetKey({
        path: ['multipartitioned_asset'],
      }),
    ],
    tags: [
      {
        __typename: 'PipelineTag',
        key: DagsterTag.User,
        value: 'user@dagsterlabs.com',
      },
    ],
  },
);

export const BackfillTableFragmentCompletedAssetJobStatus: MockedResponse<SingleBackfillQuery> = {
  request: {
    query: SINGLE_BACKFILL_CANCELABLE_RUNS_QUERY,
    variables: {
      backfillId: 'pwgcpiwc',
    },
  },
  result: {
    data: {
      __typename: 'Query',
      partitionBackfillOrError: {
        id: 'pwgcpiwc',
        cancelableRuns: [],
        __typename: 'PartitionBackfill',
      },
    },
  },
};

export const BackfillTableFragmentCompletedOpJob: BackfillTableFragment = buildPartitionBackfill({
  id: 'pqdiepuf',
  status: BulkActionStatus.COMPLETED,
  isValidSerialization: true,
  numPartitions: 4,
  hasCancelPermission: true,
  hasResumePermission: true,
  timestamp: 1674660356.340658,
  partitionSetName: 'op_job_partition_set',
  partitionSet: buildPartitionSet({
    id: 'a41b026cedcc5f871b4bf10db6e56ec1c63b8df0',
    name: 'op_job_partition_set',
    mode: 'default',
    pipelineName: 'op_job',
    repositoryOrigin: buildRepositoryOrigin({
      id: 'c22d9677b8089be89b1e014b9de34284962f83a7',
      repositoryName: 'repo',
      repositoryLocationName: 'test.py',
    }),
  }),
  error: null,
  numCancelable: 0,
  partitionNames: ['2022-07-01', '2022-08-01', '2022-09-01', '2022-10-01'],
  assetSelection: null,
});

export const BackfillTableFragmentCompletedOpJobStatus: MockedResponse<SingleBackfillQuery> = {
  request: {
    query: SINGLE_BACKFILL_CANCELABLE_RUNS_QUERY,
    variables: {
      backfillId: 'pqdiepuf',
    },
  },
  result: {
    data: {
      __typename: 'Query',
      partitionBackfillOrError: buildPartitionBackfill({
        id: 'pqdiepuf',
        isAssetBackfill: true,
        cancelableRuns: [buildRun({runId: '1baeadb4-7e7d-47e5-aeac-8a5f921cf27c', status: RunStatus.QUEUED})],
      }),
    },
  },
};

export const BackfillTableFragmentInvalidPartitionSet: BackfillTableFragment =
  buildPartitionBackfill({
    id: 'jzduiapb',
    status: BulkActionStatus.COMPLETED,
    isValidSerialization: false,
    numPartitions: 0,
    hasCancelPermission: true,
    hasResumePermission: true,
    timestamp: 1676397948.698646,
    partitionSetName: null,
    partitionSet: null,
    error: null,
    numCancelable: 0,
    partitionNames: [],
    isAssetBackfill: true,
    assetSelection: [
      buildAssetKey({
        path: ['asset1'],
        __typename: 'AssetKey',
      }),
      buildAssetKey({
        path: ['asset2'],
        __typename: 'AssetKey',
      }),
    ],
  });

export const BackfillTablePureAssetCountsOnly: BackfillTableFragment = buildPartitionBackfill({
  id: 'likqkgna',
  status: BulkActionStatus.CANCELING,
  isValidSerialization: true,
  numPartitions: 30,
  hasCancelPermission: true,
  hasResumePermission: true,
  timestamp: 1677023094.435064,
  partitionSetName: null,
  partitionSet: null,
  isAssetBackfill: true,
  error: buildPythonError({
    message:
      'dagster._core.errors.DagsterUserCodeUnreachableError: Could not reach user code server. gRPC Error code: UNAVAILABLE\n',
    stack: ['OMITTED FROM MOCKS'],
    errorChain: [
      buildErrorChainLink({
        isExplicitLink: true,
        error: buildPythonError({
          message:
            'grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:\n\tstatus = StatusCode.UNAVAILABLE\n\tdetails = "failed to connect to all addresses"\n\tdebug_error_string = "{"created":"@1677105084.883333000","description":"Failed to pick subchannel","file":"src/core/ext/filters/client_channel/client_channel.cc","file_line":3261,"referenced_errors":[{"created":"@1677105084.883332000","description":"failed to connect to all addresses","file":"src/core/lib/transport/error_utils.cc","file_line":167,"grpc_status":14}]}"\n>\n',
          stack: ['OMITTED FROM MOCKS'],
        }),
      }),
    ],
  }),
  numCancelable: 0,
  partitionNames: null,
  assetSelection: [
    buildAssetKey({
      path: ['asset_daily'],
    }),
    buildAssetKey({
      path: ['asset_weekly'],
    }),
  ],
});

const BackfillTablePureAssetNoCountsOrPartitionNames: BackfillTableFragment =
  buildPartitionBackfill({
    id: 'vlpmimsl',
    status: BulkActionStatus.COMPLETED,
    isValidSerialization: true,
    numPartitions: null,
    hasCancelPermission: true,
    hasResumePermission: true,
    timestamp: 1677078839.707758,
    partitionSetName: null,
    partitionSet: null,
    isAssetBackfill: true,
    error: buildPythonError({
      message:
        'dagster._core.errors.DagsterLaunchFailedError: Tried to start a run on a server after telling it to shut down\n',
      stack: ['OMITTED FROM MOCKS'],
      errorChain: [],
    }),
    numCancelable: 0,
    partitionNames: null,
    assetSelection: [
      buildAssetKey({
        path: ['asset_daily'],
      }),
      buildAssetKey({
        path: ['asset_weekly'],
      }),
    ],
  });

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
