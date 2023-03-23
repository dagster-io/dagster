import {tokenizedValueFromString} from '@dagster-io/ui';
import * as React from 'react';

import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

import {DefaultLogLevels, LogLevel} from './LogLevel';
import {LogFilter} from './LogsProvider';
import {getRunFilterProviders} from './getRunFilterProviders';

const DELIMITER = '|';

function levelsToQuery(levels: string[]): string {
  return levels
    .sort()
    .map((key) => key.toLowerCase())
    .join(DELIMITER);
}

export const DefaultQuerystring: {[key: string]: string} = {
  steps: '*',
  logs: '',
  levels: levelsToQuery(DefaultLogLevels),
  hideNonMatches: 'true',
  focusedTime: '',
};

/**
 * Query parameter structure, all optional:
 *
 * `steps`
 *   - string (selection syntax)
 *   - Initializes step selection in Gantt chart
 * `logs`
 *   - string (comma-separated foo:bar tokens or free text)
 *   - Initializes log filter input
 * `levels`
 *   - string (comma-separated values)
 *   - Initializes levels in log filter
 * `focusedTime`
 *   - string (unix timestamp with msec)
 *   - Scrolls directly to log with specified time, if no `logs` filter
 */
export const decodeRunPageFilters = (qs: {[key: string]: string}) => {
  const logValues = qs['logs'].split(DELIMITER);
  const focusedTime = qs['focusedTime'] && !qs['logs'] ? Number(qs['focusedTime']) : null;
  const hideNonMatches = qs['hideNonMatches'] === 'true' ? true : false;

  const providers = getRunFilterProviders();
  const logQuery = logValues.map((token) => tokenizedValueFromString(token, providers));

  const levelsValues = qs['levels'].split(DELIMITER);

  return {
    sinceTime: 0,
    focusedTime,
    hideNonMatches,
    logQuery,
    levels: levelsValues
      .map((level) => level.toUpperCase())
      .filter((level) => LogLevel.hasOwnProperty(level))
      .reduce((accum, level) => ({...accum, [level]: true}), {}),
  } as LogFilter;
};

export function encodeRunPageFilters(filter: LogFilter) {
  const logQueryTokenStrings = filter.logQuery.map((v) =>
    v.token ? `${v.token}:${v.value}` : v.value,
  );

  return {
    hideNonMatches: filter.hideNonMatches ? 'true' : 'false',
    focusedTime: filter.focusedTime || '',
    logs: logQueryTokenStrings.join(DELIMITER),
    levels: levelsToQuery(Object.keys(filter.levels).filter((key) => !!filter.levels[key])),
  };
}

export const EnabledRunLogLevelsKey = 'EnabledRunLogLevels';

export const validateLogLevels = (json: any) => {
  if (json === undefined || !Array.isArray(json)) {
    return null;
  }

  const validLevels = new Set(Object.keys(LogLevel));
  return json.filter((level) => validLevels.has(level));
};

export function useQueryPersistedLogFilter(): [LogFilter, (updates: LogFilter) => void] {
  // We only read the stored log levels here as defaults, but we do not set them. This is
  // because we don't want to update the persisted value unless the user interacts with the
  // LogFilterSelect component. Navigating to a page with levels set in the URL querystring
  // should *not* implicitly update the persisted values.
  const [storedLogLevels] = useStateWithStorage(EnabledRunLogLevelsKey, validateLogLevels);

  const defaults = React.useMemo(() => {
    const levels = storedLogLevels ?? DefaultLogLevels;
    return {...DefaultQuerystring, levels: levelsToQuery(levels)};
  }, [storedLogLevels]);

  return useQueryPersistedState<LogFilter>({
    encode: encodeRunPageFilters,
    decode: decodeRunPageFilters,
    defaults,
  });
}
