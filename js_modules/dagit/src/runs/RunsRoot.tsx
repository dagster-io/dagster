import * as React from "react";

import Loading from "../Loading";
import * as querystring from "query-string";
import { RouteComponentProps } from "react-router";
import { RunTable } from "./RunTable";
import { RunsRootQuery, RunsRootQueryVariables } from "./types/RunsRootQuery";
import { RunsFilter, RUN_PROVIDERS_EMPTY } from "./RunsFilter";

import gql from "graphql-tag";
import { __RouterContext as RouterContext } from "react-router";
import { useQuery } from "react-apollo";
import { IconNames } from "@blueprintjs/icons";
import { NonIdealState, Button } from "@blueprintjs/core";
import { ScrollContainer, Header } from "../ListComponents";
import {
  TokenizingFieldValue,
  tokenizedValuesFromString,
  stringFromValue
} from "../TokenizingField";
import styled from "styled-components/macro";
import { PipelineRunsFilter, PipelineRunStatus } from "../types/globalTypes";

const PAGE_SIZE = 25;

export const RunsQueryVariablesContext = React.createContext<
  RunsRootQueryVariables
>({ filter: {} });

function runsFilterForSearchTokens(search: TokenizingFieldValue[]) {
  if (!search[0]) return {};

  const obj: PipelineRunsFilter = {};

  for (const item of search) {
    if (item.token === "pipeline") {
      obj.pipelineName = item.value;
    } else if (item.token === "id") {
      obj.runId = item.value;
    } else if (item.token === "status") {
      obj.status = item.value as PipelineRunStatus;
    } else if (item.token === "tag") {
      const [key, value] = item.value.split("=");
      if (obj.tags) {
        obj.tags.push({ key, value });
      } else {
        obj.tags = [{ key, value }];
      }
    }
  }

  return obj;
}

export const RunsRoot: React.FunctionComponent<RouteComponentProps> = ({
  location
}) => {
  const { history } = React.useContext(RouterContext);
  const qs = querystring.parse(location.search);

  const [cursorStack, setCursorStack] = React.useState<string[]>([]);
  const cursor = (qs.cursor as string) || undefined;

  const setCursor = (cursor: string | undefined) => {
    history.push({ search: `?${querystring.stringify({ ...qs, cursor })}` });
  };
  const popCursor = () => {
    const nextStack = [...cursorStack];
    setCursor(nextStack.pop());
    setCursorStack(nextStack);
  };
  const pushCursor = (nextCursor: string) => {
    if (cursor) setCursorStack([...cursorStack, cursor]);
    setCursor(nextCursor);
  };

  const filterTokens = tokenizedValuesFromString(
    (qs.q as string) || "",
    RUN_PROVIDERS_EMPTY
  );

  const setFilterTokens = (tokens: TokenizingFieldValue[]) => {
    // Note: changing search also clears the cursor so you're back on page 1
    setCursorStack([]);
    const params = { ...qs, q: stringFromValue(tokens), cursor: undefined };
    history.push({ search: `?${querystring.stringify(params)}` });
  };

  const queryVars: RunsRootQueryVariables = {
    cursor: cursor,
    limit: PAGE_SIZE + 1,
    filter: runsFilterForSearchTokens(filterTokens)
  };
  const queryResult = useQuery<RunsRootQuery, RunsRootQueryVariables>(
    RUNS_ROOT_QUERY,
    {
      fetchPolicy: "cache-and-network",
      pollInterval: 15 * 1000,
      partialRefetch: true,
      variables: queryVars
    }
  );

  return (
    <RunsQueryVariablesContext.Provider value={queryVars}>
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
            <RunsFilter
              tokens={filterTokens}
              onChange={setFilterTokens}
              loading={queryResult.loading}
            />
          </Filters>
        </div>

        <Loading queryResult={queryResult} allowStaleData={true}>
          {({ pipelineRunsOrError }) => {
            if (pipelineRunsOrError.__typename !== "PipelineRuns") {
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
            const hasPrevPage = !!cursor;
            const hasNextPage = runs.length === PAGE_SIZE + 1;
            return (
              <>
                <RunTable runs={displayed} onSetFilter={setFilterTokens} />
                <div style={{ textAlign: "center" }}>
                  <Button
                    style={{
                      visibility: hasPrevPage ? "initial" : "hidden",
                      marginRight: 4
                    }}
                    icon={IconNames.ARROW_LEFT}
                    onClick={() => popCursor()}
                  >
                    Prev Page
                  </Button>
                  <Button
                    style={{
                      visibility: hasNextPage ? "initial" : "hidden",
                      marginLeft: 4
                    }}
                    rightIcon={IconNames.ARROW_RIGHT}
                    onClick={() =>
                      pushCursor(displayed[displayed.length - 1].runId)
                    }
                  >
                    Next Page
                  </Button>
                </div>
              </>
            );
          }}
        </Loading>
      </ScrollContainer>
    </RunsQueryVariablesContext.Provider>
  );
};

export const RUNS_ROOT_QUERY = gql`
  query RunsRootQuery(
    $limit: Int
    $cursor: String
    $filter: PipelineRunsFilter!
  ) {
    pipelineRunsOrError(limit: $limit, cursor: $cursor, filter: $filter) {
      ... on PipelineRuns {
        results {
          ...RunTableRunFragment
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ... on PythonError {
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
