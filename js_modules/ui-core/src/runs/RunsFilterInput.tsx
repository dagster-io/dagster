import {Box, Icon} from '@dagster-io/ui-components';
import {UserDisplay} from '@shared/runs/UserDisplay';
import memoize from 'lodash/memoize';
import {useCallback, useMemo} from 'react';

import {DagsterTag} from './RunTag';
import {RunFilterToken, RunFilterTokenType} from './RunsFilterUtils';
import {gql, useApolloClient, useLazyQuery} from '../apollo-client';
import {
  RunTagKeysQuery,
  RunTagKeysQueryVariables,
  RunTagValuesQuery,
  RunTagValuesQueryVariables,
} from './types/RunsFilterInput.types';
import {COMMON_COLLATOR} from '../app/Util';
import {__ASSET_JOB_PREFIX} from '../asset-graph/Utils';
import {RunStatus} from '../graphql/types';
import {useFilters} from '../ui/BaseFilters';
import {FilterObject} from '../ui/BaseFilters/useFilter';
import {capitalizeFirstLetter, useStaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';
import {
  SuggestionFilterSuggestion,
  useSuggestionFilter,
} from '../ui/BaseFilters/useSuggestionFilter';
import {TimeRangeState, useTimeRangeFilter} from '../ui/BaseFilters/useTimeRangeFilter';
import {TruncatedTextWithFullTextOnHover} from '../ui/TruncatedTextWithFullTextOnHover';
import {useRepositoryOptions} from '../workspace/WorkspaceContext/util';

export interface RunsFilterInputProps {
  loading?: boolean;
  tokens: RunFilterToken[];
  onChange: (tokens: RunFilterToken[]) => void;
  enabledFilters?: RunFilterTokenType[];
}

const StatusFilterValues = Object.keys(RunStatus).map((x) => ({
  label: capitalizeFirstLetter(x),
  value: x,
  match: [x],
}));
const CREATED_BY_TAGS = [
  DagsterTag.Automaterialize,
  DagsterTag.SensorName,
  DagsterTag.ScheduleName,
  DagsterTag.User,
];

// Exclude these tags from the "tag" filter because they're already being fetched by other filters.
const tagsToExclude = [...CREATED_BY_TAGS, DagsterTag.Backfill, DagsterTag.Partition];

export const useRunsFilterInput = ({tokens, onChange, enabledFilters}: RunsFilterInputProps) => {
  const {options} = useRepositoryOptions();

  const [fetchTagKeys, {data: tagKeyData}] = useLazyQuery<
    RunTagKeysQuery,
    RunTagKeysQueryVariables
  >(RUN_TAG_KEYS_QUERY);
  const client = useApolloClient();

  const fetchTagValues = useCallback(
    async (tagKey: string) => {
      const {data} = await client.query<RunTagValuesQuery, RunTagValuesQueryVariables>({
        query: RUN_TAG_VALUES_QUERY,
        variables: {tagKeys: tagKey ? [tagKey] : []},
      });
      if (data?.runTagsOrError?.__typename === 'RunTags') {
        return (
          data?.runTagsOrError.tags?.[0]?.values.map((tagValue) =>
            tagSuggestionValueObject(tagKey, tagValue),
          ) || []
        );
      }

      return [];
    },
    [client],
  );

  const tagSuggestions: SuggestionFilterSuggestion<{
    value: string;
    key?: string;
  }>[] = useMemo(() => {
    if (tagKeyData?.runTagKeysOrError?.__typename === 'RunTagKeys') {
      return (
        tagKeyData?.runTagKeysOrError.keys
          .filter((key) => !tagsToExclude.includes(key as DagsterTag))
          .map((tagKey) => ({
            final: false,
            value: {
              value: tagKey,
            },
          })) || []
      );
    }
    return [];
  }, [tagKeyData]);

  const [fetchSensorValues, sensorValues] = useTagDataFilterValues(DagsterTag.SensorName);
  const [fetchScheduleValues, scheduleValues] = useTagDataFilterValues(DagsterTag.ScheduleName);
  const [fetchUserValues, userValues] = useTagDataFilterValues(DagsterTag.User);
  const [fetchBackfillValues, backfillValues] = useTagDataFilterValues(DagsterTag.Backfill);
  const [fetchPartitionValues, partitionValues] = useTagDataFilterValues(DagsterTag.Partition);

  const isIDFilterEnabled = !enabledFilters || enabledFilters?.includes('id');
  const isStatusFilterEnabled = !enabledFilters || enabledFilters?.includes('status');
  const isBackfillsFilterEnabled = !enabledFilters || enabledFilters?.includes('backfill');
  const isPartitionsFilterEnabled = !enabledFilters || enabledFilters?.includes('partition');
  const isJobFilterEnabled = !enabledFilters || enabledFilters?.includes('job');

  const onFocus = useCallback(() => {
    fetchTagKeys();
    fetchSensorValues();
    fetchScheduleValues();
    fetchUserValues();
    if (isBackfillsFilterEnabled) {
      fetchBackfillValues();
    }
    fetchPartitionValues();
  }, [
    fetchBackfillValues,
    fetchScheduleValues,
    fetchSensorValues,
    fetchTagKeys,
    fetchUserValues,
    fetchPartitionValues,
    isBackfillsFilterEnabled,
  ]);

  const createdByValues = useMemo(
    () => [
      {
        ...tagToFilterValue(DagsterTag.Automaterialize, 'true'),
        final: true,
      },
      ...[...sensorValues].sort((a, b) => COMMON_COLLATOR.compare(a.label, b.label)),
      ...[...scheduleValues].sort((a, b) => COMMON_COLLATOR.compare(a.label, b.label)),
      ...[...userValues].sort((a, b) => COMMON_COLLATOR.compare(a.label, b.label)),
    ],
    [sensorValues, scheduleValues, userValues],
  );

  const {pipelines, jobs} = useMemo(() => {
    const pipelineNames = [];
    const jobNames = [];

    if (!isJobFilterEnabled) {
      return {pipelines: [], jobs: []};
    }

    for (const option of options) {
      const {repository} = option;
      for (const pipeline of repository.pipelines) {
        if (pipeline.isJob) {
          if (!pipeline.name.startsWith(__ASSET_JOB_PREFIX)) {
            jobNames.push(pipeline.name);
          }
        } else {
          pipelineNames.push(pipeline.name);
        }
      }
    }
    return {
      pipelines: pipelineNames.map((name) => ({
        key: name,
        value: name,
        match: [name],
      })),
      jobs: jobNames.map((name) => ({
        key: name,
        value: name,
        match: [name],
      })),
    };
  }, [isJobFilterEnabled, options]);

  const jobFilter = useStaticSetFilter({
    name: 'Job',
    icon: 'job',
    allowMultipleSelections: false,
    allValues: jobs,
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="job" />
        <TruncatedTextWithFullTextOnHover text={value} />
      </Box>
    ),
    getStringValue: (x) => x,
    state: useMemo(
      () => new Set(tokens.filter((x) => x.token === 'job').map((x) => x.value)),
      [tokens],
    ),
    onStateChanged: (values) => {
      onChange([
        ...tokens.filter((x) => x.token !== 'job'),
        ...Array.from(values).map((value) => ({
          token: 'job' as const,
          value,
        })),
      ]);
    },
  });

  const statusFilter = useStaticSetFilter({
    name: 'Status',
    icon: 'status',
    allValues: StatusFilterValues,
    renderLabel: ({value}) => <span>{capitalizeFirstLetter(value)}</span>,
    getStringValue: (x) => capitalizeFirstLetter(x),
    state: useMemo(
      () => new Set(tokens.filter((x) => x.token === 'status').map((x) => x.value)),
      [tokens],
    ),
    onStateChanged: (values) => {
      onChange([
        ...tokens.filter((x) => x.token !== 'status'),
        ...Array.from(values).map((value) => ({
          token: 'status' as const,
          value,
        })),
      ]);
    },
  });

  const pipelinesFilter = useStaticSetFilter({
    name: 'Pipelines',
    icon: 'job',
    allValues: pipelines,
    allowMultipleSelections: false,
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="job" />
        <TruncatedTextWithFullTextOnHover text={value} />
      </Box>
    ),
    getStringValue: (x) => x,
    state: useMemo(
      () => new Set(tokens.filter((x) => x.token === 'job').map((x) => x.value)),
      [tokens],
    ),
    onStateChanged: (values) => {
      onChange([
        ...tokens.filter((x) => x.token !== 'pipeline'),
        ...Array.from(values).map((value) => ({
          token: 'pipeline' as const,
          value,
        })),
      ]);
    },
  });

  const backfillsFilter = useSuggestionFilter({
    name: 'Backfill ID',
    icon: 'backfill',
    initialSuggestions: backfillValues,
    getNoSuggestionsPlaceholder: (query) => (query ? 'Invalid ID' : 'Type or paste a backfill ID'),

    state: useMemo(() => {
      return tokens
        .filter(({token, value}) => token === 'tag' && value.split('=')[0] === DagsterTag.Backfill)
        .map(({value}) => tagValueToFilterObject(value));
    }, [tokens]),

    freeformSearchResult: (query) => {
      return /^([a-zA-Z0-9-]{6,12})$/.test(query.trim())
        ? {
            value: tagValueToFilterObject(`${DagsterTag.Backfill}=${query.trim()}`),
            final: true,
          }
        : null;
    },
    setState: (values) => {
      onChange([
        ...tokens.filter(({token, value}) => {
          if (token !== 'tag') {
            return true;
          }
          return value.split('=')[0] !== DagsterTag.Backfill;
        }),
        ...Array.from(values).map((value) => ({
          token: 'tag' as const,
          value: `${value.type}=${value.value}`,
        })),
      ]);
    },
    getStringValue: ({value}) => value,
    getKey: ({value}) => value,
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="id" />
        <TruncatedTextWithFullTextOnHover text={value.value} />
      </Box>
    ),
    onSuggestionClicked: async (value) => {
      return [{value}];
    },
    renderActiveStateLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="id" />
        <TruncatedTextWithFullTextOnHover text={value.value} />
        {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
        {value.value!}
      </Box>
    ),
    isMatch: ({value}, query) => value.toLowerCase().includes(query.toLowerCase()),
    matchType: 'any-of',
  });

  const partitionsFilter = useSuggestionFilter({
    name: 'Partition',
    icon: 'partition',
    initialSuggestions: partitionValues,
    getNoSuggestionsPlaceholder: (query) =>
      query ? 'Invalid partition' : 'Type or paste a partition',

    state: useMemo(() => {
      return tokens
        .filter(({token, value}) => token === 'tag' && value.split('=')[0] === DagsterTag.Partition)
        .map(({value}) => tagValueToFilterObject(value));
    }, [tokens]),

    freeformSearchResult: (query) => {
      return {
        value: tagValueToFilterObject(`${DagsterTag.Partition}=${query.trim()}`),
        final: true,
      };
    },
    setState: (values) => {
      onChange([
        ...tokens.filter(({token, value}) => {
          if (token !== 'tag') {
            return true;
          }
          return value.split('=')[0] !== DagsterTag.Partition;
        }),
        ...Array.from(values).map((value) => ({
          token: 'tag' as const,
          value: `${value.type}=${value.value}`,
        })),
      ]);
    },
    getStringValue: ({value}) => value,
    getKey: ({value}) => value,
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="partition" />
        <TruncatedTextWithFullTextOnHover text={value.value} />
      </Box>
    ),
    onSuggestionClicked: async (value) => {
      return [{value}];
    },
    renderActiveStateLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="partition" />
        <TruncatedTextWithFullTextOnHover text={value.value} />
        {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
        {value.value!}
      </Box>
    ),
    isMatch: ({value}, query) => value.toLowerCase().includes(query.toLowerCase()),
    matchType: 'any-of',
  });

  const launchedByFilter = useSuggestionFilter({
    name: 'Launched by',
    icon: 'add_circle',
    initialSuggestions: createdByValues,
    allowMultipleSelections: false,
    renderLabel: ({value}) => {
      let icon;
      let labelValue = value.value;
      if (value.type === DagsterTag.SensorName) {
        icon = <Icon name="sensors" />;
      } else if (value.type === DagsterTag.ScheduleName) {
        icon = <Icon name="schedule" />;
      } else if (value.type === DagsterTag.User) {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        return <UserDisplay email={value.value!} isFilter />;
      } else if (value.type === DagsterTag.Automaterialize) {
        icon = <Icon name="automation_condition" />;
        labelValue = 'Automation condition';
      }
      return (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          {icon}
          {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
          <TruncatedTextWithFullTextOnHover text={labelValue!} />
        </Box>
      );
    },
    getStringValue: (x) => {
      if (x.type === DagsterTag.Automaterialize) {
        return 'Automation condition';
      }
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      return x.value!;
    },
    state: useMemo(() => {
      return tokens
        .filter(
          ({token, value}) =>
            token === 'tag' && CREATED_BY_TAGS.includes(value.split('=')[0] as DagsterTag),
        )
        .map(({value}) => tagValueToFilterObject(value));
    }, [tokens]),
    freeformSearchResult(query, suggestionPath) {
      if (suggestionPath.length === 0) {
        return [
          {
            value: {
              key: `${DagsterTag.ScheduleName}-freeform`,
              type: DagsterTag.ScheduleName,
              value: query,
            },
            final: true,
          },
          {
            value: {
              key: `${DagsterTag.SensorName}-freeform`,
              type: DagsterTag.SensorName,
              value: query,
            },
            final: true,
          },
        ];
      }
      return null;
    },
    freeformResultPosition: 'end',
    setState: (values) => {
      onChange([
        ...tokens.filter((token) => {
          if (token.token !== 'tag') {
            return true;
          }
          return !CREATED_BY_TAGS.includes(token.value.split('=')[0] as DagsterTag);
        }),
        ...Array.from(values).map((value) => ({
          token: 'tag' as const,
          value: `${value.type}=${value.value}`,
        })),
      ]);
    },
    getKey: ({value}) => value,
    isMatch: ({value}, query) => value.toLowerCase().includes(query.toLowerCase()),
    matchType: 'any-of',
    onSuggestionClicked: async (value) => {
      return [{value}];
    },
  });

  const createdDateFilter = useTimeRangeFilter({
    name: 'Created date',
    activeFilterTerm: 'Created',
    icon: 'date',
    state: useMemo(() => {
      const before = tokens.find((token) => token.token === 'created_date_before');
      const after = tokens.find((token) => token.token === 'created_date_after');
      return [
        after ? parseInt(after.value) * 1000 : null,
        before ? parseInt(before.value) * 1000 : null,
      ] as TimeRangeState;
    }, [tokens]),
    onStateChanged: (values) => {
      onChange([
        ...tokens.filter(
          (token) => !['created_date_before', 'created_date_after'].includes(token.token ?? ''),
        ),
        ...([
          values[0] != null ? {token: 'created_date_after', value: `${values[0] / 1000}`} : null,
          values[1] != null ? {token: 'created_date_before', value: `${values[1] / 1000}`} : null,
        ].filter((x) => x) as RunFilterToken[]),
      ]);
    },
  });

  const tagFilter = useSuggestionFilter({
    name: 'Tag',
    icon: 'tag',
    initialSuggestions: tagSuggestions,

    freeformSearchResult: useCallback(
      (
        query: string,
        path: {
          value: string;
          key?: string | undefined;
        }[],
      ) => {
        return {
          ...tagSuggestionValueObject(path[0] ? path[0].value : '', query),
          final: !!path.length,
        };
      },
      [],
    ),

    state: useMemo(() => {
      return tokens
        .filter(({token, value}) => {
          if (token !== 'tag') {
            return false;
          }
          return !tagsToExclude.includes(value.split('=')[0] as DagsterTag);
        })
        .map((token) => {
          const [key, value] = token.value.split('=');
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          return tagSuggestionValueObject(key!, value!).value;
        });
    }, [tokens]),

    setState: (nextState) => {
      onChange([
        ...tokens.filter(({token, value}) => {
          if (token !== 'tag') {
            return true;
          }
          return tagsToExclude.includes(value.split('=')[0] as DagsterTag);
        }),
        ...nextState.map(({key, value}) => {
          return {
            token: 'tag' as const,
            value: `${key}=${value}`,
          };
        }),
      ]);
    },
    onSuggestionClicked: async ({value}) => {
      return await fetchTagValues(value);
    },
    getStringValue: ({key, value}) => `${key}=${value}`,
    getKey: ({key, value}) => `${key}: ${value}`,
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="tag" />
        <TruncatedTextWithFullTextOnHover text={value.value} />
      </Box>
    ),
    renderActiveStateLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="tag" />
        <TruncatedTextWithFullTextOnHover text={`${value.key}=${value.value}`} />
        {value.key}={value.value}
      </Box>
    ),
    isMatch: ({value}, query) => value.toLowerCase().includes(query.toLowerCase()),
    matchType: 'all-of',
  });

  const ID_EMPTY = 'Type or paste 36-character ID';
  const ID_TOO_SHORT = 'Invalid Run ID';

  const idFilter = useSuggestionFilter({
    name: 'Run ID',
    icon: 'id',
    initialSuggestions: [],
    getNoSuggestionsPlaceholder: (query) => (!query ? ID_EMPTY : ID_TOO_SHORT),
    state: useMemo(() => {
      return tokens.filter(({token}) => token === 'id').map((token) => token.value);
    }, [tokens]),
    freeformSearchResult: (query) => {
      return /^([a-f0-9-]{36})$/.test(query.trim()) ? {value: query.trim(), final: true} : null;
    },
    setState: (nextState) => {
      onChange([
        ...tokens.filter(({token}) => token !== 'id'),
        ...nextState.map((value) => {
          return {token: 'id' as const, value};
        }),
      ]);
    },
    getStringValue: (value) => value,
    getKey: (value) => value,
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="id" />
        <TruncatedTextWithFullTextOnHover text={value} />
      </Box>
    ),
    onSuggestionClicked: async (value) => {
      return [{value}];
    },
    renderActiveStateLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="id" />
        <TruncatedTextWithFullTextOnHover text={value} />
        {value}
      </Box>
    ),
    isMatch: (value, query) => value.toLowerCase().includes(query.toLowerCase()),
    matchType: 'any-of',
  });

  const {button, activeFiltersJsx} = useFilters({
    filters: [
      isStatusFilterEnabled ? statusFilter : null,
      launchedByFilter,
      createdDateFilter,
      isJobFilterEnabled ? jobFilter : null,
      isJobFilterEnabled && pipelines.length > 0 ? pipelinesFilter : null,
      isIDFilterEnabled ? idFilter : null,
      isBackfillsFilterEnabled ? backfillsFilter : null,
      isPartitionsFilterEnabled ? partitionsFilter : null,
      tagFilter,
    ].filter((x) => x) as FilterObject[],
  });

  return {button: <span onClick={onFocus}>{button}</span>, activeFiltersJsx};
};

export function useTagDataFilterValues(tagKey?: DagsterTag) {
  const [fetch, {data}] = useLazyQuery<RunTagValuesQuery, RunTagValuesQueryVariables>(
    RUN_TAG_VALUES_QUERY,
    {
      variables: {tagKeys: tagKey ? [tagKey] : []},
    },
  );

  const values = useMemo(() => {
    if (!tagKey || data?.runTagsOrError?.__typename !== 'RunTags') {
      return [];
    }
    return data.runTagsOrError.tags
      .map((x) => x.values)
      .flat()
      .map((x) => ({...tagToFilterValue(tagKey, x), final: true}));
  }, [data, tagKey]);

  return [fetch, values] as [typeof fetch, typeof values];
}

function tagToFilterValue(key: string, value: string) {
  return {
    label: value,
    value: tagValueToFilterObject(`${key}=${value}`),
    match: [value],
  };
}

// Memoize this object because the static set filter component checks for object equality (set.has)
export const tagValueToFilterObject = memoize((value: string) => ({
  key: value,
  type: value.split('=')[0] as DagsterTag,
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  value: value.split('=')[1]!,
}));

export const tagSuggestionValueObject = memoize(
  (key: string, value: string) => ({
    final: true,
    value: {
      key,
      value,
    },
  }),
  (key, value) => `${key}:${value}`,
);

export const RUN_TAG_KEYS_QUERY = gql`
  query RunTagKeysQuery {
    runTagKeysOrError {
      ... on RunTagKeys {
        keys
      }
    }
  }
`;

export const RUN_TAG_VALUES_QUERY = gql`
  query RunTagValuesQuery($tagKeys: [String!]!) {
    runTagsOrError(tagKeys: $tagKeys) {
      ... on RunTags {
        tags {
          key
          values
        }
      }
    }
  }
`;
