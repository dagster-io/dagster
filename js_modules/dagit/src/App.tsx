import * as React from "react";

import { BrowserRouter, Redirect, Route, Switch } from "react-router-dom";

import CustomAlertProvider from "./CustomAlertProvider";
import { NonIdealState } from "@blueprintjs/core";
import { PipelineExecutionRoot } from "./execute/PipelineExecutionRoot";
import { PipelineExecutionSetupRoot } from "./execute/PipelineExecutionSetupRoot";
import { PipelineNamesContext } from "./PipelineNamesContext";
import { PipelineExplorerRoot } from "./PipelineExplorerRoot";
import { PipelineOverviewRoot } from "./pipelines/PipelineOverviewRoot";
import PythonErrorInfo from "./PythonErrorInfo";
import { RootPipelinesQuery } from "./types/RootPipelinesQuery";
import { RunRoot } from "./runs/RunRoot";
import { RunsRoot } from "./runs/RunsRoot";
import { SolidsRoot } from "./solids/SolidsRoot";
import SchedulesRoot from "./schedules/SchedulesRoot";
import { ScheduleRoot } from "./schedules/ScheduleRoot";
import { AssetsRoot } from "./assets/AssetsRoot";
import { LeftNav } from "./nav/LeftNav";
import { PipelineNav } from "./nav/PipelineNav";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";
import { FeatureFlagsRoot } from "./FeatureFlagsRoot";
import { InstanceDetailsRoot } from "./InstanceDetailsRoot";
import { SolidDetailsRoot } from "./solids/SolidDetailsRoot";

function extractData(result?: RootPipelinesQuery) {
  if (!result || !result.pipelinesOrError) {
    return { pipelines: [], error: null };
  }
  if (result.pipelinesOrError.__typename === "PipelineConnection") {
    return {
      pipelines: result.pipelinesOrError.nodes.map(p => p.name),
      error: null
    };
  } else {
    return { pipelines: [], error: result.pipelinesOrError };
  }
}

const AppRoutes = () => (
  <Switch>
    <Route path="/flags" component={FeatureFlagsRoot} />
    <Route path="/runs/all/:runId" component={RunRoot} />
    <Route path="/runs" component={RunsRoot} exact={true} />
    <Route path="/runs/:pipelineName/:runId" component={RunRoot} />
    <Route path="/solid/:name" component={SolidDetailsRoot} />
    <Route path="/solids/:name?" component={SolidsRoot} />
    <Route path="/schedules/:scheduleName" component={ScheduleRoot} />
    <Route path="/schedules" component={SchedulesRoot} />
    <Route path="/assets" component={AssetsRoot} exact={true} />
    <Route path="/assets/:assetSelector" component={AssetsRoot} />
    <Route path="/instance" component={InstanceDetailsRoot} />

    <Route
      path="/pipeline"
      render={() => (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            width: "100%",
            height: "100%"
          }}
        >
          <PipelineNav />
          <Switch>
            <Route
              path="/pipeline/:pipelineSelector/overview"
              component={PipelineOverviewRoot}
            />
            <Route
              path="/pipeline/:pipelineSelector/playground/setup"
              component={PipelineExecutionSetupRoot}
            />
            <Route
              path="/pipeline/:pipelineSelector/playground"
              component={PipelineExecutionRoot}
            />
            {/* Capture solid subpath in a regex match */}
            <Route path="/pipeline/(/?.*)" component={PipelineExplorerRoot} />
          </Switch>
        </div>
      )}
    />

    <PipelineNamesContext.Consumer>
      {names =>
        names.length ? (
          <Redirect to={`/pipeline/${names[0]}/`} />
        ) : (
          <Route render={() => <NonIdealState title="No pipelines" />} />
        )
      }
    </PipelineNamesContext.Consumer>
  </Switch>
);

export const App: React.FunctionComponent = () => {
  const result = useQuery<RootPipelinesQuery>(ROOT_PIPELINES_QUERY, {
    fetchPolicy: "cache-and-network"
  });
  const { pipelines, error } = extractData(result.data);

  return (
    <div style={{ display: "flex", height: "100%" }}>
      <BrowserRouter>
        <PipelineNamesContext.Provider value={pipelines || []}>
          <LeftNav />
          {error ? (
            <PythonErrorInfo
              contextMsg={`${error.__typename} encountered when loading pipelines:`}
              error={error}
              centered={true}
            />
          ) : (
            <>
              <AppRoutes />
              <CustomAlertProvider />
            </>
          )}
        </PipelineNamesContext.Provider>
      </BrowserRouter>
    </div>
  );
};

export const ROOT_PIPELINES_QUERY = gql`
  query RootPipelinesQuery {
    pipelinesOrError {
      __typename
      ...PythonErrorFragment
      ... on PipelineConnection {
        nodes {
          name
        }
      }
    }
  }

  ${PythonErrorInfo.fragments.PythonErrorFragment}
`;
