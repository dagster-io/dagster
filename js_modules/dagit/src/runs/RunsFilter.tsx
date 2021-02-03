import {gql, QueryResult, useQuery} from '@apollo/client';
import * as React from 'react';

import {useQueryPersistedState} from 'src/hooks/useQueryPersistedState';
import {RunsSearchSpaceQuery} from 'src/runs/types/RunsSearchSpaceQuery';
import {PipelineRunStatus, PipelineRunsFilter} from 'src/types/globalTypes';
import {
  SuggestionProvider,
  TokenizingField,
  TokenizingFieldValue,
  stringFromValue,
  tokenizedValuesFromString,
} from 'src/ui/TokenizingField';
import {useActiveRepo, useRepositorySelector} from 'src/workspace/WorkspaceContext';

export type RunFilterTokenType = 'id' | 'status' | 'pipeline' | 'snapshotId' | 'tag';

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
  return useQueryPersistedState<TokenizingFieldValue[]>({
    encode: (tokens) => ({q: stringFromValue(tokens), cursor: undefined}),
    decode: ({q = ''}) =>
      tokenizedValuesFromString(q, RUN_PROVIDERS_EMPTY).filter(
        (t) =>
          !t.token || !enabledFilters || enabledFilters.includes(t.token as RunFilterTokenType),
      ),
  });
}

export function runsFilterForSearchTokens(search: TokenizingFieldValue[]) {
  if (!search[0]) {
    return {};
  }

  const obj: PipelineRunsFilter = {};

  for (const item of search) {
    if (item.token === 'pipeline') {
      obj.pipelineName = item.value;
    } else if (item.token === 'id') {
      obj.runIds = [item.value];
    } else if (item.token === 'status') {
      if (!obj.statuses) {
        obj.statuses = [];
      }
      obj.statuses.push(item.value as PipelineRunStatus);
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
  result?: QueryResult<RunsSearchSpaceQuery>,
  enabledFilters?: RunFilterTokenType[],
): SuggestionProvider[] {
  const tags = result?.data?.pipelineRunTags || [];
  const pipelineNames =
    result?.data?.repositoryOrError?.__typename === 'Repository'
      ? result.data.repositoryOrError.pipelines.map((n) => n.name)
      : [];

  const suggestions: {token: RunFilterTokenType; values: () => string[]}[] = [
    {
      token: 'id',
      values: () => [],
    },
    {
      token: 'status',
      values: () => Object.keys(PipelineRunStatus),
    },
    {
      token: 'pipeline',
      values: () => pipelineNames,
    },
    {
      token: 'tag',
      values: () => {
        const all: string[] = [];
        [...tags]
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

interface RunsFilterProps {
  loading?: boolean;
  tokens: TokenizingFieldValue[];
  onChange: (tokens: TokenizingFieldValue[]) => void;
  enabledFilters?: RunFilterTokenType[];
}

export const RunsFilter: React.FunctionComponent<RunsFilterProps> = ({
  loading,
  tokens,
  onChange,
  enabledFilters,
}) => {
  const activeRepo = useActiveRepo();
  const repositorySelector = useRepositorySelector();
  const suggestions = searchSuggestionsForRuns(
    useQuery<RunsSearchSpaceQuery>(RUNS_SEARCH_SPACE_QUERY, {
      fetchPolicy: 'cache-and-network',
      skip: !activeRepo,
      variables: activeRepo ? {repositorySelector} : {},
    }),
    enabledFilters,
  );

  const search = tokenizedValuesFromString(stringFromValue(tokens), suggestions);

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
    const limitedTokens = new Set<string>(['id', 'pipeline', 'snapshotId']);
    const presentLimitedTokens = tokens.filter((token) => limitedTokens.has(token));

    return suggestionProviders.filter((provider) => !presentLimitedTokens.includes(provider.token));
  };

  return (
    <TokenizingField
      values={search}
      onChange={onChange}
      suggestionProviders={suggestions}
      suggestionProvidersFilter={suggestionProvidersFilter}
      loading={loading}
    />
  );
};

const RUNS_SEARCH_SPACE_QUERY = gql`
  query RunsSearchSpaceQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        pipelines {
          id
          name
        }
      }
    }
    pipelineRunTags {
      key
      values
    }
  }
`;
