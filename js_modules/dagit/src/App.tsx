import {NonIdealState, Spinner} from '@blueprintjs/core';
import * as React from 'react';
import {BrowserRouter, Redirect, Route, Switch} from 'react-router-dom';

import CustomAlertProvider from 'src/CustomAlertProvider';
import {CustomConfirmationProvider} from 'src/CustomConfirmationProvider';
import {CustomTooltipProvider} from 'src/CustomTooltipProvider';
import {
  DagsterRepositoryContext,
  useCurrentRepositoryState,
  useRepositoryOptions,
} from 'src/DagsterRepositoryContext';
import {APP_PATH_PREFIX} from 'src/DomUtils';
import {FeatureFlagsRoot} from 'src/FeatureFlagsRoot';
import {InstanceDetailsRoot} from 'src/InstanceDetailsRoot';
import {PipelineExplorerRoot} from 'src/PipelineExplorerRoot';
import {PipelineRunsRoot} from 'src/PipelineRunsRoot';
import PythonErrorInfo from 'src/PythonErrorInfo';
import {TimezoneProvider} from 'src/TimeComponents';
import {AssetsRoot} from 'src/assets/AssetsRoot';
import {PipelineExecutionRoot} from 'src/execute/PipelineExecutionRoot';
import {PipelineExecutionSetupRoot} from 'src/execute/PipelineExecutionSetupRoot';
import {LeftNav} from 'src/nav/LeftNav';
import {PipelineNav} from 'src/nav/PipelineNav';
import {PipelinePartitionsRoot} from 'src/partitions/PipelinePartitionsRoot';
import {PipelineOverviewRoot} from 'src/pipelines/PipelineOverviewRoot';
import {RunRoot} from 'src/runs/RunRoot';
import {RunsRoot} from 'src/runs/RunsRoot';
import {ScheduleRoot} from 'src/schedules/ScheduleRoot';
import {SchedulerRoot} from 'src/schedules/SchedulerRoot';
import {SchedulesRoot} from 'src/schedules/SchedulesRoot';
import {SolidDetailsRoot} from 'src/solids/SolidDetailsRoot';
import {SolidsRoot} from 'src/solids/SolidsRoot';

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
            display: 'flex',
            flexDirection: 'column',
            minWidth: 0,
            width: '100%',
            height: '100%',
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
      {(context) =>
        context?.repository?.pipelines.length ? (
          <Redirect to={`/pipeline/${context?.repository.pipelines[0].name}/`} />
        ) : (
          <Route render={() => <NonIdealState title="No pipelines" />} />
        )
      }
    </DagsterRepositoryContext.Consumer>
  </Switch>
);

export const App: React.FunctionComponent = () => {
  const {options, loading, error} = useRepositoryOptions();
  const [repo, setRepo] = useCurrentRepositoryState(options);

  const content = () => {
    if (error) {
      return (
        <PythonErrorInfo
          contextMsg={`${error.__typename} encountered when loading pipelines:`}
          error={error}
          centered={true}
        />
      );
    }

    if (loading) {
      return <NonIdealState icon={<Spinner size={24} />} />;
    }

    return (
      <CustomConfirmationProvider>
        <DagsterRepositoryContext.Provider value={repo}>
          <AppRoutes />
          <CustomTooltipProvider />
          <CustomAlertProvider />
        </DagsterRepositoryContext.Provider>
      </CustomConfirmationProvider>
    );
  };

  return (
    <div style={{display: 'flex', height: '100%'}}>
      <BrowserRouter basename={APP_PATH_PREFIX}>
        <TimezoneProvider>
          <LeftNav options={options} loading={loading} repo={repo} setRepo={setRepo} />
          {content()}
        </TimezoneProvider>
      </BrowserRouter>
    </div>
  );
};
