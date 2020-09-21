import {NonIdealState, Spinner} from '@blueprintjs/core';
import * as React from 'react';
import {BrowserRouter, Redirect, Route, Switch} from 'react-router-dom';

import CustomAlertProvider from './CustomAlertProvider';
import {CustomConfirmationProvider} from './CustomConfirmationProvider';
import {CustomTooltipProvider} from './CustomTooltipProvider';
import {
  DagsterRepositoryContext,
  useCurrentRepositoryState,
  useRepositoryOptions,
} from './DagsterRepositoryContext';
import {APP_PATH_PREFIX} from './DomUtils';
import {FeatureFlagsRoot} from './FeatureFlagsRoot';
import {InstanceDetailsRoot} from './InstanceDetailsRoot';
import {PipelineExplorerRoot} from './PipelineExplorerRoot';
import {PipelineRunsRoot} from './PipelineRunsRoot';
import PythonErrorInfo from './PythonErrorInfo';
import {TimezoneProvider} from './TimeComponents';
import {AssetsRoot} from './assets/AssetsRoot';
import {PipelineExecutionRoot} from './execute/PipelineExecutionRoot';
import {PipelineExecutionSetupRoot} from './execute/PipelineExecutionSetupRoot';
import {LeftNav} from './nav/LeftNav';
import {PipelineNav} from './nav/PipelineNav';
import {PipelinePartitionsRoot} from './partitions/PipelinePartitionsRoot';
import {PipelineOverviewRoot} from './pipelines/PipelineOverviewRoot';
import {RunRoot} from './runs/RunRoot';
import {RunsRoot} from './runs/RunsRoot';
import {ScheduleRoot} from './schedules/ScheduleRoot';
import {SchedulerRoot} from './schedules/SchedulerRoot';
import {SchedulesRoot} from './schedules/SchedulesRoot';
import {SolidDetailsRoot} from './solids/SolidDetailsRoot';
import {SolidsRoot} from './solids/SolidsRoot';

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
