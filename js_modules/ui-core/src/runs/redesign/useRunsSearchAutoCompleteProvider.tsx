import {IconName, MiddleTruncate} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {getTagPairAtCursor} from './getTagPairAtCursor';
import {
  RUNS_SEARCH_ATTRIBUTES,
  RUN_STATUSES,
  RunsSearchAttribute,
  TAG_KEY_BY_ATTRIBUTE,
  formatRunsSearchValue,
  getAttributeForTagKey,
  tagValueToCodeLocation,
} from './runsSearchAttributes';
import {COMMON_COLLATOR} from '../../app/Util';
import {isHiddenAssetGroupJob} from '../../asset-graph/Utils';
import {
  createSelectionAutoComplete,
  useSelectionAutoCompleteResults,
} from '../../selection/SelectionAutoComplete';
import {
  SelectionAutoCompleteProvider,
  Suggestion,
  SuggestionJSXBase,
  createProvider,
} from '../../selection/SelectionAutoCompleteProvider';
import {getUnquotedValueProblem} from '../../selection/SelectionInputUtil';
import {DagsterRepoOption, useRepositoryOptions} from '../../workspace/WorkspaceContext/util';
import {useLazyRunTagKeys, useLazyRunTagValues, useRunTagValues} from '../useRunTagQueries';

const ATTRIBUTE_ICONS = {
  id: 'id',
  status: 'status',
  job: 'job',
  code_location: 'code_location',
  sensor: 'sensors',
  schedule: 'schedule',
  user: 'account_circle',
  backfill: 'backfill',
  partition: 'partition',
  tag: 'tag',
  snapshot_id: 'snapshot',
} as const satisfies Record<RunsSearchAttribute, IconName>;

const ATTRIBUTE_LABELS = {
  id: 'Run ID',
  backfill: 'Backfill ID',
  snapshot_id: 'Snapshot ID',
} as const satisfies Partial<Record<RunsSearchAttribute, string>>;

type ValuesByAttribute = Record<Exclude<RunsSearchAttribute, 'tag'>, string[]>;

// The shared provider inserts an empty value as `<null>`, which the Runs search rejects.
const withoutEmptyValues = (values: string[]) => values.filter((value) => value !== '');

const getWorkspaceValues = (options: DagsterRepoOption[]) => {
  const jobs = options.flatMap(({repository}) =>
    repository.pipelines
      .filter((pipeline) => pipeline.isJob && !isHiddenAssetGroupJob(pipeline.name))
      .map((pipeline) => pipeline.name),
  );
  const codeLocations = options.flatMap(
    ({repository, repositoryLocation}) =>
      tagValueToCodeLocation(`${repository.name}@${repositoryLocation.name}`) ?? [],
  );

  return {
    jobs: [...new Set(jobs)].sort(COMMON_COLLATOR.compare),
    codeLocations: codeLocations.sort(COMMON_COLLATOR.compare),
  };
};

const createTagKeySuggestion = (key: string, textCallback?: (text: string) => string) => {
  const text = `${formatRunsSearchValue(key)}=`;
  return {
    text: textCallback ? textCallback(text) : text,
    jsx: <SuggestionJSXBase label={<MiddleTruncate text={key} />} />,
  };
};

type TagKeyResultsOptions = {
  tagKeys: string[];
  query: string;
  quoted: boolean;
  textCallback?: (text: string) => string;
};

/** Tag keys for the first half of a pair, or the typed key when none match. */
const getTagKeyResults = ({
  tagKeys,
  query,
  quoted,
  textCallback,
}: TagKeyResultsOptions): Suggestion[] => {
  const queryLower = query.toLowerCase();
  const matches = tagKeys.filter((key) => key.toLowerCase().includes(queryLower));

  if (query && !matches.length) {
    // Quoting an unquoted key with a problem would change the key or still not parse.
    if (!quoted && getUnquotedValueProblem(query)) {
      return [];
    }
    return [createTagKeySuggestion(query, textCallback)];
  }

  // Uncapped, like the legacy filter, so system keys can't crowd out the rest.
  return matches.map((key) => createTagKeySuggestion(key, textCallback));
};

type RunsSearchHintOptions = {
  valuesByAttribute: ValuesByAttribute;
  /** The key of the tag pair whose value the cursor is in, if any. */
  valueKey: string | null;
  tagValues: string[];
  tagKeys: string[];
  keyQuoted: boolean;
};

const createRunsSearchHint = ({
  valuesByAttribute,
  valueKey,
  tagValues,
  tagKeys,
  keyQuoted,
}: RunsSearchHintOptions) => {
  const tagPairs = valueKey ? tagValues.map((value) => ({key: valueKey, value})) : [];
  const provider = createProvider({
    attributesMap: Object.fromEntries(
      RUNS_SEARCH_ATTRIBUTES.map((attribute) => [
        attribute,
        attribute === 'tag' ? tagPairs : valuesByAttribute[attribute],
      ]),
    ),
    attributeToIcon: ATTRIBUTE_ICONS,
    attributeToLabel: ATTRIBUTE_LABELS,
    functions: [],
    formatValue: formatRunsSearchValue,
  });

  return createSelectionAutoComplete({
    ...provider,
    getAttributeValueResultsMatchingQuery: (props) =>
      props.attribute === 'tag' && props.key === undefined
        ? getTagKeyResults({
            tagKeys,
            query: props.query,
            quoted: keyQuoted,
            textCallback: props.textCallback,
          })
        : provider.getAttributeValueResultsMatchingQuery(props),
    supportsTraversal: false,
    supportsNot: false,
  });
};

type RunsSearchResultsOptions = {
  line: string;
  cursorIndex: number;
  valuesByAttribute: ValuesByAttribute;
  tagKeys: string[];
  loading: boolean;
};

const useRunsSearchResults = ({
  line,
  cursorIndex,
  valuesByAttribute,
  tagKeys,
  loading,
}: RunsSearchResultsOptions) => {
  const {valueKey, keyRangeEnd, keyQuoted} = useMemo(
    () => getTagPairAtCursor(line, cursorIndex),
    [line, cursorIndex],
  );
  const tagValues = useRunTagValues(valueKey);

  const hint = useMemo(
    () =>
      createRunsSearchHint({
        valuesByAttribute,
        valueKey,
        tagValues: tagValues.values,
        tagKeys,
        keyQuoted,
      }),
    [valuesByAttribute, valueKey, tagValues.values, tagKeys, keyQuoted],
  );

  const results = useSelectionAutoCompleteResults(hint, line, cursorIndex);

  // The shared visitor replaces the whole pair, but a key row writes only `key=`, so keep the value.
  const autoCompleteResults = useMemo(
    () => (keyRangeEnd !== null ? {...results, to: keyRangeEnd} : results),
    [results, keyRangeEnd],
  );

  return {
    autoCompleteResults,
    loading: loading || tagValues.loading,
  };
};

export const useRunsSearchAutoCompleteProvider = () => {
  const {options, loading: workspaceLoading} = useRepositoryOptions();
  const tagKeysQuery = useLazyRunTagKeys();

  const sensors = useLazyRunTagValues(TAG_KEY_BY_ATTRIBUTE.sensor);
  const schedules = useLazyRunTagValues(TAG_KEY_BY_ATTRIBUTE.schedule);
  const users = useLazyRunTagValues(TAG_KEY_BY_ATTRIBUTE.user);
  const backfills = useLazyRunTagValues(TAG_KEY_BY_ATTRIBUTE.backfill);
  const partitions = useLazyRunTagValues(TAG_KEY_BY_ATTRIBUTE.partition);
  const tagValueQueries = [sensors, schedules, users, backfills, partitions];

  // Keys with their own attribute (like `schedule`) are suggested there instead.
  const tagKeys = useMemo(
    () => tagKeysQuery.keys.filter((key) => !getAttributeForTagKey(key)),
    [tagKeysQuery.keys],
  );

  const valuesByAttribute = useMemo(() => {
    const {jobs, codeLocations} = getWorkspaceValues(options);
    return {
      id: [],
      status: RUN_STATUSES,
      job: jobs,
      code_location: codeLocations,
      sensor: withoutEmptyValues(sensors.values),
      schedule: withoutEmptyValues(schedules.values),
      user: withoutEmptyValues(users.values),
      backfill: withoutEmptyValues(backfills.values),
      partition: withoutEmptyValues(partitions.values),
      snapshot_id: [],
    } satisfies ValuesByAttribute;
  }, [
    options,
    sensors.values,
    schedules.values,
    users.values,
    backfills.values,
    partitions.values,
  ]);

  const loading =
    workspaceLoading || tagKeysQuery.loading || tagValueQueries.some((query) => query.loading);

  /** Load each list once per page, retrying any that failed. */
  const fetchSuggestions = () => {
    [tagKeysQuery, ...tagValueQueries]
      .filter((query) => !query.loaded && !query.loading)
      .forEach((query) => query.fetch());
  };

  const useAutoComplete: SelectionAutoCompleteProvider['useAutoComplete'] = ({line, cursorIndex}) =>
    useRunsSearchResults({line, cursorIndex, valuesByAttribute, tagKeys, loading});

  return {useAutoComplete, fetchSuggestions};
};
