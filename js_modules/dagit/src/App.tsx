import * as React from "react";

import { BrowserRouter, Redirect, Route, Switch } from "react-router-dom";

import CustomAlertProvider from "./CustomAlertProvider";
import { NonIdealState } from "@blueprintjs/core";
import { PipelineExecutionRoot } from "./execute/PipelineExecutionRoot";
import { PipelineExecutionSetupRoot } from "./execute/PipelineExecutionSetupRoot";
import { PipelineNamesContext } from "./PipelineNamesContext";
import PipelineExplorerRoot from "./PipelineExplorerRoot";
import PythonErrorInfo from "./PythonErrorInfo";
import { RootPipelinesQuery } from "./types/RootPipelinesQuery";
import { RunRoot } from "./runs/RunRoot";
import { RunsRoot } from "./runs/RunsRoot";
import { SolidsRoot } from "./solids/SolidsRoot";
import SchedulesRoot from "./schedules/SchedulesRoot";
import { ScheduleRoot } from "./schedules/ScheduleRoot";
import { LeftNav } from "./LeftNav";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";

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
    <Route path="/runs/all/:runId" component={RunRoot} />
    <Route path="/runs/:pipelineName/:runId" component={RunRoot} />
    <Route path="/runs" component={RunsRoot} exact={true} />
    <Route path="/solids/:name?" component={SolidsRoot} />

    <Route path="/playground/setup" component={PipelineExecutionSetupRoot} />
    <Route path="/playground" component={PipelineExecutionRoot} />
    {/* Capture solid subpath in a regex match */}
    <Route path="/pipeline/(/?.*)" component={PipelineExplorerRoot} />

    <Route path="/schedules" component={SchedulesRoot} />
    <Route path="/schedules/:scheduleName" component={ScheduleRoot} />

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
    <BrowserRouter>
      {error ? (
        <PythonErrorInfo
          contextMsg={`${error.__typename} encountered when loading pipelines:`}
          error={error}
          centered={true}
        />
      ) : (
        <PipelineNamesContext.Provider value={pipelines}>
          <div style={{ display: "flex", height: "100%" }}>
            <LeftNav />
            <AppRoutes />
            <CustomAlertProvider />
          </div>
        </PipelineNamesContext.Provider>
      )}
    </BrowserRouter>
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
