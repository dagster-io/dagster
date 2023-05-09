import {gql, useLazyQuery, useApolloClient} from '@apollo/client';
import {
  TokenizingFieldValue,
  tokensAsStringArray,
  tokenizedValuesFromStringArray,
  Box,
  Icon,
} from '@dagster-io/ui';
import memoize from 'lodash/memoize';
import qs from 'qs';
import * as React from 'react';

import {__ASSET_JOB_PREFIX} from '../asset-graph/Utils';
import {RunsFilter, RunStatus} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';
import {TruncatedTextWithFullTextOnHover} from '../nav/getLeftNavItemsForOption';
import {useFilters} from '../ui/Filters';
import {FilterObject} from '../ui/Filters/useFilter';
import {capitalizeFirstLetter, useStaticSetFilter} from '../ui/Filters/useStaticSetFilter';
import {SuggestionFilterSuggestion, useSuggestionFilter} from '../ui/Filters/useSuggestionFilter';
import {TimeRangeState, useTimeRangeFilter} from '../ui/Filters/useTimeRangeFilter';
import {useRepositoryOptions} from '../workspace/WorkspaceContext';

import {DagsterTag} from './RunTag';
import {
  RunTagKeysNewQuery,
  RunTagValuesNewQuery,
  RunTagValuesNewQueryVariables,
} from './types/RunsFilterInputNew.types';

export type RunFilterTokenType =
  | 'id'
  | 'status'
  | 'pipeline'
  | 'job'
  | 'snapshotId'
  | 'tag'
  | 'backfill'
  | 'created_date_before'
  | 'created_date_after';

export type RunFilterToken = {
  token?: RunFilterTokenType;
  value: string;
};
const CREATED_BY_TAGS = [
  DagsterTag.Automaterialize,
  DagsterTag.SensorName,
  DagsterTag.ScheduleName,
  DagsterTag.User,
];

const RUN_PROVIDERS_EMPTY = [
  {
    token: 'id',
    values: () => [],
  },
  {
    token: 'status',
    values: () => [],
  },
  {
    token: 'pipeline',
    values: () => [],
  },
  {
    token: 'job',
    values: () => [],
  },
  {
    token: 'tag',
    values: () => [],
  },
  {
    token: 'snapshotId',
    values: () => [],
  },
  {
    token: 'created_date_before',
    values: () => [],
  },
  {
    token: 'created_date_after',
    values: () => [],
  },
];

const StatusFilterValues = Object.keys(RunStatus).map((x) => ({
  label: capitalizeFirstLetter(x),
  value: x,
  match: [x],
}));

/**
 * This React hook provides run filtering state similar to React.useState(), but syncs
 * the value to the URL query string so that reloading the page / navigating "back"
 * maintains your view as expected.
 *
 * @param enabledFilters: This is useful if you want to ignore some filters that could
 * be provided (eg pipeline:, which is not relevant within pipeline scoped views.)
 */
export function useQueryPersistedRunFilters(enabledFilters?: RunFilterTokenType[]) {
  return useQueryPersistedState<RunFilterToken[]>(
    React.useMemo(
      () => ({
        encode: (tokens) => ({q: tokensAsStringArray(tokens), cursor: undefined}),
        decode: ({q = []}) =>
          tokenizedValuesFromStringArray(q, RUN_PROVIDERS_EMPTY).filter(
            (t) =>
              !t.token || !enabledFilters || enabledFilters.includes(t.token as RunFilterTokenType),
          ) as RunFilterToken[],
      }),
      [enabledFilters],
    ),
  );
}

export function runsPathWithFilters(filterTokens: RunFilterToken[]) {
  return `/runs?${qs.stringify({q: tokensAsStringArray(filterTokens)}, {arrayFormat: 'brackets'})}`;
}

export function runsFilterForSearchTokens(search: TokenizingFieldValue[]) {
  if (!search[0]) {
    return {};
  }

  const obj: RunsFilter = {};

  for (const item of search) {
    if (item.token === 'created_date_before') {
      obj.createdBefore = parseInt(item.value);
    } else if (item.token === 'created_date_after') {
      obj.updatedAfter = parseInt(item.value);
    } else if (item.token === 'pipeline' || item.token === 'job') {
      obj.pipelineName = item.value;
    } else if (item.token === 'id') {
      obj.runIds = obj.runIds || [];
      obj.runIds.push(item.value);
    } else if (item.token === 'status') {
      obj.statuses = obj.statuses || [];
      obj.statuses.push(item.value as RunStatus);
    } else if (item.token === 'snapshotId') {
      obj.snapshotId = item.value;
    } else if (item.token === 'tag') {
      const [key, value = ''] = item.value.split('=');
      if (obj.tags) {
        obj.tags.push({key, value});
      } else {
        obj.tags = [{key, value}];
      }
    }
  }

  return obj;
}

interface RunsFilterInputProps {
  tokens: RunFilterToken[];
  onChange: (tokens: RunFilterToken[]) => void;
  enabledFilters?: RunFilterTokenType[];
  loading?: boolean;
}

// Exclude these tags from the "tag" filter because theyre already being fetched by other filters.
const tagsToExclude = [...CREATED_BY_TAGS, DagsterTag.Backfill];

export const useRunsFilterInput = ({tokens, onChange, enabledFilters}: RunsFilterInputProps) => {
  const {options} = useRepositoryOptions();

  const [fetchTagKeys, {data: tagKeyData}] = useLazyQuery<RunTagKeysNewQuery>(RUN_TAG_KEYS_QUERY);
  const client = useApolloClient();
  const {UserDisplay} = useLaunchPadHooks();

  const fetchTagValues = React.useCallback(
    async (tagKey: string) => {
      const {data} = await client.query<RunTagValuesNewQuery, RunTagValuesNewQueryVariables>({
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
  }>[] = React.useMemo(() => {
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

  const isBackfillsFilterEnabled = !enabledFilters || enabledFilters?.includes('backfill');

  const onFocus = React.useCallback(() => {
    fetchTagKeys();
    fetchSensorValues();
    fetchScheduleValues();
    fetchUserValues();
    if (isBackfillsFilterEnabled) {
      fetchBackfillValues();
    }
  }, [
    fetchBackfillValues,
    fetchScheduleValues,
    fetchSensorValues,
    fetchTagKeys,
    fetchUserValues,
    isBackfillsFilterEnabled,
  ]);

  const createdByValues = React.useMemo(
    () => [
      tagToFilterValue(DagsterTag.Automaterialize, 'true'),
      ...sensorValues,
      ...scheduleValues,
      ...userValues,
    ],
    [sensorValues, scheduleValues, userValues],
  );

  const isJobFilterEnabled = !enabledFilters || enabledFilters?.includes('job');

  const {pipelines, jobs} = React.useMemo(() => {
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

  const isPipelineFilterEnabled =
    !enabledFilters || (enabledFilters?.includes('job') && pipelines.length);

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
    initialState: React.useMemo(
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
    initialState: React.useMemo(
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
    initialState: React.useMemo(
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

  const backfillsFilter = useStaticSetFilter({
    name: 'Backfill ID',
    icon: 'backfill',
    allValues: backfillValues,
    allowMultipleSelections: false,
    initialState: React.useMemo(() => {
      return new Set(
        tokens
          .filter(
            ({token, value}) => token === 'tag' && value.split('=')[0] === DagsterTag.Backfill,
          )
          .map(({value}) => tagValueToFilterObject(value)),
      );
    }, [tokens]),
    renderLabel: ({value}) => (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="job" />
        <TruncatedTextWithFullTextOnHover text={value.value} />
      </Box>
    ),
    getStringValue: ({value}) => value,
    onStateChanged: (values) => {
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
  });

  const {button, activeFiltersJsx} = useFilters({
    filters: [
      !enabledFilters || enabledFilters?.includes('status') ? statusFilter : null,
      useStaticSetFilter({
        name: 'Created By',
        icon: 'add_circle',
        allValues: createdByValues,
        renderLabel: ({value}) => {
          let icon;
          let labelValue = value.value;
          if (value.type === DagsterTag.SensorName) {
            icon = <Icon name="sensors" />;
          } else if (value.type === DagsterTag.ScheduleName) {
            icon = <Icon name="schedule" />;
          } else if (value.type === DagsterTag.User) {
            return <UserDisplay email={value.value} isFilter />;
          } else if (value.type === DagsterTag.Automaterialize) {
            icon = <Icon name="auto_materialize_policy" />;
            labelValue = 'Auto-materialize policy';
          }
          return (
            <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
              {icon}
              <TruncatedTextWithFullTextOnHover text={labelValue} />
            </Box>
          );
        },
        getStringValue: (x) => {
          if (x.type === DagsterTag.Automaterialize) {
            return 'Auto-materialize policy';
          }
          return x.value;
        },
        initialState: React.useMemo(() => {
          return new Set(
            tokens
              .filter(
                ({token, value}) =>
                  token === 'tag' && CREATED_BY_TAGS.includes(value.split('=')[0] as DagsterTag),
              )
              .map(({value}) => tagValueToFilterObject(value)),
          );
        }, [tokens]),
        onStateChanged: (values) => {
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
      }),
      useTimeRangeFilter({
        name: 'Created date',
        icon: 'date',
        timezone: 'UTC',
        initialState: React.useMemo(() => {
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
              values[0] != null
                ? {token: 'created_date_after', value: `${values[0] / 1000}`}
                : null,
              values[1] != null
                ? {token: 'created_date_before', value: `${values[1] / 1000}`}
                : null,
            ].filter((x) => x) as RunFilterToken[]),
          ]);
        },
      }),
      isJobFilterEnabled ? jobFilter : null,
      isPipelineFilterEnabled ? pipelinesFilter : null,
      isBackfillsFilterEnabled ? backfillsFilter : null,
      useSuggestionFilter({
        name: 'Tag',
        icon: 'tag',
        initialSuggestions: tagSuggestions,

        freeformSearchResult: React.useCallback(
          (
            query: string,
            path: {
              value: string;
              key?: string | undefined;
            }[],
          ) => {
            return {
              ...tagSuggestionValueObject(path.length ? path[0].value : '', query),
              final: !!path.length,
            };
          },
          [],
        ),

        state: React.useMemo(() => {
          return tokens
            .filter(({token, value}) => {
              if (token !== 'tag') {
                return false;
              }
              return !tagsToExclude.includes(value.split('=')[0] as DagsterTag);
            })
            .map((token) => {
              const [key, value] = token.value.split('=');
              return tagSuggestionValueObject(key, value).value;
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
      }),
    ].filter((x) => x) as FilterObject[],
  });

  return {button: <span onClick={onFocus}>{button}</span>, activeFiltersJsx};
};

export const RUN_TAG_KEYS_QUERY = gql`
  query RunTagKeysNewQuery {
    runTagKeysOrError {
      ... on RunTagKeys {
        keys
      }
    }
  }
`;

export const RUN_TAG_VALUES_QUERY = gql`
  query RunTagValuesNewQuery($tagKeys: [String!]!) {
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

export function useTagDataFilterValues(tagKey?: DagsterTag) {
  const [fetch, {data}] = useLazyQuery<RunTagValuesNewQuery, RunTagValuesNewQueryVariables>(
    RUN_TAG_VALUES_QUERY,
    {
      variables: {tagKeys: tagKey ? [tagKey] : []},
    },
  );

  const values = React.useMemo(() => {
    if (!tagKey || data?.runTagsOrError?.__typename !== 'RunTags') {
      return [];
    }
    return data.runTagsOrError.tags
      .map((x) => x.values)
      .flat()
      .map((x) => tagToFilterValue(tagKey, x));
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
  value: value.split('=')[1],
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
