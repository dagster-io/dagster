import * as React from 'react';

import {SplitPanelContainer} from '../ui/SplitPanelContainer';

import {LoadingOverlay} from './LoadingOverlay';
import {SessionSettingsBar} from './SessionSettingsBar';

const LOADING_PIPELINE = `Loading pipeline and partition sets...`;

export const LaunchpadSessionLoading = () => (
  <SplitPanelContainer
    axis="vertical"
    identifier="execution"
    firstInitialPercent={75}
    firstMinSize={100}
    first={
      <>
        <LoadingOverlay isLoading message={LOADING_PIPELINE} />
        <SessionSettingsBar />
      </>
    }
    second={<LoadingOverlay isLoading message="Loading pipeline and partition sets..." />}
  />
);
