import React from 'react';

import {SearchResult} from '../search/types';

type FeatureContext = {
  canSeeMaterializeAction: boolean;
  canSeeWipeMaterializationAction: boolean;
  canSeeToggleScheduleAction: boolean;
  canSeeToggleSensorAction: boolean;
  canSeeExecuteChecksAction: boolean;
};

export const CloudOSSContext = React.createContext<{
  isBranchDeployment: boolean;
  featureContext: FeatureContext;
  onViewChange: (view: {path: string}) => void;
  useAugmentSearchResults: () => (results: SearchResult[]) => SearchResult[];
}>({
  isBranchDeployment: false,
  featureContext: {
    canSeeMaterializeAction: true,
    canSeeToggleScheduleAction: true,
    canSeeToggleSensorAction: true,
    canSeeWipeMaterializationAction: true,
    canSeeExecuteChecksAction: true,
  },
  onViewChange: () => {},
  useAugmentSearchResults: () => (results) => results,
});
