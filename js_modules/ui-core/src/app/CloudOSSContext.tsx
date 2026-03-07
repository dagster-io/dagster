import React from 'react';

type FeatureContext = {
  canSeeMaterializeAction: boolean;
  canSeeWipeMaterializationAction: boolean;
  canSeeToggleScheduleAction: boolean;
  canSeeToggleSensorAction: boolean;
  canSeeExecuteChecksAction: boolean;
  canSeeBackfillCoordinatorLogs: boolean;
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
  },
});
