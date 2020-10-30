import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Route, RouteComponentProps, Switch} from 'react-router-dom';

import {PipelineRoot} from 'src/pipelines/PipelineRoot';
import {ScheduleRoot} from 'src/schedules/ScheduleRoot';
import {SchedulesRoot} from 'src/schedules/SchedulesRoot';
import {SolidDetailsRoot} from 'src/solids/SolidDetailsRoot';
import {SolidsRoot} from 'src/solids/SolidsRoot';
import {MainContent} from 'src/ui/MainContent';
import {useWorkspaceState} from 'src/workspace/WorkspaceContext';
import {WorkspaceOverviewRoot} from 'src/workspace/WorkspaceOverviewRoot';
import {WorkspacePipelineRoot} from 'src/workspace/WorkspacePipelineRoot';
import {WorkspaceRepoRoot} from 'src/workspace/WorkspaceRepoRoot';
import {WorkspaceRepositoryLocationsRoot} from 'src/workspace/WorkspaceRepositoryLocationsRoot';
import {repoAddressFromPath} from 'src/workspace/repoAddressFromPath';

const RepoRouteContainer: React.FC<{repoPath: string}> = (props) => {
  const {repoPath} = props;
  const workspaceState = useWorkspaceState();

  const addressForPath = repoAddressFromPath(repoPath);

  // A RepoAddress could not be created for this path, which means it's invalid.
  if (!addressForPath) {
    return (
      <NonIdealState
        icon="cube"
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
    );
  }

  const {loading, activeRepo} = workspaceState;

  if (loading) {
    return <div />;
  }

  // If we don't have any active repositories, or if our active repo does not match
  // the repo path in the URL, it means we aren't able to load this repo.
  if (!activeRepo || activeRepo.path !== repoPath) {
    return (
      <NonIdealState
        icon="cube"
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
    );
  }

  return (
    <Switch>
      <Route
        path="/workspace/:repoPath/pipelines/(/?.*)"
        render={() => <PipelineRoot repoAddress={addressForPath} />}
      />
      <Route
        path="/workspace/:repoPath/solid/:name"
        render={(props: RouteComponentProps<{name: string}>) => (
          <SolidDetailsRoot name={props.match.params.name} repoAddress={addressForPath} />
        )}
      />
      <Route
        path="/workspace/:repoPath/solids/:name?"
        render={(props: RouteComponentProps<{name?: string}>) => (
          <SolidsRoot name={props.match.params.name} repoAddress={addressForPath} />
        )}
      />
      <Route
        path="/workspace/:repoPath/schedules"
        exact
        render={() => <SchedulesRoot repoAddress={addressForPath} />}
      />
      <Route
        path="/workspace/:repoPath/schedules/:scheduleName"
        render={(props: RouteComponentProps<{scheduleName: string}>) => (
          <ScheduleRoot
            scheduleName={props.match.params.scheduleName}
            repoAddress={addressForPath}
          />
        )}
      />
      <Route
        path="/workspace/:repoPath/:tab?"
        exact
        render={(props: RouteComponentProps<{tab?: string}>) => (
          <WorkspaceRepoRoot tab={props.match.params.tab} repoAddress={addressForPath} />
        )}
      />
    </Switch>
  );
};

export const WorkspaceRoot: React.FC<{}> = () => (
  <MainContent>
    <Switch>
      <Route path="/workspace" exact component={WorkspaceOverviewRoot} />
      <Route
        path="/workspace/repository-locations"
        exact
        component={WorkspaceRepositoryLocationsRoot}
      />
      <Route
        path="/workspace/pipelines/:pipelinePath"
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
