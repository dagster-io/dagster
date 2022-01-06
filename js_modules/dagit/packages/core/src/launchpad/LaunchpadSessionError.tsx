import * as React from 'react';

import {NonIdealState, NonIdealStateProps} from '../ui/NonIdealState';
import {Spinner} from '../ui/Spinner';
import {SplitPanelContainer} from '../ui/SplitPanelContainer';

import {SessionSettingsBar} from './SessionSettingsBar';

export const LaunchpadSessionError: React.FC<NonIdealStateProps> = (props) => (
  <SplitPanelContainer
    axis="vertical"
    identifier="execution"
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
