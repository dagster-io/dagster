import {NonIdealState, Spinner} from '@blueprintjs/core';
import * as React from 'react';
import {BrowserRouter, Route, Switch} from 'react-router-dom';

import {CustomAlertProvider} from 'src/CustomAlertProvider';
import {CustomConfirmationProvider} from 'src/CustomConfirmationProvider';
import {CustomTooltipProvider} from 'src/CustomTooltipProvider';
import {
  DagsterRepositoryContext,
  useCurrentRepositoryState,
  useRepositoryOptions,
} from 'src/DagsterRepositoryContext';
import {APP_PATH_PREFIX} from 'src/DomUtils';
import {FallthroughRoot} from 'src/FallthroughRoot';
import {FeatureFlagsRoot} from 'src/FeatureFlagsRoot';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {TimezoneProvider} from 'src/TimeComponents';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {InstanceRoot} from 'src/instance/InstanceRoot';
import {LeftNav} from 'src/nav/LeftNav';
import {PipelineRoot} from 'src/pipelines/PipelineRoot';
import {ScheduleRoot} from 'src/schedules/ScheduleRoot';
import {SchedulesRoot} from 'src/schedules/SchedulesRoot';
import {SolidDetailsRoot} from 'src/solids/SolidDetailsRoot';
import {SolidsRoot} from 'src/solids/SolidsRoot';

const AppRoutes = () => (
  <Switch>
    <Route path="/flags" component={FeatureFlagsRoot} />
    <Route path="/solid/:name" component={SolidDetailsRoot} />
    <Route path="/solids/:name?" component={SolidsRoot} />
    <Route path="/schedules/:scheduleName" component={ScheduleRoot} />
    <Route path="/schedules" component={SchedulesRoot} />
    <Route path="/pipeline/(.*)" component={PipelineRoot} />
    <Route path="/instance" component={InstanceRoot} />
    <Route path="*" component={FallthroughRoot} />
  </Switch>
);

export const App: React.FunctionComponent = () => {
  const {options, loading, error} = useRepositoryOptions();
  const [repo, setRepo] = useCurrentRepositoryState(options);
  useDocumentTitle('Dagit');

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
