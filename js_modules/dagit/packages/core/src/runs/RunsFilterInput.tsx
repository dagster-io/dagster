import {gql, useLazyQuery} from '@apollo/client';
import {
  SuggestionProvider,
  TokenizingField,
  TokenizingFieldValue,
  tokensAsStringArray,
  tokenizedValuesFromStringArray,
} from '@dagster-io/ui';
import qs from 'qs';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {__ASSET_JOB_PREFIX} from '../asset-graph/Utils';
import {RunsFilter, RunStatus} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {DagsterRepoOption, useRepositoryOptions} from '../workspace/WorkspaceContext';

import {useRunsFilterInput as useRunsFilterInputNew} from './RunsFilterInputNew';
import {
  RunTagKeysQuery,
  RunTagValuesQuery,
  RunTagValuesQueryVariables,
} from './types/RunsFilterInput.types';

type RunTags = Array<{
  __typename: 'PipelineTagAndValues';
  key: string;
  values: Array<string>;
}>;

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
];

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
    if (item.token === 'pipeline' || item.token === 'job') {
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

function searchSuggestionsForRuns(
  repositoryOptions: DagsterRepoOption[],
  runTagKeys?: string[],
  selectedRunTagKey?: string,
  runTagValues?: RunTags,
  enabledFilters?: RunFilterTokenType[],
): SuggestionProvider[] {
  const pipelineNames = new Set<string>();
  const jobNames = new Set<string>();

  for (const option of repositoryOptions) {
    const {repository} = option;
    for (const pipeline of repository.pipelines) {
      if (pipeline.isJob) {
        jobNames.add(pipeline.name);
      } else {
        pipelineNames.add(pipeline.name);
      }
    }
  }

  const suggestions: {token: RunFilterTokenType; values: () => string[]; textOnly?: boolean}[] = [
    {
      token: 'id',
      values: () => [],
    },
    {
      token: 'status',
      values: () => Object.keys(RunStatus),
    },
    {
      token: 'pipeline',
      values: () => Array.from(pipelineNames),
    },
    {
      token: 'job',
      values: () => Array.from(jobNames),
    },
    {
      token: 'tag',
      values: () => {
        if (!selectedRunTagKey) {
          return (runTagKeys || []).map((key) => `${key}`);
        }
        return (runTagValues || [])
          .filter(({key}) => key === selectedRunTagKey)
          .map(({values}) => values.map((value) => `${selectedRunTagKey}=${value}`))
          .flat();
      },
      textOnly: !selectedRunTagKey,
    },
    {
      token: 'snapshotId',
      values: () => [],
    },
  ];

  if (enabledFilters) {
    return suggestions.filter((x) => enabledFilters.includes(x.token));
  }

  return suggestions;
}

export interface RunsFilterInputProps {
  loading?: boolean;
  tokens: RunFilterToken[];
  onChange: (tokens: RunFilterToken[]) => void;
  enabledFilters?: RunFilterTokenType[];
}

export const RunsFilterInput = (props: RunsFilterInputProps) => {
  const {flagRunsTableFiltering} = useFeatureFlags();
  const {button, activeFiltersJsx} = useRunsFilterInputNew(props);
  return flagRunsTableFiltering ? (
    <div>
      {button}
      {activeFiltersJsx}
    </div>
  ) : (
    <RunsFilterInputImpl {...props} />
  );
};

const RunsFilterInputImpl: React.FC<RunsFilterInputProps> = ({
  tokens,
  onChange,
  enabledFilters,
  loading,
}) => {
  const {options} = useRepositoryOptions();
  const [selectedTagKey, setSelectedTagKey] = React.useState<string | undefined>();
  const [fetchTagKeys, {data: tagKeyData}] = useLazyQuery<RunTagKeysQuery>(RUN_TAG_KEYS_QUERY);
  const [fetchTagValues, {data: tagValueData}] = useLazyQuery<
    RunTagValuesQuery,
    RunTagValuesQueryVariables
  >(RUN_TAG_VALUES_QUERY, {
    variables: {tagKeys: selectedTagKey ? [selectedTagKey] : []},
  });

  React.useEffect(() => {
    if (selectedTagKey) {
      fetchTagValues();
    }
  }, [selectedTagKey, fetchTagValues]);

  const suggestions = searchSuggestionsForRuns(
    options,
    tagKeyData?.runTagKeysOrError?.__typename === 'RunTagKeys'
      ? tagKeyData.runTagKeysOrError.keys
      : [],
    selectedTagKey,
    tagValueData?.runTagsOrError?.__typename === 'RunTags' ? tagValueData.runTagsOrError.tags : [],
    enabledFilters,
  );

  const search = tokenizedValuesFromStringArray(tokensAsStringArray(tokens), suggestions);
  const refreshSuggestions = (text: string) => {
    if (!text.startsWith('tag:')) {
      return;
    }
    const tagKeyText = text.slice(4);
    if (
      tagKeyData?.runTagKeysOrError?.__typename === 'RunTagKeys' &&
      tagKeyData.runTagKeysOrError.keys.includes(tagKeyText)
    ) {
      setSelectedTagKey(tagKeyText);
    }
  };

  const suggestionProvidersFilter = (
    suggestionProviders: SuggestionProvider[],
    values: TokenizingFieldValue[],
  ) => {
    const tokens: string[] = [];
    for (const {token} of values) {
      if (token) {
        tokens.push(token);
      }
    }

    // If id is set, then no other filters can be set
    if (tokens.includes('id')) {
      return [];
    }

    // Can only have one filter value for pipeline or id
    const limitedTokens = new Set<string>(['id', 'job', 'pipeline', 'snapshotId']);
    const presentLimitedTokens = tokens.filter((token) => limitedTokens.has(token));

    return suggestionProviders.filter(
      (provider) => !provider.token || !presentLimitedTokens.includes(provider.token),
    );
  };

  const onFocus = React.useCallback(() => fetchTagKeys(), [fetchTagKeys]);

  return (
    <TokenizingField
      values={search}
      onChange={(values) => onChange(values as RunFilterToken[])}
      onFocus={onFocus}
      onTextChange={refreshSuggestions}
      suggestionProviders={suggestions}
      suggestionProvidersFilter={suggestionProvidersFilter}
      loading={loading}
    />
  );
};

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
