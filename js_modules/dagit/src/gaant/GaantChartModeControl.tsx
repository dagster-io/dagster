import * as React from 'react';
import {GaantChartMode} from './Constants';
import {ButtonGroup, Button} from '@blueprintjs/core';

export const GaantChartModeControl: React.FunctionComponent<{
  value: GaantChartMode;
  hideTimedMode: boolean;
  onChange: (mode: GaantChartMode) => void;
}> = React.memo(({value, onChange, hideTimedMode}) => (
  <ButtonGroup style={{flexShrink: 0}}>
    <Button
      key={GaantChartMode.FLAT}
      small={true}
      icon="column-layout"
      title={'Flat'}
      active={value === GaantChartMode.FLAT}
      onClick={() => onChange(GaantChartMode.FLAT)}
    />
    <Button
      key={GaantChartMode.WATERFALL}
      small={true}
      icon="gantt-chart"
      title={'Waterfall'}
      active={value === GaantChartMode.WATERFALL}
      onClick={() => onChange(GaantChartMode.WATERFALL)}
    />
    {!hideTimedMode && (
      <Button
        key={GaantChartMode.WATERFALL_TIMED}
        small={true}
        icon="time"
        rightIcon="gantt-chart"
        title={'Waterfall with Execution Timing'}
        active={value === GaantChartMode.WATERFALL_TIMED}
        onClick={() => onChange(GaantChartMode.WATERFALL_TIMED)}
      />
    )}
  </ButtonGroup>
));
