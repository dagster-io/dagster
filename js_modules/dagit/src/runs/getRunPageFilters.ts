import {tokenizedValueFromString} from 'src/TokenizingField';
import {DefaultLogLevels, LogLevel} from 'src/runs/LogLevel';
import {LogFilter} from 'src/runs/LogsProvider';
import {getRunFilterProviders} from 'src/runs/getRunFilterProviders';

/**
 * Query parameter structure, all optional:
 *
 * `steps`
 *   - string (selection syntax)
 *   - Initializes step selection in Gaant chart
 * `logs`
 *   - string (comma-separated foo:bar tokens or free text)
 *   - Initializes log filter input
 * `levels`
 *   - string (comma-separated values)
 *   - Initializes levels in log filter
 */
export const getRunPageFilters = (searchValue: string) => {
  const params = new URLSearchParams(searchValue);

  const stepQuery = params.get('steps') || '*';
  const logValues = params.getAll('logs') || [];
  const providers = getRunFilterProviders();
  const logQuery = logValues.map((token) => tokenizedValueFromString(token, providers));

  const levelsValues = params.getAll('levels');
  const levelsArr = levelsValues.length ? levelsValues : DefaultLogLevels;
  const levels = levelsArr
    .map((level) => level.toUpperCase())
    .filter((level) => LogLevel.hasOwnProperty(level))
    .reduce((accum, level) => ({...accum, [level]: true}), {});

  return {
    since: 0,
    stepQuery,
    logQuery,
    levels,
  } as LogFilter;
};
