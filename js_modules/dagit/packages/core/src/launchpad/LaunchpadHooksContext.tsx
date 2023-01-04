import {Button} from '@dagster-io/ui';
import React from 'react';

import {GenericError} from '../app/PythonErrorInfo';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment';

import {LaunchRootExecutionButton} from './LaunchRootExecutionButton';
import {useLaunchWithTelemetry} from './useLaunchWithTelemetry';

type LaunchpadHooksContextValue = {
  LaunchRootExecutionButton?: typeof LaunchRootExecutionButton;
  useLaunchWithTelemetry?: typeof useLaunchWithTelemetry;
  MaterializeButton?: typeof Button;
  PythonErrorInfoHeader?: React.FC<{
    error: GenericError | PythonErrorFragment;
    fallback?: React.ReactNode;
  }>;
};

export const LaunchpadHooksContext = React.createContext<LaunchpadHooksContextValue>({
  LaunchRootExecutionButton: undefined,
  useLaunchWithTelemetry: undefined,
});

export function useLaunchPadHooks() {
  const {
    LaunchRootExecutionButton: overrideLaunchRootExecutionButton,
    useLaunchWithTelemetry: overrideUseLaunchWithTelemetry,
    MaterializeButton: OverrideMaterializeButton,
    PythonErrorInfoHeader,
  } = React.useContext(LaunchpadHooksContext);

  return {
    LaunchRootExecutionButton: overrideLaunchRootExecutionButton ?? LaunchRootExecutionButton,
    useLaunchWithTelemetry: overrideUseLaunchWithTelemetry ?? useLaunchWithTelemetry,
    MaterializeButton: OverrideMaterializeButton ?? Button,
    PythonErrorInfoHeader,
  };
}
