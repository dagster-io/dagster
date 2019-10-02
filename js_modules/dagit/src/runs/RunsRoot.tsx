import * as React from "react";

import Loading from "../Loading";
import * as querystring from "query-string";
import { RouteComponentProps } from "react-router";
import { RunTable } from "./RunTable";
import { RunsRootQuery, RunsRootQueryVariables } from "./types/RunsRootQuery";
import { RunsSearchSpaceQuery } from "./types/RunsSearchSpaceQuery";

import gql from "graphql-tag";
import { __RouterContext as RouterContext } from "react-router";
import { useQuery, QueryResult } from "react-apollo";
import { IconNames } from "@blueprintjs/icons";
import { NonIdealState, Button } from "@blueprintjs/core";
import { ScrollContainer, Header } from "../ListComponents";
import {
  TokenizingField,
  TokenizingFieldValue,
  SuggestionProvider,
  tokenizedValuesListFromString,
  stringFromValue
} from "../TokenizingField";
import styled from "styled-components";
import { PipelineRunsSelector, PipelineRunStatus } from "../types/globalTypes";

const PAGE_SIZE = 50;

function searchSuggestionsForRuns(
  result?: QueryResult<RunsSearchSpaceQuery>
): SuggestionProvider[] {
  // optional chaining cannot come soon enough
  const tags = (result && result.data && result.data.pipelineRunTags) || [];
  const pipelineNames =
    (result &&
      result.data &&
      result.data.pipelinesOrError &&
      result.data.pipelinesOrError.__typename === "PipelineConnection" &&
      result.data.pipelinesOrError.nodes.map(n => n.name)) ||
    [];

  return [
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
}

function runsSelectorForSearchTokens(search: TokenizingFieldValue[]) {
  if (!search[0]) return {};

  const obj: PipelineRunsSelector = {};

  for (const item of search) {
    if (item.token === "pipeline") {
      obj.pipeline = item.value;
    } else if (item.token === "id") {
      obj.runId = item.value;
    } else if (item.token === "status") {
      obj.status = item.value as PipelineRunStatus;
    } else if (item.token === "tag") {
      const [key, value] = item.value.split("=");
      obj.tagKey = key;
      obj.tagValue = value;
    }
  }

  return obj;
}

export const RunsRoot: React.FunctionComponent<RouteComponentProps> = ({
  location
}) => {
  const router = React.useContext(RouterContext);
  const qs = querystring.parse(location.search);

  const suggestions = searchSuggestionsForRuns(
    useQuery<RunsSearchSpaceQuery>(RUNS_SEARCH_SPACE_QUERY, {
      fetchPolicy: "cache-and-network"
    })
  );

  const search = tokenizedValuesListFromString(
    (qs.q as string) || "",
    searchSuggestionsForRuns()
  );
  const setSearch = (search: TokenizingFieldValue[]) => {
    // Note: changing search also clears the cursor so you're back on page 1
    router.history.push({
      search: `?${querystring.stringify({
        ...qs,
        q: stringFromValue(search),
        cursor: undefined
      })}`
    });
  };
  const cursor = (qs.cursor as string) || undefined;
  const setCursor = (cursor: string) => {
    router.history.push({
      search: `?${querystring.stringify({ ...qs, cursor })}`
    });
  };

  const queryResult = useQuery<RunsRootQuery, RunsRootQueryVariables>(
    RUNS_ROOT_QUERY,
    {
      fetchPolicy: "cache-and-network",
      pollInterval: 15 * 1000,
      partialRefetch: true,
      variables: {
        cursor: cursor,
        limit: PAGE_SIZE + 1,
        selector: runsSelectorForSearchTokens(search)
      }
    }
  );

  return (
    <ScrollContainer>
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between"
        }}
      >
        <Header>{`Runs`}</Header>
        <Filters>
          <TokenizingField
            values={search}
            maxValues={1}
            onChange={search => setSearch(search)}
            suggestionProviders={suggestions}
          />
        </Filters>
      </div>

      <Loading queryResult={queryResult}>
        {({ pipelineRunsOrError }) => {
          if (
            pipelineRunsOrError.__typename ===
            "InvalidPipelineRunsSelectorError"
          ) {
            return (
              <NonIdealState
                icon={IconNames.ERROR}
                title="Query Error"
                description={pipelineRunsOrError.message}
              />
            );
          }

          const runs = pipelineRunsOrError.results;
          const displayed = runs.slice(0, PAGE_SIZE);
          const hasNextPage = runs.length === PAGE_SIZE + 1;

          return (
            <>
              <RunTable runs={displayed} />
              <div style={{ textAlign: "center" }}>
                {hasNextPage && (
                  <Button
                    rightIcon={IconNames.ARROW_RIGHT}
                    onClick={() =>
                      setCursor(displayed[displayed.length - 1].runId)
                    }
                  >
                    Show More
                  </Button>
                )}
              </div>
            </>
          );
        }}
      </Loading>
    </ScrollContainer>
  );
};

export const RUNS_SEARCH_SPACE_QUERY = gql`
  query RunsSearchSpaceQuery {
    pipelinesOrError {
      __typename
      ... on PipelineConnection {
        nodes {
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

export const RUNS_ROOT_QUERY = gql`
  query RunsRootQuery(
    $limit: Int
    $cursor: String
    $selector: PipelineRunsSelector!
  ) {
    pipelineRunsOrError(limit: $limit, cursor: $cursor, params: $selector) {
      ... on PipelineRuns {
        results {
          ...RunTableRunFragment
        }
      }
      ... on InvalidPipelineRunsSelectorError {
        message
      }
    }
  }

  ${RunTable.fragments.RunTableRunFragment}
`;

const Filters = styled.div`
  float: right;
  display: flex;
  align-items: center;
  margin-bottom: 14px;
`;
