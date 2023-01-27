import {RunStatus} from '../graphql/types';

import {LiveDataForNode} from './Utils';
import {AssetNodeFragment} from './types/AssetNode.types';

export const AssetNodeFragmentBasic: AssetNodeFragment = {
  __typename: 'AssetNode',
  assetKey: {__typename: 'AssetKey', path: ['asset1']},
  computeKind: null,
  description: 'This is a test asset description',
  graphName: null,
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
  currentLogicalVersion: null,
  projectedLogicalVersion: null,
  freshnessInfo: null,
  freshnessPolicy: null,
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
  currentLogicalVersion: null,
  projectedLogicalVersion: null,
  freshnessInfo: null,
  freshnessPolicy: null,
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
  currentLogicalVersion: null,
  projectedLogicalVersion: null,
  freshnessInfo: null,
  freshnessPolicy: null,
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
  currentLogicalVersion: 'INITIAL',
  projectedLogicalVersion: 'V_A',
  freshnessInfo: null,
  freshnessPolicy: null,
  partitionStats: null,
};

export const LiveDataForNodeMaterialized: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: `${Date.now()}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'INITIAL',
  projectedLogicalVersion: 'V_A',
  freshnessInfo: null,
  freshnessPolicy: null,
  partitionStats: null,
};

export const LiveDataForNodeMaterializedAndStale: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: `${Date.now()}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'V_A',
  projectedLogicalVersion: 'V_B',
  freshnessInfo: null,
  freshnessPolicy: null,
  partitionStats: null,
};

export const LiveDataForNodeMaterializedAndStaleAndLate: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: `${Date.now()}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'V_A',
  projectedLogicalVersion: 'V_B',
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 12,
  },
  freshnessPolicy: {
    __typename: 'FreshnessPolicy',
    maximumLagMinutes: 10,
    cronSchedule: null,
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
    timestamp: `${Date.now()}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'V_A',
  projectedLogicalVersion: 'V_B',
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 0,
  },
  freshnessPolicy: {
    __typename: 'FreshnessPolicy',
    maximumLagMinutes: 10,
    cronSchedule: null,
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
    timestamp: `${Date.now()}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'V_B',
  projectedLogicalVersion: 'V_B',
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 0,
  },
  freshnessPolicy: {
    __typename: 'FreshnessPolicy',
    maximumLagMinutes: 10,
    cronSchedule: null,
  },
  partitionStats: null,
};

export const LiveDataForNodeMaterializedAndLate: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: `${Date.now()}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'V_A',
  projectedLogicalVersion: 'V_A',
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 12,
  },
  freshnessPolicy: {
    __typename: 'FreshnessPolicy',
    maximumLagMinutes: 10,
    cronSchedule: null,
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
  currentLogicalVersion: 'INITIAL',
  projectedLogicalVersion: null,
  freshnessInfo: null,
  freshnessPolicy: null,
  partitionStats: null,
};

export const LiveDataForNodeSourceObservationRunning: LiveDataForNode = {
  stepKey: 'source_asset',
  unstartedRunIds: [],
  inProgressRunIds: ['12345'],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'INITIAL',
  projectedLogicalVersion: null,
  freshnessInfo: null,
  freshnessPolicy: null,
  partitionStats: null,
};

export const LiveDataForNodeSourceObservedStale: LiveDataForNode = {
  stepKey: 'source_asset',
  unstartedRunIds: [],
  inProgressRunIds: ['12345'],
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: {
    __typename: 'ObservationEvent',
    runId: 'ABCDEF',
    timestamp: `${Date.now()}`,
  },
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'INITIAL',
  projectedLogicalVersion: 'DIFFERENT',
  freshnessInfo: null,
  freshnessPolicy: null,
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
    timestamp: `${Date.now()}`,
  },
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'DIFFERENT',
  projectedLogicalVersion: 'DIFFERENT',
  freshnessInfo: null,
  freshnessPolicy: null,
  partitionStats: null,
};

export const LiveDataForNodePartitionedSomeMissing: LiveDataForNode = {
  stepKey: 'partitioned_asset',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: `${Date.now()}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'DIFFERENT',
  projectedLogicalVersion: 'DIFFERENT',
  freshnessInfo: null,
  freshnessPolicy: null,
  partitionStats: {
    numMaterialized: 5,
    numPartitions: 1500,
  },
};

export const LiveDataForNodePartitionedNoneMissing: LiveDataForNode = {
  stepKey: 'partitioned_asset',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: `${Date.now()}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'DIFFERENT',
  projectedLogicalVersion: 'DIFFERENT',
  freshnessInfo: null,
  freshnessPolicy: null,
  partitionStats: {
    numMaterialized: 1500,
    numPartitions: 1500,
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
  currentLogicalVersion: 'INITIAL',
  projectedLogicalVersion: 'V_A',
  freshnessInfo: null,
  freshnessPolicy: null,
  partitionStats: {
    numMaterialized: 0,
    numPartitions: 1500,
  },
};

export const LiveDataForNodePartitionedStale: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: `${Date.now()}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'V_A',
  projectedLogicalVersion: 'V_B',
  freshnessInfo: null,
  freshnessPolicy: null,
  partitionStats: {
    numMaterialized: 1500,
    numPartitions: 1500,
  },
};

export const LiveDataForNodePartitionedStaleAndLate: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: `${Date.now()}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'V_A',
  projectedLogicalVersion: 'V_B',
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 12,
  },
  freshnessPolicy: {
    __typename: 'FreshnessPolicy',
    maximumLagMinutes: 10,
    cronSchedule: null,
  },
  partitionStats: {
    numMaterialized: 1500,
    numPartitions: 1500,
  },
};

export const LiveDataForNodePartitionedStaleAndFresh: LiveDataForNode = {
  stepKey: 'asset1',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    timestamp: `${Date.now()}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  currentLogicalVersion: 'V_A',
  projectedLogicalVersion: 'V_B',
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 0,
  },
  freshnessPolicy: {
    __typename: 'FreshnessPolicy',
    maximumLagMinutes: 10,
    cronSchedule: null,
  },
  partitionStats: {
    numMaterialized: 1500,
    numPartitions: 1500,
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
  currentLogicalVersion: null,
  projectedLogicalVersion: null,
  freshnessInfo: null,
  freshnessPolicy: null,
  partitionStats: {
    numMaterialized: 1500,
    numPartitions: 1500,
  },
};
