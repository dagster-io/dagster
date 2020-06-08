import * as React from "react";

import { BrowserRouter, Redirect, Route, Switch } from "react-router-dom";

import CustomAlertProvider from "./CustomAlertProvider";
import { NonIdealState, Spinner } from "@blueprintjs/core";
import { PipelineExecutionRoot } from "./execute/PipelineExecutionRoot";
import { PipelineExecutionSetupRoot } from "./execute/PipelineExecutionSetupRoot";
import { PipelineExplorerRoot } from "./PipelineExplorerRoot";
import { PipelineOverviewRoot } from "./pipelines/PipelineOverviewRoot";
import PythonErrorInfo from "./PythonErrorInfo";
import { RootRepositoriesQuery } from "./types/RootRepositoriesQuery";
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
import {
  DagsterRepositoryContext,
  REPOSITORY_LOCATION_FRAGMENT
} from "./DagsterRepositoryContext";
import { CustomTooltipProvider } from "./CustomTooltipProvider";

const extractData = (result: RootRepositoriesQuery | undefined) => {
  if (!result?.repositoryLocationsOrError) {
    return {
      repositoryContext: {
        repositoryLocation: undefined,
        repository: undefined
      }
    };
  }

  if (result.repositoryLocationsOrError.__typename === "PythonError") {
    return {
      error: result.repositoryLocationsOrError,
      repositoryContext: {
        repositoryLocation: undefined,
        repository: undefined
      }
    };
  }

  const [repositoryLocation] = result.repositoryLocationsOrError.nodes || [];
  const [repository] = repositoryLocation?.repositories || [];
  const repositoryContext = { repositoryLocation, repository };
  return { repositoryContext };
};

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
    <Route path="/assets/(/?.*)" component={AssetsRoot} />
    <Route path="/instance" component={InstanceDetailsRoot} />

    <Route
      path="/pipeline"
      render={() => (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            minWidth: 0,
            width: "100%",
            height: "100%"
          }}
        >
          <PipelineNav />
          <Switch>
            <Route
              path="/pipeline/:pipelinePath/overview"
              component={PipelineOverviewRoot}
            />
            <Route
              path="/pipeline/:pipelinePath/playground/setup"
              component={PipelineExecutionSetupRoot}
            />
            <Route
              path="/pipeline/:pipelinePath/playground"
              component={PipelineExecutionRoot}
            />
            {/* Capture solid subpath in a regex match */}
            <Route path="/pipeline/(/?.*)" component={PipelineExplorerRoot} />
          </Switch>
        </div>
      )}
    />

    <DagsterRepositoryContext.Consumer>
      {context =>
        context.repository?.pipelines.length ? (
          <Redirect to={`/pipeline/${context.repository.pipelines[0].name}/`} />
        ) : (
          <Route render={() => <NonIdealState title="No pipelines" />} />
        )
      }
    </DagsterRepositoryContext.Consumer>
  </Switch>
);

export const App: React.FunctionComponent = () => {
  const result = useQuery<RootRepositoriesQuery>(ROOT_REPOSITORIES_QUERY, {
    fetchPolicy: "cache-and-network"
  });

  const { repositoryContext, error } = extractData(result?.data);
  const { repositoryLocation, repository } = repositoryContext;

  return (
    <div style={{ display: "flex", height: "100%" }}>
      <BrowserRouter>
        <DagsterRepositoryContext.Provider value={repositoryContext}>
          <LeftNav />
          {error ? (
            <PythonErrorInfo
              contextMsg={`${error.__typename} encountered when loading pipelines:`}
              error={error}
              centered={true}
            />
          ) : repositoryLocation && repository ? (
            <>
              <AppRoutes />
              <CustomTooltipProvider />
              <CustomAlertProvider />
            </>
          ) : (
            <NonIdealState icon={<Spinner size={24} />} />
          )}
        </DagsterRepositoryContext.Provider>
      </BrowserRouter>
    </div>
  );
};

export const ROOT_REPOSITORIES_QUERY = gql`
  query RootRepositoriesQuery {
    repositoryLocationsOrError {
      __typename
      ... on RepositoryLocationConnection {
        nodes {
          ...RepositoryLocationFragment
        }
      }
      ...PythonErrorFragment
    }
  }
  ${REPOSITORY_LOCATION_FRAGMENT}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
`;
