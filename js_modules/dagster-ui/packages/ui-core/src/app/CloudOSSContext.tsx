import React from 'react';

import {SearchResult} from '../search/types';

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
  useAugmentSearchResults: () => (
    results: SearchResult[],
    searchContext: 'catalog' | 'global',
  ) => SearchResult[];
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
  useAugmentSearchResults: () => (results) => results,
});
