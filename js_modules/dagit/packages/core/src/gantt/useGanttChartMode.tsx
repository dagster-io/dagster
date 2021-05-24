import * as React from 'react';

import {GanttChartMode} from './Constants';

const GANTT_CHART_MODE_KEY = 'GanttChartModePreference';

type Output = [GanttChartMode, (update: GanttChartMode) => void];

export const useGanttChartMode = () => {
  const [mode, setMode] = React.useState<GanttChartMode>(() => {
    const storedValue = window.localStorage.getItem(GANTT_CHART_MODE_KEY);
    if (
      storedValue === GanttChartMode.FLAT ||
      storedValue === GanttChartMode.WATERFALL ||
      storedValue === GanttChartMode.WATERFALL_TIMED
    ) {
      return storedValue;
    }
    return GanttChartMode.WATERFALL_TIMED;
  });

  const onChange = React.useCallback((update: GanttChartMode) => {
    window.localStorage.setItem(GANTT_CHART_MODE_KEY, update);
    setMode(update);
  }, []);

  return React.useMemo(() => [mode, onChange], [mode, onChange]) as Output;
};
