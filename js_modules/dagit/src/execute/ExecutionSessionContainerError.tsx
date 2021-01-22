import {NonIdealState, Spinner} from '@blueprintjs/core';
import * as React from 'react';

import {SessionSettingsBar} from 'src/execute/SessionSettingsBar';
import {SplitPanelContainer} from 'src/ui/SplitPanelContainer';

export const ExecutionSessionContainerError: React.FC<NonIdealState['props']> = (props) => (
  <SplitPanelContainer
    axis={'vertical'}
    identifier={'execution'}
    firstInitialPercent={75}
    firstMinSize={100}
    first={
      <>
        <SessionSettingsBar>
          <Spinner size={20} />
        </SessionSettingsBar>
        <NonIdealState {...props} />
      </>
    }
    second={<div />}
  />
);
