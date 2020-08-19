import * as React from "react";

import { BrowserRouter, Redirect, Route, Switch } from "react-router-dom";

import CustomAlertProvider from "./CustomAlertProvider";
import { NonIdealState, Spinner } from "@blueprintjs/core";
import { PipelineExecutionRoot } from "./execute/PipelineExecutionRoot";
import { PipelineExecutionSetupRoot } from "./execute/PipelineExecutionSetupRoot";
import { PipelineExplorerRoot } from "./PipelineExplorerRoot";
import { PipelineOverviewRoot } from "./pipelines/PipelineOverviewRoot";
import { PipelinePartitionsRoot } from "./partitions/PipelinePartitionsRoot";
import { PipelineRunsRoot } from "./PipelineRunsRoot";
import PythonErrorInfo from "./PythonErrorInfo";
import { RunRoot } from "./runs/RunRoot";
import { RunsRoot } from "./runs/RunsRoot";
import { SolidsRoot } from "./solids/SolidsRoot";
import { SchedulerRoot } from "./schedules/SchedulerRoot";
import { SchedulesRoot } from "./schedules/SchedulesRoot";
import { ScheduleRoot } from "./schedules/ScheduleRoot";
import { AssetsRoot } from "./assets/AssetsRoot";
import { LeftNav } from "./nav/LeftNav";
import { PipelineNav } from "./nav/PipelineNav";
import { FeatureFlagsRoot } from "./FeatureFlagsRoot";
import { InstanceDetailsRoot } from "./InstanceDetailsRoot";
import { SolidDetailsRoot } from "./solids/SolidDetailsRoot";
import {
  DagsterRepositoryContext,
  useRepositoryOptions,
  useCurrentRepositoryState
} from "./DagsterRepositoryContext";
import { CustomTooltipProvider } from "./CustomTooltipProvider";
import { APP_PATH_PREFIX } from "./DomUtils";
import { CustomConfirmationProvider } from "./CustomConfirmationProvider";

const AppRoutes = () => (
  <Switch>
    <Route path="/flags" component={FeatureFlagsRoot} />
    <Route path="/runs" component={RunsRoot} exact={true} />
    <Route path="/solid/:name" component={SolidDetailsRoot} />
    <Route path="/solids/:name?" component={SolidsRoot} />
    <Route path="/scheduler" component={SchedulerRoot} exact={true} />
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
            <Route path="/pipeline/:pipelinePath/overview" component={PipelineOverviewRoot} />
            <Route
              path="/pipeline/:pipelinePath/playground/setup"
              component={PipelineExecutionSetupRoot}
            />
            <Route path="/pipeline/:pipelinePath/playground" component={PipelineExecutionRoot} />
            <Route path="/pipeline/:pipelinePath/runs/:runId" component={RunRoot} />

            <Route path="/pipeline/:pipelinePath/runs" component={PipelineRunsRoot} />
            <Route path="/pipeline/:pipelinePath/partitions" component={PipelinePartitionsRoot} />
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
  const { options, error } = useRepositoryOptions();
  const [repo, setRepo] = useCurrentRepositoryState(options);

  return (
    <div style={{ display: "flex", height: "100%" }}>
      <BrowserRouter basename={APP_PATH_PREFIX}>
        <LeftNav options={options} repo={repo} setRepo={setRepo} />
        {error ? (
          <PythonErrorInfo
            contextMsg={`${error.__typename} encountered when loading pipelines:`}
            error={error}
            centered={true}
          />
        ) : repo ? (
          <CustomConfirmationProvider>
            <DagsterRepositoryContext.Provider value={repo}>
              <AppRoutes />
              <CustomTooltipProvider />
              <CustomAlertProvider />
            </DagsterRepositoryContext.Provider>
          </CustomConfirmationProvider>
        ) : (
          <NonIdealState icon={<Spinner size={24} />} />
        )}
      </BrowserRouter>
    </div>
  );
};
