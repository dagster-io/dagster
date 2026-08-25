import React from 'react';

type FeatureContext = {
  canSeeMaterializeAction: boolean;
  canSeeWipeMaterializationAction: boolean;
  canSeeToggleScheduleAction: boolean;
  canSeeToggleSensorAction: boolean;
  canSeeExecuteChecksAction: boolean;
  canSeeBackfillCoordinatorLogs: boolean;
  // Whether deleting dynamic partitions can also wipe their materializations. Requires
  // event log storage support for partitioned wipes, which OSS storages do not have.
  canWipeOnDeleteDynamicPartitions: boolean;
};

export const CloudOSSContext = React.createContext<{
  isBranchDeployment: boolean;
  featureContext: FeatureContext;
}>({
  isBranchDeployment: false,
  featureContext: {
    canSeeMaterializeAction: true,
    canSeeToggleScheduleAction: true,
    canSeeToggleSensorAction: true,
    canSeeWipeMaterializationAction: true,
    canSeeExecuteChecksAction: true,
    canSeeBackfillCoordinatorLogs: false,
    canWipeOnDeleteDynamicPartitions: false,
  },
});
