import * as React from 'react';
import {Route, RouteComponentProps, Switch} from 'react-router-dom';

import {PipelineRoot} from '../pipelines/PipelineRoot';
import {ScheduleRoot} from '../schedules/ScheduleRoot';
import {SensorRoot} from '../sensors/SensorRoot';
import {Box} from '../ui/Box';
import {MainContent} from '../ui/MainContent';
import {NonIdealState} from '../ui/NonIdealState';

import {GraphRoot} from './GraphRoot';
import {WorkspaceContext} from './WorkspaceContext';
import {WorkspaceOverviewRoot} from './WorkspaceOverviewRoot';
import {WorkspacePipelineRoot} from './WorkspacePipelineRoot';
import {WorkspaceRepoRoot} from './WorkspaceRepoRoot';
import {repoAddressFromPath} from './repoAddressFromPath';

const RepoRouteContainer: React.FC<{repoPath: string}> = (props) => {
  const {repoPath} = props;
  const workspaceState = React.useContext(WorkspaceContext);
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
      <Route
        path="/workspace/:repoPath/graphs/(/?.*)"
        render={(props) => <GraphRoot {...props} repoAddress={addressForPath} />}
      />
      <Route
        path={[
          '/workspace/:repoPath/pipelines/(/?.*)',
          '/workspace/:repoPath/jobs/(/?.*)',
          '/workspace/:repoPath/pipeline_or_job/(/?.*)',
        ]}
        render={() => <PipelineRoot repoAddress={addressForPath} />}
      />
      <Route
        path="/workspace/:repoPath/schedules/:scheduleName/:runTab?"
        render={(props: RouteComponentProps<{runTab?: string; scheduleName: string}>) => (
          <ScheduleRoot
            scheduleName={props.match.params.scheduleName}
            repoAddress={addressForPath}
            runTab={props.match.params.runTab}
          />
        )}
      />
      <Route
        path="/workspace/:repoPath/sensors/:sensorName"
        render={(props: RouteComponentProps<{sensorName: string}>) => (
          <SensorRoot sensorName={props.match.params.sensorName} repoAddress={addressForPath} />
        )}
      />
      <Route
        path="/workspace/:repoPath/:tab?"
        render={(props: RouteComponentProps<{tab?: string}>) => (
          <WorkspaceRepoRoot tab={props.match.params.tab} repoAddress={addressForPath} />
        )}
      />
    </Switch>
  );
};

export const WorkspaceRoot = () => {
  return (
    <MainContent>
      <Switch>
        <Route path="/workspace" exact component={WorkspaceOverviewRoot} />
        <Route
          path={['/workspace/pipelines/:pipelinePath', '/workspace/jobs/:pipelinePath']}
          render={(props: RouteComponentProps<{pipelinePath: string}>) => (
            <WorkspacePipelineRoot pipelinePath={props.match.params.pipelinePath} />
          )}
        />
        <Route
          path="/workspace/:repoPath"
          render={(props: RouteComponentProps<{repoPath: string}>) => (
            <RepoRouteContainer repoPath={props.match.params.repoPath} />
          )}
        />
      </Switch>
    </MainContent>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default WorkspaceRoot;
