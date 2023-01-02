import {Button} from '@dagster-io/ui';
import React from 'react';

import {PythonErrorFragment_errorChain} from '../app/types/PythonErrorFragment';

import {LaunchRootExecutionButton} from './LaunchRootExecutionButton';
import {useLaunchWithTelemetry} from './useLaunchWithTelemetry';

type LaunchpadHooksContextValue = {
  LaunchRootExecutionButton?: typeof LaunchRootExecutionButton;
  useLaunchWithTelemetry?: typeof useLaunchWithTelemetry;
  MaterializeButton?: typeof Button;
  MaybeMissingEnvVarError?: React.FC<{
    errorChain: PythonErrorFragment_errorChain[];
    message: string;
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
    MaybeMissingEnvVarError,
  } = React.useContext(LaunchpadHooksContext);

  return {
    LaunchRootExecutionButton: overrideLaunchRootExecutionButton ?? LaunchRootExecutionButton,
    useLaunchWithTelemetry: overrideUseLaunchWithTelemetry ?? useLaunchWithTelemetry,
    MaterializeButton: OverrideMaterializeButton ?? Button,
    MaybeMissingEnvVarError,
  };
}
