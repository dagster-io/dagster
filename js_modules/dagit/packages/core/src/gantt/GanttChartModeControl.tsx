import * as React from 'react';

import {ButtonGroup, ButtonGroupItem} from '../ui/ButtonGroup';

import {GanttChartMode} from './Constants';

export const GanttChartModeControl: React.FunctionComponent<{
  value: GanttChartMode;
  hideTimedMode: boolean;
  onChange: (mode: GanttChartMode) => void;
}> = React.memo(({value, onChange, hideTimedMode}) => {
  const buttons: ButtonGroupItem<GanttChartMode>[] = [
    {id: GanttChartMode.FLAT, icon: 'drag_handle'},
    {id: GanttChartMode.WATERFALL, icon: 'waterfall_chart'},
  ];

  if (!hideTimedMode) {
    buttons.push({id: GanttChartMode.WATERFALL_TIMED, icon: 'timer'});
  }

  const activeItems = React.useMemo(() => new Set([value]), [value]);
  const onClick = React.useCallback((id: GanttChartMode) => onChange(id), [onChange]);

  return <ButtonGroup activeItems={activeItems} buttons={buttons} onClick={onClick} />;
});
