import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';

import {SessionSettingsBar} from 'src/execute/SessionSettingsBar';
import {Spinner} from 'src/ui/Spinner';
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
          <Spinner purpose="section" />
        </SessionSettingsBar>
        <NonIdealState {...props} />
      </>
    }
    second={<div />}
  />
);
