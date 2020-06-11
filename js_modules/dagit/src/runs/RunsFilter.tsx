import * as React from "react";
import { useQuery, QueryResult } from "react-apollo";
import { RunsSearchSpaceQuery } from "./types/RunsSearchSpaceQuery";
import {
  DagsterRepositoryContext,
  useRepositorySelector
} from "../DagsterRepositoryContext";
import {
  TokenizingField,
  TokenizingFieldValue,
  SuggestionProvider,
  stringFromValue,
  tokenizedValuesFromString
} from "../TokenizingField";
import gql from "graphql-tag";

export const RUN_PROVIDERS_EMPTY = [
  {
    token: "id",
    values: () => []
  },
  {
    token: "status",
    values: () => []
  },
  {
    token: "pipeline",
    values: () => []
  },
  {
    token: "tag",
    values: () => []
  }
];

function searchSuggestionsForRuns(
  result?: QueryResult<RunsSearchSpaceQuery>,
  enabledFilters?: string[]
): SuggestionProvider[] {
  const tags = (result && result.data && result.data.pipelineRunTags) || [];
  const pipelineNames =
    result?.data?.repositoryOrError?.__typename === "Repository"
      ? result.data.repositoryOrError.pipelines.map(n => n.name)
      : [];

  const suggestions = [
    {
      token: "id",
      values: () => []
    },
    {
      token: "status",
      values: () => ["NOT_STARTED", "STARTED", "SUCCESS", "FAILURE", "MANAGED"]
    },
    {
      token: "pipeline",
      values: () => pipelineNames
    },
    {
      token: "tag",
      values: () => {
        const all: string[] = [];
        tags
          .sort((a, b) => a.key.localeCompare(b.key))
          .forEach(t => t.values.forEach(v => all.push(`${t.key}=${v}`)));
        return all;
      }
    }
  ];

  if (enabledFilters) {
    return suggestions.filter(x => enabledFilters.includes(x.token));
  }

  return suggestions;
}

interface RunsFilterProps {
  loading?: boolean;
  tokens: TokenizingFieldValue[];
  onChange: (tokens: TokenizingFieldValue[]) => void;
  enabledFilters?: string[];
}

export const RunsFilter: React.FunctionComponent<RunsFilterProps> = ({
  loading,
  tokens,
  onChange,
  enabledFilters
}) => {
  const { repositoryLocation, repository } = React.useContext(
    DagsterRepositoryContext
  );
  const repositorySelector = useRepositorySelector();
  const suggestions = searchSuggestionsForRuns(
    useQuery<RunsSearchSpaceQuery>(RUNS_SEARCH_SPACE_QUERY, {
      fetchPolicy: "cache-and-network",
      skip: !repository || !repositoryLocation,
      variables: { repositorySelector }
    }),
    enabledFilters
  );

  const search = tokenizedValuesFromString(
    stringFromValue(tokens),
    suggestions
  );

  const suggestionProvidersFilter = (
    suggestionProviders: SuggestionProvider[],
    values: TokenizingFieldValue[]
  ) => {
    const tokens: string[] = [];
    for (const { token } of values) {
      if (token) {
        tokens.push(token);
      }
    }

    // If id is set, then no other filters can be set
    if (tokens.includes("id")) {
      return [];
    }

    // Can only have one filter value for pipeline, status, or id
    const limitedTokens = new Set<string>(["id", "pipeline", "status"]);
    const presentLimitedTokens = tokens.filter(token =>
      limitedTokens.has(token)
    );

    return suggestionProviders.filter(
      provider => !presentLimitedTokens.includes(provider.token)
    );
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

export const RUNS_SEARCH_SPACE_QUERY = gql`
  query RunsSearchSpaceQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        pipelines {
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
