import {Button, ButtonGroup} from '@blueprintjs/core';
import * as React from 'react';

import {GanttChartMode} from './Constants';

export const GanttChartModeControl: React.FunctionComponent<{
  value: GanttChartMode;
  hideTimedMode: boolean;
  onChange: (mode: GanttChartMode) => void;
}> = React.memo(({value, onChange, hideTimedMode}) => (
  <ButtonGroup style={{flexShrink: 0}}>
    <Button
      key={GanttChartMode.FLAT}
      small={true}
      icon="column-layout"
      title={'Flat'}
      active={value === GanttChartMode.FLAT}
      onClick={() => onChange(GanttChartMode.FLAT)}
    />
    <Button
      key={GanttChartMode.WATERFALL}
      small={true}
      icon="gantt-chart"
      title={'Waterfall'}
      active={value === GanttChartMode.WATERFALL}
      onClick={() => onChange(GanttChartMode.WATERFALL)}
    />
    {!hideTimedMode && (
      <Button
        key={GanttChartMode.WATERFALL_TIMED}
        small={true}
        icon="time"
        rightIcon="gantt-chart"
        title={'Waterfall with Execution Timing'}
        active={value === GanttChartMode.WATERFALL_TIMED}
        onClick={() => onChange(GanttChartMode.WATERFALL_TIMED)}
      />
    )}
  </ButtonGroup>
));
