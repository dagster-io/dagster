import {Box, MainContent, NonIdealState, SpinnerWithText} from '@dagster-io/ui-components';
import {useContext} from 'react';
import {Redirect, Switch, useParams} from 'react-router-dom';

import {CodeLocationNotFound} from './CodeLocationNotFound';
import {GraphRoot} from './GraphRoot';
import {WorkspaceAssetsRoot} from './WorkspaceAssetsRoot';
import {WorkspaceContext} from './WorkspaceContext/WorkspaceContext';
import {WorkspaceGraphsRoot} from './WorkspaceGraphsRoot';
import {WorkspaceJobsRoot} from './WorkspaceJobsRoot';
import {WorkspaceOpsRoot} from './WorkspaceOpsRoot';
import {WorkspaceSchedulesRoot} from './WorkspaceSchedulesRoot';
import {WorkspaceSensorsRoot} from './WorkspaceSensorsRoot';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {repoAddressFromPath} from './repoAddressFromPath';
import {workspacePathFromAddress} from './workspacePath';
import {useFeatureFlags} from '../app/Flags';
import {Route} from '../app/Route';
import {AssetGroupRoot} from '../assets/AssetGroupRoot';
import {CodeLocationDefinitionsRoot} from '../code-location/CodeLocationDefinitionsRoot';
import CodeLocationOverviewRoot from '../code-location/CodeLocationOverviewRoot';
import {PipelineRoot} from '../pipelines/PipelineRoot';
import {ResourceRoot} from '../resources/ResourceRoot';
import {WorkspaceResourcesRoot} from '../resources/WorkspaceResourcesRoot';
import {ScheduleRoot} from '../schedules/ScheduleRoot';
import {SensorRoot} from '../sensors/SensorRoot';

const RepoRouteContainer = () => {
  const {repoPath} = useParams<{repoPath: string}>();
  const workspaceState = useContext(WorkspaceContext);
  const addressForPath = repoAddressFromPath(repoPath);
  const {flagCodeLocationPage} = useFeatureFlags();

  const {loading} = workspaceState;

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

  const matchingRepo = workspaceState.allRepos.find(
    (repo) =>
      repo.repository.name === addressForPath.name &&
      repo.repositoryLocation.name === addressForPath.location,
  );

  // If we don't have any active code locations, or if our active repo does not match
  // the repo path in the URL, it means we aren't able to load this repo.
  if (!matchingRepo) {
    if (loading) {
      return (
        <Box padding={{vertical: 64}} flex={{direction: 'row', justifyContent: 'center'}}>
          <SpinnerWithText label={`Loading ${repoAddressAsHumanString(addressForPath)}…`} />
        </Box>
      );
    }

    const entryForLocation = workspaceState.locationEntries.find(
      (entry) => entry.id === addressForPath.location,
    );

    return (
      <Box padding={{vertical: 64}}>
        <CodeLocationNotFound
          repoAddress={addressForPath}
          locationEntry={entryForLocation || null}
        />
      </Box>
    );
  }

  return (
    <Switch>
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
      {flagCodeLocationPage ? (
        <>
          <Route path="/locations/:repoPath" exact>
            <CodeLocationOverviewRoot repoAddress={addressForPath} />
          </Route>
          <Route path="/locations/:repoPath/definitions" exact>
            <Redirect to={workspacePathFromAddress(addressForPath, '/assets')} />
          </Route>
          <Route
            path={[
              '/locations/:repoPath/assets',
              '/locations/:repoPath/jobs',
              '/locations/:repoPath/resources',
              '/locations/:repoPath/schedules',
              '/locations/:repoPath/sensors',
              '/locations/:repoPath/graphs',
              '/locations/:repoPath/ops/:name?',
            ]}
            exact
          >
            <CodeLocationDefinitionsRoot
              repoAddress={addressForPath}
              repository={matchingRepo.repository}
            />
          </Route>
        </>
      ) : (
        <>
          <Route path="/locations/:repoPath" exact>
            <Redirect to={workspacePathFromAddress(addressForPath, '/assets')} />
          </Route>
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
        </>
      )}
      <Route path={['/locations/:repoPath/*', '/locations/:repoPath/']}>
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
