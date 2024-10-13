import {
  NonIdealState,
  NonIdealStateProps,
  Spinner,
  SplitPanelContainer,
} from '@dagster-io/ui-components';

import {SessionSettingsBar} from './SessionSettingsBar';

export const LaunchpadSessionError = (props: NonIdealStateProps) => (
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
