import {useQueryPersistedState} from 'src/hooks/useQueryPersistedState';
import {DefaultLogLevels, LogLevel} from 'src/runs/LogLevel';
import {LogFilter} from 'src/runs/LogsProvider';
import {getRunFilterProviders} from 'src/runs/getRunFilterProviders';
import {tokenizedValueFromString} from 'src/ui/TokenizingField';

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
  hideNonMatches: 'false',
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
 */
export const decodeRunPageFilters = (qs: {[key: string]: string}) => {
  const logValues = qs['logs'].split(DELIMITER);
  const focusedTime = qs['timestamp'] ? Number(qs['timestamp']) : null;
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

export function useQueryPersistedLogFilter() {
  return useQueryPersistedState<LogFilter>({
    encode: encodeRunPageFilters,
    decode: decodeRunPageFilters,
    defaults: DefaultQuerystring,
  });
}
