import * as React from 'react';

import {SplitPanelContainer} from 'src/SplitPanelContainer';
import {LoadingOverlay} from 'src/execute/LoadingOverlay';
import {SessionSettingsBar} from 'src/execute/SessionSettingsBar';

const LOADING_PIPELINE = `Loading pipeline and partition sets...`;

export const ExecutionSessionContainerLoading = () => (
  <SplitPanelContainer
    axis={'vertical'}
    identifier={'execution'}
    firstInitialPercent={75}
    firstMinSize={100}
    first={
      <>
        <LoadingOverlay isLoading message={LOADING_PIPELINE} />
        <SessionSettingsBar />
      </>
    }
    second={<LoadingOverlay isLoading message={'Loading pipeline and partition sets...'} />}
  />
);
