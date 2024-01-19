import {Button} from '@dagster-io/ui-components';
import React from 'react';

import {LaunchRootExecutionButton} from './LaunchRootExecutionButton';
import {useLaunchWithTelemetry} from './useLaunchWithTelemetry';
import {GenericError} from '../app/PythonErrorInfo';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {UserDisplay} from '../runs/UserDisplay';
import {SetFilterValue} from '../ui/Filters/useStaticSetFilter';

type LaunchpadHooksContextValue = {
  LaunchRootExecutionButton?: typeof LaunchRootExecutionButton;
  useLaunchWithTelemetry?: typeof useLaunchWithTelemetry;
  UserDisplay?: typeof UserDisplay;
  MaterializeButton?: typeof Button;
  PythonErrorInfoHeader?: React.ComponentType<{
    error: GenericError | PythonErrorFragment;
    fallback?: React.ReactNode;
  }>;
  StaticFilterSorter?: Record<string, (a: SetFilterValue<any>, b: SetFilterValue<any>) => number>;
};

export const LaunchpadHooksContext = React.createContext<LaunchpadHooksContextValue>({
  LaunchRootExecutionButton: undefined,
  useLaunchWithTelemetry: undefined,
  StaticFilterSorter: undefined,
});

export function useLaunchPadHooks() {
  const {
    LaunchRootExecutionButton: overrideLaunchRootExecutionButton,
    useLaunchWithTelemetry: overrideUseLaunchWithTelemetry,
    MaterializeButton: OverrideMaterializeButton,
    UserDisplay: OverrideUserDisplay,
    PythonErrorInfoHeader,
    StaticFilterSorter,
  } = React.useContext(LaunchpadHooksContext);

  return {
    LaunchRootExecutionButton: overrideLaunchRootExecutionButton ?? LaunchRootExecutionButton,
    useLaunchWithTelemetry: overrideUseLaunchWithTelemetry ?? useLaunchWithTelemetry,
    MaterializeButton: OverrideMaterializeButton ?? Button,
    PythonErrorInfoHeader,
    UserDisplay: OverrideUserDisplay ?? UserDisplay,
    StaticFilterSorter,
  };
}
