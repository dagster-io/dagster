import React from 'react';

import {LaunchRootExecutionButton, useLaunchWithTelemetry} from './LaunchRootExecutionButton';

type LaunchpadHooksContextValue = {
  LaunchRootExecutionButton?: typeof LaunchRootExecutionButton;
  useLaunchWithTelemetry?: typeof useLaunchWithTelemetry;
};

export const LaunchpadHooksContext = React.createContext<LaunchpadHooksContextValue>({
  LaunchRootExecutionButton: undefined,
  useLaunchWithTelemetry: undefined,
});

export function useLaunchPadHooks() {
  const {LaunchRootExecutionButton: overrideLaunchRootExecutionButton} = React.useContext(
    LaunchpadHooksContext,
  );

  const {useLaunchWithTelemetry: overrideUseLaunchWithTelemetry} = React.useContext(
    LaunchpadHooksContext,
  );

  return {
    LaunchRootExecutionButton: overrideLaunchRootExecutionButton ?? LaunchRootExecutionButton,
    useLaunchWithTelemetry: overrideUseLaunchWithTelemetry ?? useLaunchWithTelemetry,
  };
}
