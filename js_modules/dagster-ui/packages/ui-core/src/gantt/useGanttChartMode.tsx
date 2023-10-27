import {useStateWithStorage} from '../hooks/useStateWithStorage';

import {GanttChartMode} from './Constants';

const GANTT_CHART_MODE_KEY = 'GanttChartModePreference';

const validateSavedMode = (storedValue: string) =>
  storedValue === GanttChartMode.FLAT ||
  storedValue === GanttChartMode.WATERFALL ||
  storedValue === GanttChartMode.WATERFALL_TIMED
    ? storedValue
    : GanttChartMode.WATERFALL_TIMED;

export const useGanttChartMode = () => {
  return useStateWithStorage(GANTT_CHART_MODE_KEY, validateSavedMode);
};
