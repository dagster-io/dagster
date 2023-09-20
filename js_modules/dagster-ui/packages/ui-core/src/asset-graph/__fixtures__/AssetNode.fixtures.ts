import {
  RunStatus,
  StaleStatus,
  StaleCause,
  StaleCauseCategory,
  AssetCheckSeverity,
  AssetCheckExecutionResolvedStatus,
  buildAssetCheckExecution,
  buildAssetCheckEvaluation,
  buildAssetCheck,
} from '../../graphql/types';
import {LiveDataForNode} from '../Utils';
import {AssetNodeFragment} from '../types/AssetNode.types';

export const MockStaleReasonData: StaleCause = {
  __typename: 'StaleCause',
  key: {
    path: ['asset0'],
    __typename: 'AssetKey',
  },
  partitionKey: null,
  reason: 'updated data version',
  category: StaleCauseCategory.DATA,
  dependency: {
    path: ['asset0'],
    __typename: 'AssetKey',
  },
  dependencyPartitionKey: null,
};

export const MockStaleReasonCode: StaleCause = {
  __typename: 'StaleCause',
  key: {
    path: ['asset1'],
    __typename: 'AssetKey',
  },
  partitionKey: null,
  reason: 'code version changed',
  category: StaleCauseCategory.CODE,
  dependency: {
    path: ['asset1'],
    __typename: 'AssetKey',
  },
  dependencyPartitionKey: null,
};

const TIMESTAMP = `${new Date('2023-02-12 00:00:00').getTime()}`;

export const AssetNodeFragmentBasic: AssetNodeFragment = {
  __typename: 'AssetNode',
  assetKey: {__typename: 'AssetKey', path: ['asset1']},
  computeKind: null,
  description: 'This is a test asset description',
  graphName: null,
  hasMaterializePermission: true,
  id: '["asset1"]',
  isObservable: false,
  isPartitioned: false,
  isSource: false,
  jobNames: ['job1'],
  opNames: ['asset1'],
  opVersion: '1',
};

export const AssetNodeFragmentSource: AssetNodeFragment = {
  ...AssetNodeFragmentBasic,
  assetKey: {__typename: 'AssetKey', path: ['source_asset']},
  description: 'This is a test source asset',
  id: '["source_asset"]',
  isObservable: true,
  isSource: true,
  jobNames: [],
  opNames: [],
};

export const AssetNodeFragmentPartitioned: AssetNodeFragment = {
  ...AssetNodeFragmentBasic,
  assetKey: {__typename: 'AssetKey', path: ['asset1']},
  description: 'This is a partitioned asset description',
  id: '["asset1"]',
  isPartitioned: true,
};

export const LiveDataForNodeRunStartedNotMaterializing: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: ['ABCDEF'],
  inProgressRunIds: [],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: null,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: null,
};

export const LiveDataForNodeRunStartedMaterializing: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: ['ABCDEF'],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: null,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: null,
};

export const LiveDataForNodeRunFailed: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: {
    __typename: 'Run',
    id: 'ABCDEF',
    status: RunStatus.FAILURE,
    endTime: 1673301346,
  },
  staleStatus: null,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: null,
};

export const LiveDataForNodeNeverMaterialized: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.MISSING,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: null,
};

export const LiveDataForNodeMaterialized: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: null,
};

export const LiveDataForNodeMaterializedWithChecks: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [
    buildAssetCheck({
      name: 'check_1',
      executionForLatestMaterialization: buildAssetCheckExecution({
        runId: '1234',
        status: AssetCheckExecutionResolvedStatus.FAILED,
        evaluation: buildAssetCheckEvaluation({
          severity: AssetCheckSeverity.WARN,
        }),
      }),
    }),
    buildAssetCheck({
      name: 'check_2',
      executionForLatestMaterialization: buildAssetCheckExecution({
        runId: '1234',
        status: AssetCheckExecutionResolvedStatus.FAILED,
        evaluation: buildAssetCheckEvaluation({
          severity: AssetCheckSeverity.ERROR,
        }),
      }),
    }),
    buildAssetCheck({
      name: 'check_3',
      executionForLatestMaterialization: buildAssetCheckExecution({
        runId: '1234',
        status: AssetCheckExecutionResolvedStatus.IN_PROGRESS,
        evaluation: buildAssetCheckEvaluation({
          severity: AssetCheckSeverity.WARN,
        }),
      }),
    }),
    buildAssetCheck({
      name: 'check_4',
      executionForLatestMaterialization: buildAssetCheckExecution({
        runId: '1234',
        status: AssetCheckExecutionResolvedStatus.SKIPPED,
        evaluation: buildAssetCheckEvaluation({
          severity: AssetCheckSeverity.WARN,
        }),
      }),
    }),
    buildAssetCheck({
      name: 'check_5',
      executionForLatestMaterialization: buildAssetCheckExecution({
        runId: '1234',
        status: AssetCheckExecutionResolvedStatus.SUCCEEDED,
        evaluation: buildAssetCheckEvaluation({
          severity: AssetCheckSeverity.WARN,
        }),
      }),
    }),
  ],
  freshnessInfo: null,
  partitionStats: null,
};

export const LiveDataForNodeMaterializedWithChecksOk: LiveDataForNode = {
  ...LiveDataForNodeMaterializedWithChecks,
  assetChecks: LiveDataForNodeMaterializedWithChecks.assetChecks.filter(
    (c) => c.executionForLatestMaterialization?.evaluation?.severity !== AssetCheckSeverity.ERROR,
  ),
};

export const LiveDataForNodeMaterializedAndStale: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.STALE,
  staleCauses: [MockStaleReasonCode],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: null,
};

export const LiveDataForNodeMaterializedAndStaleAndOverdue: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.STALE,
  staleCauses: [MockStaleReasonCode],
  assetChecks: [],
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 12,
  },
  partitionStats: null,
};

export const LiveDataForNodeMaterializedAndStaleAndFresh: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.STALE,
  staleCauses: [MockStaleReasonCode, MockStaleReasonData],
  assetChecks: [],
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 0,
  },
  partitionStats: null,
};

export const LiveDataForNodeMaterializedAndFresh: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 0,
  },
  partitionStats: null,
};

export const LiveDataForNodeMaterializedAndOverdue: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 12,
  },
  partitionStats: null,
};

export const LiveDataForNodeFailedAndOverdue: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterializationRunStatus: null,
  lastObservation: null,
  lastMaterialization: null,
  runWhichFailedToMaterialize: {
    __typename: 'Run',
    id: '123456',
    status: RunStatus.FAILURE,
    endTime: 1673301346,
  },
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 12,
  },
  partitionStats: null,
};

export const LiveDataForNodeSourceNeverObserved: LiveDataForNode = {
  stepKey: 'source_asset',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.MISSING,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,

  partitionStats: null,
};

export const LiveDataForNodeSourceObservationRunning: LiveDataForNode = {
  stepKey: 'source_asset',
  unstartedRunIds: [],
  inProgressRunIds: ['ABCDEF'],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.MISSING,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: null,
};
export const LiveDataForNodeSourceObservedUpToDate: LiveDataForNode = {
  stepKey: 'source_asset',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: {
    __typename: 'ObservationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,

  partitionStats: null,
};

export const LiveDataForNodePartitionedSomeMissing: LiveDataForNode = {
  stepKey: 'partitioned_asset',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: {
    numMaterialized: 6,
    numMaterializing: 0,
    numPartitions: 1500,
    numFailed: 0,
  },
};

export const LiveDataForNodePartitionedSomeFailed: LiveDataForNode = {
  stepKey: 'partitioned_asset',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: {
    numMaterialized: 6,
    numMaterializing: 0,
    numPartitions: 1500,
    numFailed: 849,
  },
};

export const LiveDataForNodePartitionedNoneMissing: LiveDataForNode = {
  stepKey: 'partitioned_asset',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: {
    numMaterialized: 1500,
    numMaterializing: 0,
    numPartitions: 1500,
    numFailed: 0,
  },
};

export const LiveDataForNodePartitionedNeverMaterialized: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.MISSING,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: {
    numMaterialized: 0,
    numMaterializing: 0,
    numPartitions: 1500,
    numFailed: 0,
  },
};

export const LiveDataForNodePartitionedMaterializing: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: ['LMAANO'],
  inProgressRunIds: ['ABCDEF', 'CDEFG', 'HIHKA'],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.MISSING,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: {
    numMaterialized: 0,
    numMaterializing: 5,
    numPartitions: 1500,
    numFailed: 0,
  },
};

export const LiveDataForNodePartitionedStale: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.STALE,
  staleCauses: [MockStaleReasonData],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: {
    numMaterialized: 1500,
    numMaterializing: 0,
    numPartitions: 1500,
    numFailed: 0,
  },
};

export const LiveDataForNodePartitionedOverdue: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 12,
  },
  partitionStats: {
    numMaterialized: 1500,
    numMaterializing: 0,
    numPartitions: 1500,
    numFailed: 0,
  },
};

export const LiveDataForNodePartitionedFresh: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 0,
  },
  partitionStats: {
    numMaterialized: 1500,
    numMaterializing: 0,
    numPartitions: 1500,
    numFailed: 0,
  },
};

export const LiveDataForNodePartitionedLatestRunFailed: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: {
    __typename: 'Run',
    id: 'ABCDEF',
    status: RunStatus.FAILURE,
    endTime: 1673301346,
  },
  staleStatus: null,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: {
    numMaterialized: 1495,
    numMaterializing: 0,
    numPartitions: 1500,
    numFailed: 1,
  },
};

export const AssetNodeScenariosBase = [
  {
    title: 'No Live Data',
    liveData: undefined,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Loading'],
  },

  {
    title: 'Run Started - Not Materializing Yet',
    liveData: LiveDataForNodeRunStartedNotMaterializing,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Materializing...', 'ABCDEF'],
  },
  {
    title: 'Run Started - Materializing',
    liveData: LiveDataForNodeRunStartedMaterializing,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Materializing...', 'ABCDEF'],
  },

  {
    title: 'Run Failed to Materialize',
    liveData: LiveDataForNodeRunFailed,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Failed', 'Jan'],
  },

  {
    title: 'Never Materialized',
    liveData: LiveDataForNodeNeverMaterialized,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Never materialized'],
  },

  {
    title: 'Materialized',
    liveData: LiveDataForNodeMaterialized,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Materialized', 'Feb'],
  },

  {
    title: 'Materialized and Stale',
    liveData: LiveDataForNodeMaterializedAndStale,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Code version', 'Feb'],
  },

  {
    title: 'Materialized and Stale and Overdue',
    liveData: LiveDataForNodeMaterializedAndStaleAndOverdue,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Code version', 'Overdue', 'Feb'],
  },

  {
    title: 'Materialized and Stale and Fresh',
    liveData: LiveDataForNodeMaterializedAndStaleAndFresh,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Materialized'],
  },

  {
    title: 'Materialized and Fresh',
    liveData: LiveDataForNodeMaterializedAndFresh,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Materialized'],
  },

  {
    title: 'Materialized and Overdue',
    liveData: LiveDataForNodeMaterializedAndOverdue,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Overdue', 'Feb'],
  },
  {
    title: 'Materialized and Failed and Overdue',
    liveData: LiveDataForNodeFailedAndOverdue,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Failed, Overdue', 'Jan'],
  },
  {
    title: 'Materialized with Checks (Ok)',
    liveData: LiveDataForNodeMaterializedWithChecksOk,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Materialized', 'Checks'],
  },
  {
    title: 'Materialized with Checks (Failed)',
    liveData: LiveDataForNodeMaterializedWithChecks,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Materialized', 'Checks'],
  },
];

export const AssetNodeScenariosSource = [
  {
    title: 'Source Asset - No Live Data',
    liveData: undefined,
    definition: AssetNodeFragmentSource,
    expectedText: ['Loading'],
  },

  {
    title: 'Source Asset - Not Observable',
    liveData: undefined,
    definition: {...AssetNodeFragmentSource, isObservable: false},
    expectedText: [],
  },

  {
    title: 'Source Asset - Not Observable, No Description',
    liveData: undefined,
    definition: {...AssetNodeFragmentSource, isObservable: false, description: null},
    expectedText: [],
  },

  {
    title: 'Source Asset - Never Observed',
    liveData: LiveDataForNodeSourceNeverObserved,
    definition: AssetNodeFragmentSource,
    expectedText: ['Never observed', '–'],
  },

  {
    title: 'Source Asset - Observation Running',
    liveData: LiveDataForNodeSourceObservationRunning,
    definition: AssetNodeFragmentSource,
    expectedText: ['Observing...', 'ABCDEF'],
  },

  {
    title: 'Source Asset - Observed, Up To Date',
    liveData: LiveDataForNodeSourceObservedUpToDate,
    definition: AssetNodeFragmentSource,
    expectedText: ['Observed', 'Feb'],
  },
];

export const AssetNodeScenariosPartitioned = [
  {
    title: 'Partitioned Asset - Some Missing',
    liveData: LiveDataForNodePartitionedSomeMissing,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['999+', '6', '1,500 partitions'],
  },

  {
    title: 'Partitioned Asset - Some Failed',
    liveData: LiveDataForNodePartitionedSomeFailed,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['645', '849', '1,500 partitions'],
  },

  {
    title: 'Partitioned Asset - None Missing',
    liveData: LiveDataForNodePartitionedNoneMissing,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['1,500 partitions', 'All'],
  },

  {
    title: 'Never Materialized',
    liveData: LiveDataForNodePartitionedNeverMaterialized,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['1,500 partitions'],
  },

  {
    title: 'Materializing...',
    liveData: LiveDataForNodePartitionedMaterializing,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['Materializing 5 partitions'],
  },

  {
    title: 'Partitioned Asset - Overdue',
    liveData: LiveDataForNodePartitionedOverdue,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['All', 'Overdue'],
  },

  {
    title: 'Partitioned Asset - Fresh',
    liveData: LiveDataForNodePartitionedFresh,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['1,500 partitions', 'All'],
  },

  {
    title: 'Partitioned Asset - Last Run Failed',
    liveData: LiveDataForNodePartitionedLatestRunFailed,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['4', '999+', '1,500 partitions'],
  },
  {
    title: 'Partitioned Asset - Live Data Loading',
    liveData: undefined,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['Loading'],
  },
];
