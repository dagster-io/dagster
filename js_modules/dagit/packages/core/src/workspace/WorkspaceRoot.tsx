import {Box, MainContent, NonIdealState} from '@dagster-io/ui';
import * as React from 'react';
import {Redirect, Route, Switch, useParams} from 'react-router-dom';

import {AssetGroupRoot} from '../assets/AssetGroupRoot';
import {PipelineRoot} from '../pipelines/PipelineRoot';
import {ResourceRoot} from '../resources/ResourceRoot';
import {WorkspaceResourcesRoot} from '../resources/WorkspaceResourcesRoot';
import {ScheduleRoot} from '../schedules/ScheduleRoot';
import {SensorRoot} from '../sensors/SensorRoot';

import {GraphRoot} from './GraphRoot';
import {WorkspaceAssetsRoot} from './WorkspaceAssetsRoot';
import {WorkspaceContext} from './WorkspaceContext';
import {WorkspaceGraphsRoot} from './WorkspaceGraphsRoot';
import {WorkspaceJobsRoot} from './WorkspaceJobsRoot';
import {WorkspaceOpsRoot} from './WorkspaceOpsRoot';
import {WorkspaceSchedulesRoot} from './WorkspaceSchedulesRoot';
import {WorkspaceSensorsRoot} from './WorkspaceSensorsRoot';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {repoAddressFromPath} from './repoAddressFromPath';
import {workspacePathFromAddress} from './workspacePath';

const RepoRouteContainer = () => {
  const {repoPath} = useParams<{repoPath: string}>();
  const workspaceState = React.useContext(WorkspaceContext);
  const addressForPath = repoAddressFromPath(repoPath);

  // A RepoAddress could not be created for this path, which means it's invalid.
  if (!addressForPath) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="error"
          title="Invalid code location path"
          description={
            <div>
              <div>
                <strong>{repoPath}</strong>
              </div>
              {'  is not a valid code location path.'}
            </div>
          }
        />
      </Box>
    );
  }

  const {loading} = workspaceState;

  if (loading) {
    return <div />;
  }

  const matchingRepo = workspaceState.allRepos.find(
    (repo) =>
      repo.repository.name === addressForPath.name &&
      repo.repositoryLocation.name === addressForPath.location,
  );

  // If we don't have any active code locations, or if our active repo does not match
  // the repo path in the URL, it means we aren't able to load this repo.
  if (!matchingRepo) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="error"
          title="Unknown code location"
          description={
            <div>
              <div>
                <strong>{repoAddressAsHumanString(addressForPath)}</strong>
              </div>
              {'  is not loaded in the current workspace.'}
            </div>
          }
        />
      </Box>
    );
  }

  return (
    <Switch>
      <Route path="/locations/:repoPath/resources" exact>
        <WorkspaceResourcesRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/locations/:repoPath/assets" exact>
        <WorkspaceAssetsRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/locations/:repoPath/jobs" exact>
        <WorkspaceJobsRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/locations/:repoPath/schedules" exact>
        <WorkspaceSchedulesRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/locations/:repoPath/sensors" exact>
        <WorkspaceSensorsRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/locations/:repoPath/graphs" exact>
        <WorkspaceGraphsRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/locations/:repoPath/ops/:name?" exact>
        <WorkspaceOpsRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/locations/:repoPath/graphs/(/?.*)">
        <GraphRoot repoAddress={addressForPath} />
      </Route>
      <Route
        path={[
          '/locations/:repoPath/pipelines/(/?.*)',
          '/locations/:repoPath/jobs/(/?.*)',
          '/locations/:repoPath/pipeline_or_job/(/?.*)',
        ]}
      >
        <PipelineRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/locations/:repoPath/schedules/:scheduleName/:runTab?">
        <ScheduleRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/locations/:repoPath/sensors/:sensorName">
        <SensorRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/locations/:repoPath/resources/:resourceName">
        <ResourceRoot repoAddress={addressForPath} />
      </Route>
      <Route path={['/locations/:repoPath/asset-groups/:groupName/list(/?.*)']}>
        <AssetGroupRoot repoAddress={addressForPath} tab="list" />
      </Route>
      <Route
        path={[
          '/locations/:repoPath/asset-groups/:groupName/(/?.*)',
          '/locations/:repoPath/asset-groups/:groupName',
        ]}
      >
        <AssetGroupRoot repoAddress={addressForPath} tab="lineage" />
      </Route>
      <Route path="/locations/:repoPath/*">
        <Redirect to={workspacePathFromAddress(addressForPath, '/assets')} />
      </Route>
    </Switch>
  );
};

export const WorkspaceRoot = () => {
  return (
    <MainContent>
      <Switch>
        <Route path="/locations/:repoPath">
          <RepoRouteContainer />
        </Route>
      </Switch>
    </MainContent>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default WorkspaceRoot;
