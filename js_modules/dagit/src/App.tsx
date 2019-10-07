import * as React from "react";

import { BrowserRouter, Redirect, Route, Switch } from "react-router-dom";

import CustomAlertProvider from "./CustomAlertProvider";
import { NonIdealState } from "@blueprintjs/core";
import { PipelineExecutionRoot } from "./execute/PipelineExecutionRoot";
import { PipelineExecutionSetupRoot } from "./execute/PipelineExecutionSetupRoot";
import PipelineExplorerRoot from "./PipelineExplorerRoot";
import PythonErrorInfo from "./PythonErrorInfo";
import { RootPipelinesQuery } from "./types/RootPipelinesQuery";
import { RunRoot } from "./runs/RunRoot";
import { RunsRoot } from "./runs/RunsRoot";
import SchedulesRoot from "./schedules/SchedulesRoot";
import { TopNav } from "./TopNav";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";

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
    <Route path="/p/:pipelineName/runs/:runId" component={RunRoot} />
    <Redirect
      from="/p/:pipelineName"
      exact={true}
      to="/p/:pipelineName/explore"
    />

    <Route
      path="/p/:pipelineName/execute/setup"
      component={PipelineExecutionSetupRoot}
    />
    <Route path="/p/:pipelineName/execute" component={PipelineExecutionRoot} />
    {/* Capture solid subpath in a regex match */}
    <Route
      path="/p/:pipelineName/explore(/?.*)"
      component={PipelineExplorerRoot}
    />
    {/* Legacy redirects */}
    <Redirect
      from="/execute/:pipelineName/setup"
      to="/p/:pipelineName/execute/setup"
    />
    <Redirect from="/execute/:pipelineName" to="/p/:pipelineName/execute" />
    <Redirect
      from="/explore/:pipelineName/:rest?"
      to="/p/:pipelineName/explore/:rest?"
    />
    {/* Index default */}
    <Route path="/scheduler/:rest?" component={SchedulesRoot} />
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

export const App: React.FunctionComponent = () => {
  const result = useQuery<RootPipelinesQuery>(ROOT_PIPELINES_QUERY, {
    fetchPolicy: "cache-and-network"
  });
  const { pipelines, error } = extractData(result.data);

  return (
    <BrowserRouter>
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
    </BrowserRouter>
  );
};

export const ROOT_PIPELINES_QUERY = gql`
  query RootPipelinesQuery {
    pipelinesOrError {
      __typename
      ... on PythonError {
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
