import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import { BrowserRouter, Switch, Route } from "react-router-dom";

import { TopNav } from "./TopNav";
import PythonErrorInfo from "./PythonErrorInfo";
import CustomAlertProvider from "./CustomAlertProvider";
import { RootPipelinesQuery } from "./types/RootPipelinesQuery";
import { PipelineExecutionRoot } from "./execute/PipelineExecutionRoot";
import { PipelineExecutionSetupRoot } from "./execute/PipelineExecutionSetupRoot";
import RunRoot from "./runs/RunRoot";
import RunsRoot from "./runs/RunsRoot";
import PipelineExplorerRoot from "./PipelineExplorerRoot";
import { NonIdealState } from "@blueprintjs/core";

function extractData(result?: RootPipelinesQuery) {
  if (!result || !result.pipelinesOrError) {
    return { pipelines: [], error: null };
  }
  if (result.pipelinesOrError.__typename === "PipelineConnection") {
    return { pipelines: result.pipelinesOrError.nodes, error: null };
  } else {
    return { pipelines: [], error: result.pipelinesOrError };
  }
}

const AppRoutes = () => (
  <Switch>
    <Route path="/runs/:runId" component={RunRoot} />
    <Route path="/runs" component={RunsRoot} exact={true} />
    <Route
      path="/execute/:pipelineName/setup"
      component={PipelineExecutionSetupRoot}
    />
    <Route path="/execute/:pipelineName" component={PipelineExecutionRoot} />
    <Route
      path="/explore/:pipelineName/:rest?"
      component={PipelineExplorerRoot}
    />
    <Route
      render={() => (
        <NonIdealState
          title="No pipeline selected"
          description="Select a pipeline in the navbar"
        />
      )}
    />
  </Switch>
);

export default class App extends React.Component {
  public render() {
    return (
      <BrowserRouter>
        <Query query={ROOT_PIPELINES_QUERY} fetchPolicy="cache-and-network">
          {(queryResult: QueryResult<RootPipelinesQuery, any>) => {
            const { pipelines, error } = extractData(queryResult.data);
            return (
              <>
                <TopNav pipelines={pipelines} />
                {error ? (
                  <PythonErrorInfo
                    contextMsg={`${error.__typename} encountered when loading pipelines:`}
                    error={error}
                    centered={true}
                  />
                ) : (
                  <AppRoutes />
                )}
                <CustomAlertProvider />
              </>
            );
          }}
        </Query>
      </BrowserRouter>
    );
  }
}

export const ROOT_PIPELINES_QUERY = gql`
  query RootPipelinesQuery {
    pipelinesOrError {
      __typename
      ... on PythonError {
        message
        stack
      }
      ... on InvalidDefinitionError {
        message
        stack
      }
      ... on PipelineConnection {
        nodes {
          ...TopNavPipelinesFragment
        }
      }
    }
  }

  ${TopNav.fragments.TopNavPipelinesFragment}
`;
