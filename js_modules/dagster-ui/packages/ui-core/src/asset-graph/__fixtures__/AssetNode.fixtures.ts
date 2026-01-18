import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {
  AssetCheckExecutionResolvedStatus,
  AssetCheckSeverity,
  AssetHealth,
  AssetHealthStatus,
  ChangeReason,
  RunStatus,
  StaleCauseCategory,
  StaleStatus,
  buildAsset,
  buildAssetCheck,
  buildAssetCheckEvaluation,
  buildAssetCheckExecution,
  buildAssetFreshnessInfo,
  buildAssetHealth,
  buildAssetHealthCheckDegradedMeta,
  buildAssetHealthCheckUnknownMeta,
  buildAssetHealthFreshnessMeta,
  buildAssetHealthMaterializationDegradedNotPartitionedMeta,
  buildAssetHealthMaterializationDegradedPartitionedMeta,
  buildAssetHealthMaterializationHealthyPartitionedMeta,
  buildAssetKey,
  buildAssetNode,
  buildMaterializationEvent,
  buildObservationEvent,
  buildRun,
  buildStaleCause,
  buildTeamAssetOwner,
  buildUserAssetOwner,
} from '../../graphql/types';
import {LiveDataForNodeWithStaleData} from '../Utils';
import {AssetNodeFragment} from '../types/AssetNode.types';

export const MockStaleReasonData = buildStaleCause({
  key: buildAssetKey({path: ['asset0']}),
  partitionKey: null,
  reason: 'has a new data version',
  category: StaleCauseCategory.DATA,
  dependency: buildAssetKey({path: ['asset0']}),
  dependencyPartitionKey: null,
});

export const MockStaleReasonCode = buildStaleCause({
  key: buildAssetKey({path: ['asset1']}),
  partitionKey: null,
  reason: 'has a new code version',
  category: StaleCauseCategory.CODE,
  dependency: buildAssetKey({path: ['asset1']}),
  dependencyPartitionKey: null,
});

const TIMESTAMP = `${new Date('2023-02-12 00:00:00').getTime()}`;

// Health Data Fixtures - Helper function to create health data with custom asset key
const createHealthData = (
  assetKeyPath: string[],
  healthStatus: AssetHealthStatus,
  overrides: Partial<AssetHealthFragment> & {assetHealth?: AssetHealth} = {},
): AssetHealthFragment =>
  buildAsset({
    key: buildAssetKey({path: assetKeyPath}),
    latestMaterializationTimestamp:
      healthStatus === AssetHealthStatus.HEALTHY ? Number(TIMESTAMP) : null,
    latestFailedToMaterializeTimestamp:
      healthStatus === AssetHealthStatus.DEGRADED ? Number(TIMESTAMP) : null,
    freshnessStatusChangedTimestamp: Number(TIMESTAMP),
    assetHealth: buildAssetHealth({
      assetHealth: healthStatus,
      materializationStatus: healthStatus,
      assetChecksStatus: AssetHealthStatus.HEALTHY,
      freshnessStatus: AssetHealthStatus.HEALTHY,
      materializationStatusMetadata: null,
      assetChecksStatusMetadata: null,
      freshnessStatusMetadata: buildAssetHealthFreshnessMeta({
        lastMaterializedTimestamp:
          healthStatus === AssetHealthStatus.HEALTHY ? Number(TIMESTAMP) : null,
      }),
    }),
    ...overrides,
  });

export const HealthDataHealthy = createHealthData(['asset1'], AssetHealthStatus.HEALTHY);

export const HealthDataDegraded = createHealthData(['asset1'], AssetHealthStatus.DEGRADED, {
  assetHealth: buildAssetHealth({
    assetHealth: AssetHealthStatus.DEGRADED,
    materializationStatus: AssetHealthStatus.DEGRADED,
    assetChecksStatus: AssetHealthStatus.HEALTHY,
    freshnessStatus: AssetHealthStatus.HEALTHY,
    materializationStatusMetadata: buildAssetHealthMaterializationDegradedNotPartitionedMeta({
      failedRunId: 'ABCDEF',
    }),
    assetChecksStatusMetadata: null,
    freshnessStatusMetadata: buildAssetHealthFreshnessMeta({
      lastMaterializedTimestamp: null,
    }),
  }),
});

export const HealthDataWithFailedChecks = createHealthData(['asset1'], AssetHealthStatus.DEGRADED, {
  assetHealth: buildAssetHealth({
    assetHealth: AssetHealthStatus.DEGRADED,
    materializationStatus: AssetHealthStatus.HEALTHY,
    assetChecksStatus: AssetHealthStatus.DEGRADED,
    freshnessStatus: AssetHealthStatus.HEALTHY,
    materializationStatusMetadata: null,
    assetChecksStatusMetadata: buildAssetHealthCheckDegradedMeta({
      numFailedChecks: 1,
      numWarningChecks: 1,
      totalNumChecks: 5,
    }),
    freshnessStatusMetadata: buildAssetHealthFreshnessMeta({
      lastMaterializedTimestamp: Number(TIMESTAMP),
    }),
  }),
});

export const HealthDataOverdue = createHealthData(['asset1'], AssetHealthStatus.DEGRADED, {
  assetHealth: buildAssetHealth({
    assetHealth: AssetHealthStatus.DEGRADED,
    materializationStatus: AssetHealthStatus.HEALTHY,
    assetChecksStatus: AssetHealthStatus.HEALTHY,
    freshnessStatus: AssetHealthStatus.DEGRADED,
    materializationStatusMetadata: null,
    assetChecksStatusMetadata: null,
    freshnessStatusMetadata: buildAssetHealthFreshnessMeta({
      lastMaterializedTimestamp: Number(TIMESTAMP),
    }),
  }),
});

export const HealthDataPartitionedDegraded = createHealthData(
  ['asset1'],
  AssetHealthStatus.DEGRADED,
  {
    assetHealth: buildAssetHealth({
      assetHealth: AssetHealthStatus.DEGRADED,
      materializationStatus: AssetHealthStatus.DEGRADED,
      assetChecksStatus: AssetHealthStatus.HEALTHY,
      freshnessStatus: AssetHealthStatus.HEALTHY,
      materializationStatusMetadata: buildAssetHealthMaterializationDegradedPartitionedMeta({
        numMissingPartitions: 849,
        numFailedPartitions: 645,
        totalNumPartitions: 1500,
        latestFailedRunId: 'ABCDEF',
      }),
      assetChecksStatusMetadata: null,
      freshnessStatusMetadata: buildAssetHealthFreshnessMeta({
        lastMaterializedTimestamp: Number(TIMESTAMP),
      }),
    }),
  },
);

export const HealthDataPartitionedHealthy = createHealthData(
  ['asset1'],
  AssetHealthStatus.HEALTHY,
  {
    assetHealth: buildAssetHealth({
      assetHealth: AssetHealthStatus.HEALTHY,
      materializationStatus: AssetHealthStatus.HEALTHY,
      assetChecksStatus: AssetHealthStatus.HEALTHY,
      freshnessStatus: AssetHealthStatus.HEALTHY,
      materializationStatusMetadata: buildAssetHealthMaterializationHealthyPartitionedMeta({
        numMissingPartitions: 0,
        totalNumPartitions: 1500,
        latestRunId: 'ABCDEF',
      }),
      assetChecksStatusMetadata: null,
      freshnessStatusMetadata: buildAssetHealthFreshnessMeta({
        lastMaterializedTimestamp: Number(TIMESTAMP),
      }),
    }),
  },
);

export const HealthDataUnknown = createHealthData(['asset1'], AssetHealthStatus.UNKNOWN, {
  latestMaterializationTimestamp: null,
  latestFailedToMaterializeTimestamp: null,
  freshnessStatusChangedTimestamp: null,
  assetHealth: buildAssetHealth({
    assetHealth: AssetHealthStatus.UNKNOWN,
    materializationStatus: AssetHealthStatus.UNKNOWN,
    assetChecksStatus: AssetHealthStatus.UNKNOWN,
    freshnessStatus: AssetHealthStatus.UNKNOWN,
    materializationStatusMetadata: null,
    assetChecksStatusMetadata: buildAssetHealthCheckUnknownMeta({
      numNotExecutedChecks: 3,
      totalNumChecks: 3,
    }),
    freshnessStatusMetadata: null,
  }),
});

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
  changedReasons: [],
  owners: [
    buildUserAssetOwner({
      email: 'test@company.com',
    }),
    buildTeamAssetOwner({
      team: 'Team Foo',
    }),
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
  ...AssetNodeFragmentBasic,
  isMaterializable: false,
  isObservable: false,
  freshnessInfo: buildAssetFreshnessInfo({
    currentMinutesLate: 12,
  }),
});

export const AssetNodeFragmentChangedInBranch = buildAssetNode({
  ...AssetNodeFragmentBasic,
  kinds: ['sql'],
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
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    timestamp: TIMESTAMP,
  }),
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
  stepKey: 'asset7_5',
  assetChecks: LiveDataForNodeMaterializedWithChecks.assetChecks.filter(
    (c) =>
      c.executionForLatestMaterialization?.status === AssetCheckExecutionResolvedStatus.SUCCEEDED,
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
  freshnessInfo: buildAssetFreshnessInfo({
    currentMinutesLate: 12,
  }),
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
  freshnessInfo: buildAssetFreshnessInfo({
    currentMinutesLate: 0,
  }),
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
  freshnessInfo: buildAssetFreshnessInfo({
    currentMinutesLate: 0,
  }),
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
  freshnessInfo: buildAssetFreshnessInfo({
    currentMinutesLate: 12,
  }),
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
  lastObservation: buildObservationEvent({
    runId: 'ABCDEF',
    stepKey: 'asset1',
    timestamp: TIMESTAMP,
  }),
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
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    stepKey: 'asset1',
    timestamp: TIMESTAMP,
  }),
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
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    stepKey: 'asset1',
    timestamp: TIMESTAMP,
  }),
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
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    stepKey: 'asset1',
    timestamp: TIMESTAMP,
  }),
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
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    stepKey: 'asset1',
    timestamp: TIMESTAMP,
  }),
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
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    stepKey: 'asset1',
    timestamp: TIMESTAMP,
  }),
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: buildAssetFreshnessInfo({
    currentMinutesLate: 12,
  }),
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
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    stepKey: 'asset1',
    timestamp: TIMESTAMP,
  }),
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.FRESH,
  staleCauses: [],
  assetChecks: [],
  freshnessInfo: buildAssetFreshnessInfo({
    currentMinutesLate: 0,
  }),
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
    healthData: undefined,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Unknown'],
  },

  {
    title: 'Run Started - Not Executing Yet',
    liveData: LiveDataForNodeRunStartedNotMaterializing,
    healthData: HealthDataHealthy,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Executing...', 'ABCDEF'],
  },
  {
    title: 'Run Started - Executing',
    liveData: LiveDataForNodeRunStartedMaterializing,
    healthData: HealthDataHealthy,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Executing...', 'ABCDEF'],
  },

  {
    title: 'Run Failed to Execute',
    liveData: LiveDataForNodeRunFailed,
    healthData: HealthDataDegraded,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Degraded'],
  },

  {
    title: 'Never Executed',
    liveData: LiveDataForNodeNeverMaterialized,
    healthData: HealthDataUnknown,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Not evaluated', 'Unknown'],
  },

  {
    title: 'Never Executed, Failed Check',
    liveData: {
      ...LiveDataForNodeNeverMaterialized,
      assetChecks: LiveDataForNodeMaterializedWithChecks.assetChecks,
    },
    healthData: HealthDataWithFailedChecks,
    definition: AssetNodeFragmentBasic,
    expectedText: ['1 / 5 Passed', 'Degraded'],
  },

  {
    title: 'Executed',
    liveData: LiveDataForNodeMaterialized,
    healthData: HealthDataHealthy,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Healthy', 'Passing'],
  },

  {
    title: 'Executed and Stale',
    liveData: LiveDataForNodeMaterializedAndStale,
    healthData: HealthDataHealthy,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Unsynced', 'Healthy', 'Passing'],
  },

  {
    title: 'Executed and Stale and Overdue',
    liveData: LiveDataForNodeMaterializedAndStaleAndOverdue,
    healthData: HealthDataOverdue,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Unsynced', 'Degraded', 'Failed'],
  },

  {
    title: 'Executed and Stale and Fresh',
    liveData: LiveDataForNodeMaterializedAndStaleAndFresh,
    healthData: HealthDataHealthy,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Unsynced', 'Healthy'],
  },

  {
    title: 'Executed and Fresh',
    liveData: LiveDataForNodeMaterializedAndFresh,
    healthData: HealthDataHealthy,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Healthy'],
  },

  {
    title: 'Executed and Overdue',
    liveData: LiveDataForNodeMaterializedAndOverdue,
    healthData: HealthDataOverdue,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Degraded', 'Failed'],
  },
  {
    title: 'Executed and Failed and Overdue',
    liveData: LiveDataForNodeFailedAndOverdue,
    healthData: HealthDataOverdue,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Failed', 'Degraded'],
  },
  {
    title: 'Executed with Checks (Ok)',
    liveData: LiveDataForNodeMaterializedWithChecksOk,
    healthData: HealthDataHealthy,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Passing', 'Healthy', '1 / 1 Passed'],
  },
  {
    title: 'Executed with Checks (Failed)',
    liveData: LiveDataForNodeMaterializedWithChecks,
    healthData: HealthDataWithFailedChecks,
    definition: AssetNodeFragmentBasic,
    expectedText: ['Passing', 'Degraded', '1 / 5 Passed'],
  },
  {
    title: 'Changed in Branch',
    liveData: LiveDataForNodeMaterializedWithChecks,
    healthData: HealthDataWithFailedChecks,
    definition: AssetNodeFragmentChangedInBranch,
    expectedText: ['New in branch'],
  },
  {
    title: 'Very long key',
    liveData: {
      ...LiveDataForNodeMaterialized,
      stepKey: 'very_long_asset_which_was_totally_reasonable_at_the_time',
    },
    healthData: HealthDataHealthy,
    definition: {
      ...AssetNodeFragmentBasic,
      assetKey: buildAssetKey({path: ['very_long_asset_which_was_totally_reasonable_at_the_time']}),
    },
    expectedText: [],
  },
  {
    title: 'Single owner - long team name',
    liveData: LiveDataForNodeMaterialized,
    healthData: HealthDataHealthy,
    definition: {
      ...AssetNodeFragmentBasic,
      assetKey: buildAssetKey({path: ['very_long_asset_which_was_totally_reasonable_at_the_time']}),
      owners: [
        buildTeamAssetOwner({
          team: 'Team Foobar Fizz Buzz Definitely Requires Truncation',
        }),
      ],
    },
    expectedText: [],
  },
  {
    title: 'Single owner - long user name',
    liveData: LiveDataForNodeMaterialized,
    healthData: HealthDataHealthy,
    definition: {
      ...AssetNodeFragmentBasic,
      assetKey: buildAssetKey({path: ['very_long_asset_which_was_totally_reasonable_at_the_time']}),
      owners: [
        buildUserAssetOwner({
          email: 'madeline.manning.mathison@boringcompany.com',
        }),
      ],
    },
    expectedText: [],
  },
];

export const AssetNodeScenariosSource = [
  {
    title: 'Source Asset - No Live Data',
    liveData: undefined,
    healthData: undefined,
    definition: AssetNodeFragmentSource,
    expectedText: ['Unknown'],
  },

  {
    title: 'Source Asset - Not Observable',
    liveData: LiveDataForNodeNeverMaterialized,
    healthData: HealthDataUnknown,
    definition: {
      ...AssetNodeFragmentSource,
      isObservable: false,
      isExecutable: false,
      id: '["source_asset_no"]',
      assetKey: buildAssetKey({path: ['source_asset_no']}),
    },
    expectedText: [],
  },

  {
    title: 'Source Asset - Not Observable, No Description',
    liveData: LiveDataForNodeNeverMaterialized,
    healthData: HealthDataUnknown,
    definition: {
      ...AssetNodeFragmentSource,
      isObservable: false,
      isExecutable: false,
      description: null,
      id: '["source_asset_nono"]',
      assetKey: buildAssetKey({path: ['source_asset_nono']}),
    },
    expectedText: [],
  },

  {
    title: 'Source Asset - Never Observed',
    liveData: LiveDataForNodeSourceNeverObserved,
    healthData: HealthDataUnknown,
    definition: AssetNodeFragmentSource,
    expectedText: ['Unknown'],
  },

  {
    title: 'Source Asset - Overdue',
    liveData: LiveDataForNodeMaterializedAndOverdue,
    healthData: HealthDataOverdue,
    definition: AssetNodeFragmentSourceOverdue,
    expectedText: ['Degraded'],
  },
  {
    title: 'Source Asset - Observation Running',
    liveData: LiveDataForNodeSourceObservationRunning,
    healthData: HealthDataHealthy,
    definition: AssetNodeFragmentSource,
    expectedText: ['Executing...', 'ABCDEF'],
  },

  {
    title: 'Source Asset - Observed, Up To Date',
    liveData: LiveDataForNodeSourceObservedUpToDate,
    healthData: HealthDataHealthy,
    definition: AssetNodeFragmentSource,
    expectedText: ['Healthy'],
  },
];

export const AssetNodeScenariosPartitioned = [
  {
    title: 'Partitioned Asset - Some Missing',
    liveData: LiveDataForNodePartitionedSomeMissing,
    healthData: HealthDataPartitionedDegraded,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['0% filled'],
  },

  {
    title: 'Partitioned Asset - Some Failed',
    liveData: LiveDataForNodePartitionedSomeFailed,
    healthData: HealthDataPartitionedDegraded,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['849 failed'],
  },

  {
    title: 'Partitioned Asset - None Missing',
    liveData: LiveDataForNodePartitionedNoneMissing,
    healthData: HealthDataPartitionedHealthy,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['Healthy'],
  },

  {
    title: 'Never Executed',
    liveData: LiveDataForNodePartitionedNeverMaterialized,
    healthData: HealthDataUnknown,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['0% filled', 'Unknown'],
  },

  {
    title: 'Executing...',
    liveData: LiveDataForNodePartitionedMaterializing,
    healthData: HealthDataHealthy,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['Executing 5 partitions'],
  },

  {
    title: 'Partitioned Asset - Overdue',
    liveData: LiveDataForNodePartitionedOverdue,
    healthData: HealthDataOverdue,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['100% filled', 'Failed', 'Degraded'],
  },

  {
    title: 'Partitioned Asset - Fresh',
    liveData: LiveDataForNodePartitionedFresh,
    healthData: HealthDataPartitionedHealthy,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['100% filled', 'Passing'],
  },

  {
    title: 'Partitioned Asset - Checks and Tags',
    liveData: {
      ...LiveDataForNodePartitionedFresh,
      assetChecks: LiveDataForNodeMaterializedWithChecks.assetChecks,
    },
    healthData: HealthDataWithFailedChecks,
    definition: {
      ...AssetNodeFragmentPartitioned,
      changedReasons: [ChangeReason.NEW],
      kinds: ['ipynb'],
    },
    expectedText: ['100% filled', 'ipynb'],
  },

  {
    title: 'Partitioned Asset - Last Run Failed',
    liveData: LiveDataForNodePartitionedLatestRunFailed,
    healthData: HealthDataDegraded,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['100% filled', '1 failed', 'Degraded'],
  },

  {
    title: 'Partitioned Asset - Live Data Loading',
    liveData: undefined,
    healthData: undefined,
    definition: AssetNodeFragmentPartitioned,
    expectedText: ['Unknown'],
  },
];
