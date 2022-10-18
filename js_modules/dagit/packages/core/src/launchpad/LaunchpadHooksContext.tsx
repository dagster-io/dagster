import React from 'react';

import {LaunchRootExecutionButton} from './LaunchRootExecutionButton';

type LaunchpadHooksContextValue = {
  LaunchRootExecutionButton?: typeof LaunchRootExecutionButton;
};

export const LaunchpadHooksContext = React.createContext<LaunchpadHooksContextValue>({
  LaunchRootExecutionButton: undefined,
});

export function useLaunchPadHooks(): {
  LaunchRootExecutionButton: typeof LaunchRootExecutionButton;
} {
  const {LaunchRootExecutionButton: overrideLaunchRootExecutionButton} = React.useContext(
    LaunchpadHooksContext,
  );

  return {
    LaunchRootExecutionButton: overrideLaunchRootExecutionButton ?? LaunchRootExecutionButton,
  };
}
