import {Box, MainContent, NonIdealState} from '@dagster-io/ui';
import * as React from 'react';
import {Route, Switch, useParams} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {AssetGroupRoot} from '../assets/AssetGroupRoot';
import {PipelineRoot} from '../pipelines/PipelineRoot';
import {ScheduleRoot} from '../schedules/ScheduleRoot';
import {SensorRoot} from '../sensors/SensorRoot';

import {GraphRoot} from './GraphRoot';
import {WorkspaceContext} from './WorkspaceContext';
import {WorkspaceJobsRoot} from './WorkspaceJobsRoot';
import {WorkspaceOverviewRoot} from './WorkspaceOverviewRoot';
import {WorkspacePipelineRoot} from './WorkspacePipelineRoot';
import {WorkspaceRepoRoot} from './WorkspaceRepoRoot';
import {WorkspaceSchedulesRoot} from './WorkspaceSchedulesRoot';
import {WorkspaceSensorsRoot} from './WorkspaceSensorsRoot';
import {repoAddressFromPath} from './repoAddressFromPath';

const RepoRouteContainer = () => {
  const {repoPath} = useParams<{repoPath: string}>();
  const workspaceState = React.useContext(WorkspaceContext);
  const {flagNewWorkspace} = useFeatureFlags();
  const addressForPath = repoAddressFromPath(repoPath);

  // A RepoAddress could not be created for this path, which means it's invalid.
  if (!addressForPath) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="error"
          title="Invalid repository"
          description={
            <div>
              <div>
                <strong>{repoPath}</strong>
              </div>
              {'  is not a valid repository path.'}
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

  // If we don't have any active repositories, or if our active repo does not match
  // the repo path in the URL, it means we aren't able to load this repo.
  if (!matchingRepo) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="error"
          title="Unknown repository"
          description={
            <div>
              <div>
                <strong>{repoPath}</strong>
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
      {flagNewWorkspace ? (
        <Route path="/workspace/:repoPath/jobs" exact>
          <WorkspaceJobsRoot repoAddress={addressForPath} />
        </Route>
      ) : null}
      {flagNewWorkspace ? (
        <Route path="/workspace/:repoPath/schedules" exact>
          <WorkspaceSchedulesRoot repoAddress={addressForPath} />
        </Route>
      ) : null}
      {flagNewWorkspace ? (
        <Route path="/workspace/:repoPath/sensors" exact>
          <WorkspaceSensorsRoot repoAddress={addressForPath} />
        </Route>
      ) : null}
      <Route path="/workspace/:repoPath/graphs/(/?.*)">
        <GraphRoot repoAddress={addressForPath} />
      </Route>
      <Route
        path={[
          '/workspace/:repoPath/pipelines/(/?.*)',
          '/workspace/:repoPath/jobs/(/?.*)',
          '/workspace/:repoPath/pipeline_or_job/(/?.*)',
        ]}
      >
        <PipelineRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/workspace/:repoPath/schedules/:scheduleName/:runTab?">
        <ScheduleRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/workspace/:repoPath/sensors/:sensorName">
        <SensorRoot repoAddress={addressForPath} />
      </Route>
      <Route path={['/workspace/:repoPath/asset-groups/:groupName/list(/?.*)']}>
        <AssetGroupRoot repoAddress={addressForPath} tab="list" />
      </Route>
      <Route
        path={[
          '/workspace/:repoPath/asset-groups/:groupName/(/?.*)',
          '/workspace/:repoPath/asset-groups/:groupName',
        ]}
      >
        <AssetGroupRoot repoAddress={addressForPath} tab="lineage" />
      </Route>
      <Route path="/workspace/:repoPath/:tab?">
        <WorkspaceRepoRoot repoAddress={addressForPath} />
      </Route>
    </Switch>
  );
};

export const WorkspaceRoot = () => {
  return (
    <MainContent>
      <Switch>
        <Route path="/workspace" exact>
          <WorkspaceOverviewRoot />
        </Route>
        <Route path={['/workspace/pipelines/:pipelinePath', '/workspace/jobs/:pipelinePath']}>
          <WorkspacePipelineRoot />
        </Route>
        <Route path="/workspace/:repoPath">
          <RepoRouteContainer />
        </Route>
      </Switch>
    </MainContent>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default WorkspaceRoot;
