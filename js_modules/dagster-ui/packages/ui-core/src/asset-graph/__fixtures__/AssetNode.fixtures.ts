import {
  AssetCheckExecutionResolvedStatus,
  AssetCheckSeverity,
  ChangeReason,
  RunStatus,
  StaleCause,
  StaleCauseCategory,
  StaleStatus,
  buildAssetCheck,
  buildAssetCheckEvaluation,
  buildAssetCheckExecution,
  buildAssetFreshnessInfo,
  buildAssetKey,
  buildAssetNode,
  buildMaterializationEvent,
  buildRun,
} from '../../graphql/types';
import {LiveDataForNodeWithStaleData} from '../Utils';
import {AssetNodeFragment} from '../types/AssetNode.types';

export const MockStaleReasonData: StaleCause = {
  __typename: 'StaleCause',
  key: {
    path: ['asset0'],
    __typename: 'AssetKey',
  },
  partitionKey: null,
  reason: 'has a new data version',
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
  reason: 'has a new code version',
  category: StaleCauseCategory.CODE,
  dependency: {
    path: ['asset1'],
    __typename: 'AssetKey',
  },
  dependencyPartitionKey: null,
};

const TIMESTAMP = `${new Date('2023-02-12 00:00:00').getTime()}`;

export const AssetNodeFragmentBasic: AssetNodeFragment = buildAssetNode({
  assetKey: buildAssetKey({path: ['asset1']}),
  computeKind: null,
  description: 'This is a test asset description',
  graphName: null,
  hasMaterializePermission: true,
  id: '["asset1"]',
  isObservable: false,
  isPartitioned: false,
  isMaterializable: true,
  jobNames: ['job1'],
  opNames: ['asset1'],
  opVersion: '1',
  changedReasons: [
    ChangeReason.NEW,
    ChangeReason.CODE_VERSION,
    ChangeReason.DEPENDENCIES,
    ChangeReason.PARTITIONS_DEFINITION,
    ChangeReason.TAGS,
    ChangeReason.METADATA,
    ChangeReason.REMOVED,
  ],
});

export const AssetNodeFragmentSource = buildAssetNode({
  ...AssetNodeFragmentBasic,
  assetKey: buildAssetKey({path: ['source_asset']}),
  description: 'This is a test source asset',
  id: '["source_asset"]',
  isObservable: true,
  isMaterializable: false,
  jobNames: [],
  opNames: [],
});

export const AssetNodeFragmentSourceOverdue = buildAssetNode({
  isMaterializable: false,
  isObservable: false,
  freshnessInfo: buildAssetFreshnessInfo({
    currentMinutesLate: 12,
  }),
});

export const AssetNodeFragmentPartitioned: AssetNodeFragment = buildAssetNode({
  ...AssetNodeFragmentBasic,
  assetKey: buildAssetKey({path: ['asset_partioned']}),
  description: 'This is a partitioned asset description',
  id: '["asset_partioned"]',
  isPartitioned: true,
});

export const LiveDataForNodeRunStartedNotMaterializing: LiveDataForNodeWithStaleData = {
  stepKey: 'asset2',
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
  opNames: [],
};

export const LiveDataForNodeRunStartedMaterializing: LiveDataForNodeWithStaleData = {
  stepKey: 'asset3',
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
  opNames: [],
};

export const LiveDataForNodeRunFailed: LiveDataForNodeWithStaleData = {
  stepKey: 'asset4',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: buildRun({
    id: 'ABCDEF',
    status: RunStatus.FAILURE,
    endTime: 1673301346,
  }),
  staleStatus: null,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: null,
  opNames: [],
};

export const LiveDataForNodeNeverMaterialized: LiveDataForNodeWithStaleData = {
  stepKey: 'asset5',
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
  opNames: [],
};

export const LiveDataForNodeMaterialized: LiveDataForNodeWithStaleData = {
  stepKey: 'asset6',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  }),
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: null,
  opNames: [],
};

export const LiveDataForNodeMaterializedWithChecks: LiveDataForNodeWithStaleData = {
  stepKey: 'asset7',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  }),
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
  opNames: [],
};

export const LiveDataForNodeMaterializedWithChecksOk: LiveDataForNodeWithStaleData = {
  ...LiveDataForNodeMaterializedWithChecks,
  assetChecks: LiveDataForNodeMaterializedWithChecks.assetChecks.filter(
    (c) => c.executionForLatestMaterialization?.evaluation?.severity !== AssetCheckSeverity.ERROR,
  ),
};

export const LiveDataForNodeMaterializedAndStale: LiveDataForNodeWithStaleData = {
  stepKey: 'asset8',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  }),
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.STALE,
  staleCauses: [MockStaleReasonCode],
  assetChecks: [],
  freshnessInfo: null,
  partitionStats: null,
  opNames: [],
};

export const LiveDataForNodeMaterializedAndStaleAndOverdue: LiveDataForNodeWithStaleData = {
  stepKey: 'asset9',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  }),
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
  opNames: [],
};

export const LiveDataForNodeMaterializedAndStaleAndFresh: LiveDataForNodeWithStaleData = {
  stepKey: 'asset10',

  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  }),
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.STALE,
  staleCauses: [
    MockStaleReasonCode,
    MockStaleReasonData,
    MockStaleReasonData,
    MockStaleReasonData,
    MockStaleReasonData,
    MockStaleReasonData,
    MockStaleReasonData,
    MockStaleReasonData,
    MockStaleReasonData,
    MockStaleReasonData,
    MockStaleReasonData,
    MockStaleReasonData,
  ],
  assetChecks: [],
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 0,
  },
  partitionStats: null,
  opNames: [],
};

export const LiveDataForNodeMaterializedAndFresh: LiveDataForNodeWithStaleData = {
  stepKey: 'asset11',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  }),
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
  opNames: [],
};

export const LiveDataForNodeMaterializedAndOverdue: LiveDataForNodeWithStaleData = {
  stepKey: 'asset12',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  }),
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
  opNames: [],
};

export const LiveDataForNodeFailedAndOverdue: LiveDataForNodeWithStaleData = {
  stepKey: 'asset13',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterializationRunStatus: null,
  lastObservation: null,
  lastMaterialization: null,
  runWhichFailedToMaterialize: buildRun({
    id: '123456',
    status: RunStatus.FAILURE,
    endTime: 1673301346,
  }),
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: buildAssetFreshnessInfo({
    currentMinutesLate: 12,
  }),
  partitionStats: null,
  opNames: [],
};

export const LiveDataForNodeSourceNeverObserved: LiveDataForNodeWithStaleData = {
  stepKey: 'source_asset2',
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
  opNames: [],
};

export const LiveDataForNodeSourceObservationRunning: LiveDataForNodeWithStaleData = {
  stepKey: 'source_asset3',
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
  opNames: [],
};
export const LiveDataForNodeSourceObservedUpToDate: LiveDataForNodeWithStaleData = {
  stepKey: 'source_asset4',
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
  opNames: [],
  partitionStats: null,
};

export const LiveDataForNodePartitionedSomeMissing: LiveDataForNodeWithStaleData = {
  stepKey: 'partitioned_asset1',
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
  opNames: [],
};

export const LiveDataForNodePartitionedSomeFailed: LiveDataForNodeWithStaleData = {
  stepKey: 'partitioned_asset2',
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
  opNames: [],
};

export const LiveDataForNodePartitionedNoneMissing: LiveDataForNodeWithStaleData = {
  stepKey: 'partitioned_asset3',
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
  opNames: [],
};

export const LiveDataForNodePartitionedNeverMaterialized: LiveDataForNodeWithStaleData = {
  stepKey: 'asset20',
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
  opNames: [],
};

export const LiveDataForNodePartitionedMaterializing: LiveDataForNodeWithStaleData = {
  stepKey: 'asset21',
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
  opNames: [],
};

export const LiveDataForNodePartitionedStale: LiveDataForNodeWithStaleData = {
  stepKey: 'asset22',
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
  opNames: [],
};

export const LiveDataForNodePartitionedOverdue: LiveDataForNodeWithStaleData = {
  stepKey: 'asset23',
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
  opNames: [],
};

export const LiveDataForNodePartitionedFresh: LiveDataForNodeWithStaleData = {
  stepKey: 'asset24',
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
  opNames: [],
};

export const LiveDataForNodePartitionedLatestRunFailed: LiveDataForNodeWithStaleData = {
  stepKey: 'asset25',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: buildRun({
    id: 'ABCDEF',
    status: RunStatus.FAILURE,
    endTime: 1673301346,
  }),
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
  opNames: [],
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
    title: 'Never Materialized, Failed Check',
    liveData: {
      ...LiveDataForNodeNeverMaterialized,
      assetChecks: LiveDataForNodeMaterializedWithChecks.assetChecks,
    },
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
    expectedText: ['Unsynced', 'Feb'],
  },

  {
    title: 'Materialized and Stale and Overdue',
    liveData: LiveDataForNodeMaterializedAndStaleAndOverdue,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Unsynced', 'Overdue', 'Feb'],
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
    definition: {
      ...AssetNodeFragmentSource,
      isObservable: false,
      id: '["source_asset_no"]',
      assetKey: buildAssetKey({path: ['source_asset_no']}),
    },
    expectedText: [],
  },

  {
    title: 'Source Asset - Not Observable, No Description',
    liveData: undefined,
    definition: {
      ...AssetNodeFragmentSource,
      isObservable: false,
      description: null,
      id: '["source_asset_nono"]',
      assetKey: buildAssetKey({path: ['source_asset_nono']}),
    },
    expectedText: [],
  },

  {
    title: 'Source Asset - Never Observed',
    liveData: LiveDataForNodeSourceNeverObserved,
    definition: AssetNodeFragmentSource,
    expectedText: ['Never observed', '–'],
  },

  {
    title: 'Source Asset - Overdue',
    liveData: LiveDataForNodeMaterializedAndOverdue,
    definition: AssetNodeFragmentSourceOverdue,
    expectedText: ['Overdue', 'Feb'],
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
