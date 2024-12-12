import {LogFilter, LogsProviderLogs} from './LogsProvider';
import {eventTypeToDisplayType} from './getRunFilterProviders';
import {logNodeLevel} from './logNodeLevel';
import {LogNode} from './types';
import {weakmapMemoize} from '../app/Util';
import {flattenOneLevel} from '../util/flattenOneLevel';

export function filterLogs(logs: LogsProviderLogs, filter: LogFilter, filterStepKeys: string[]) {
  const filteredNodes = flattenOneLevel(logs.allNodeChunks).filter((node) => {
    // These events are used to determine which assets a run will materialize and are not intended
    // to be displayed in the Dagster UI. Pagination is offset based, so we remove these logs client-side.
    if (
      node.__typename === 'AssetMaterializationPlannedEvent' ||
      node.__typename === 'AssetCheckEvaluationPlannedEvent'
    ) {
      return false;
    }
    const l = logNodeLevel(node);
    if (!filter.levels[l]) {
      return false;
    }
    if (filter.sinceTime && Number(node.timestamp) < filter.sinceTime) {
      return false;
    }
    return true;
  });

  const hasTextFilter = !!(filter.logQuery[0] && filter.logQuery[0].value !== '');

  const textMatchNodes = hasTextFilter
    ? filteredNodes.filter((node) => {
        const nodeTexts = [node.message.toLowerCase(), ...metadataEntryKeyValueStrings(node)];
        return (
          filter.logQuery.length > 0 &&
          filter.logQuery.every((f) => {
            if (f.token === 'query') {
              return node.stepKey && filterStepKeys.includes(node.stepKey);
            }
            if (f.token === 'step') {
              return node.stepKey && node.stepKey === f.value;
            }
            if (f.token === 'type') {
              return node.eventType && f.value === eventTypeToDisplayType(node.eventType);
            }
            const valueLower = f.value.toLowerCase();
            return nodeTexts.some((text) => text.toLowerCase().includes(valueLower));
          })
        );
      })
    : [];

  return {
    filteredNodes: hasTextFilter && filter.hideNonMatches ? textMatchNodes : filteredNodes,
    textMatchNodes,
  };
}

// Given an array of metadata entries, returns searchable text in the format:
// [`label1:value1`, ...], where "value1" is the top-level value(s) present in the
// metadata entry object converted to JSON. All of our metadata entry types contain
// different top-level keys, such as "intValue", "mdStr" and "tableSchema", and
// the searchable text is the value of these keys.
//
const metadataEntryKeyValueStrings = weakmapMemoize((node: LogNode) => {
  if (!('metadataEntries' in node)) {
    return [];
  }
  const s = node.metadataEntries.map(
    ({__typename, label, description: _description, ...rest}) =>
      `${label}:${Object.values(rest)
        .map((v) => (typeof v === 'string' ? v : JSON.stringify(v)))
        .join(' ')}`,
  );
  return s;
});
