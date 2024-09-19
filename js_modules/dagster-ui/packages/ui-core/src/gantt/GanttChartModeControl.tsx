import {ButtonGroup, ButtonGroupItem} from '@dagster-io/ui-components';
import {memo, useCallback, useMemo} from 'react';

import {GanttChartMode} from './Constants';

export const GanttChartModeControl = memo(
  ({
    value,
    onChange,
    hideTimedMode,
  }: {
    value: GanttChartMode;
    hideTimedMode: boolean;
    onChange: (mode: GanttChartMode) => void;
  }) => {
    const buttons: ButtonGroupItem<GanttChartMode>[] = [
      {id: GanttChartMode.FLAT, icon: 'gantt_flat', tooltip: 'Flat view'},
      {id: GanttChartMode.WATERFALL, icon: 'gantt_waterfall', tooltip: 'Waterfall view'},
    ];

    if (!hideTimedMode) {
      buttons.push({
        id: GanttChartMode.WATERFALL_TIMED,
        icon: 'timer',
        tooltip: 'Timed view',
      });
    }

    const activeItems = useMemo(() => new Set([value]), [value]);
    const onClick = useCallback((id: GanttChartMode) => onChange(id), [onChange]);

    return <ButtonGroup activeItems={activeItems} buttons={buttons} onClick={onClick} />;
  },
);
