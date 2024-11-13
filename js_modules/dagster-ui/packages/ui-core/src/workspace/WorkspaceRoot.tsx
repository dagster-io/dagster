import {Box, MainContent, NonIdealState, SpinnerWithText} from '@dagster-io/ui-components';
import {useContext} from 'react';
import {Redirect, Switch, useParams} from 'react-router-dom';

import {GraphRoot} from './GraphRoot';
import {WorkspaceContext} from './WorkspaceContext/WorkspaceContext';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {repoAddressFromPath} from './repoAddressFromPath';
import {workspacePathFromAddress} from './workspacePath';
import {Route} from '../app/Route';
import {AssetGroupRoot} from '../assets/AssetGroupRoot';
import {CodeLocationDefinitionsRoot} from '../code-location/CodeLocationDefinitionsRoot';
import CodeLocationOverviewRoot from '../code-location/CodeLocationOverviewRoot';
import {PipelineRoot} from '../pipelines/PipelineRoot';
import {ResourceRoot} from '../resources/ResourceRoot';
import {ScheduleRoot} from '../schedules/ScheduleRoot';
import {SensorRoot} from '../sensors/SensorRoot';

const RepoRouteContainer = () => {
  const {repoPath} = useParams<{repoPath: string}>();
  const workspaceState = useContext(WorkspaceContext);
  const addressForPath = repoAddressFromPath(repoPath);

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
      <Route path="/locations/:repoPath" exact>
        <CodeLocationOverviewRoot repoAddress={addressForPath} />
      </Route>
      <Route path="/locations/:repoPath/definitions" exact>
        <Redirect to={workspacePathFromAddress(addressForPath, '/assets')} />
      </Route>
      {/* Avoid trying to render a definitions route if there is no actual repo available. */}
      {matchingRepo ? (
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
      ) : null}
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
