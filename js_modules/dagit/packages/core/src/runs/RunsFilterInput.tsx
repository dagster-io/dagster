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

import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RunStatus, RunsFilter} from '../types/globalTypes';
import {DagsterRepoOption, useRepositoryOptions} from '../workspace/WorkspaceContext';

import {canAddTagToFilter} from './RunTags';
import {
  RunsSearchSpaceQuery,
  RunsSearchSpaceQuery_pipelineRunTags,
} from './types/RunsSearchSpaceQuery';

type PipelineRunTags = RunsSearchSpaceQuery_pipelineRunTags[];

export type RunFilterTokenType = 'id' | 'status' | 'pipeline' | 'job' | 'snapshotId' | 'tag';

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
  return `/instance/runs?${qs.stringify(
    {q: tokensAsStringArray(filterTokens)},
    {arrayFormat: 'brackets'},
  )}`;
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
      const [key, value] = item.value.split('=');
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
  pipelineRunTags?: PipelineRunTags,
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

  const suggestions: {token: RunFilterTokenType; values: () => string[]}[] = [
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
        const all: string[] = [];
        [...(pipelineRunTags || [])]
          .filter(({key}) => canAddTagToFilter(key))
          .sort((a, b) => a.key.localeCompare(b.key))
          .forEach((t) => t.values.forEach((v) => all.push(`${t.key}=${v}`)));
        return all;
      },
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

interface RunsFilterInputProps {
  loading?: boolean;
  tokens: RunFilterToken[];
  onChange: (tokens: RunFilterToken[]) => void;
  enabledFilters?: RunFilterTokenType[];
}

export const RunsFilterInput: React.FC<RunsFilterInputProps> = ({
  loading,
  tokens,
  onChange,
  enabledFilters,
}) => {
  const {options} = useRepositoryOptions();
  const [performQuery, {data}] = useLazyQuery<RunsSearchSpaceQuery>(RUNS_SEARCH_SPACE_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const suggestions = searchSuggestionsForRuns(options, data?.pipelineRunTags, enabledFilters);

  const search = tokenizedValuesFromStringArray(tokensAsStringArray(tokens), suggestions);

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

  const onFocus = React.useCallback(() => performQuery(), [performQuery]);

  return (
    <TokenizingField
      values={search}
      onChange={(values) => onChange(values as RunFilterToken[])}
      onFocus={onFocus}
      suggestionProviders={suggestions}
      suggestionProvidersFilter={suggestionProvidersFilter}
      loading={loading}
    />
  );
};

const RUNS_SEARCH_SPACE_QUERY = gql`
  query RunsSearchSpaceQuery {
    pipelineRunTags {
      key
      values
    }
  }
`;
