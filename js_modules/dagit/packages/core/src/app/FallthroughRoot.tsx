import {Box, ExternalAnchorButton, Colors, NonIdealState, Spinner} from '@dagster-io/ui';
import * as React from 'react';
import {Redirect, Route, Switch, useLocation} from 'react-router-dom';

import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {__ASSET_GROUP} from '../workspace/asset-graph/Utils';
import {workspacePipelinePath} from '../workspace/workspacePath';

const InstanceRedirect = () => {
  const location = useLocation();
  const path = `${location.pathname}${location.search}`;
  return <Redirect to={`/instance${path}`} />;
};

export const FallthroughRoot = () => {
  return (
    <Switch>
      <Route path={['/runs/(.*)?', '/assets/(.*)?', '/scheduler']}>
        <InstanceRedirect />
      </Route>
      <Route path="/home">
        <FinalRedirectOrLoadingRoot />
      </Route>
      <Route path="*">
        <FinalRedirectOrLoadingRoot />
      </Route>
    </Switch>
  );
};

const FinalRedirectOrLoadingRoot = () => {
  const workspaceContext = React.useContext(WorkspaceContext);
  const {allRepos, loading, locationEntries} = workspaceContext;

  if (loading) {
    return (
      <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
          <Spinner purpose="section" />
          <div style={{color: Colors.Gray600}}>Loading workspace…</div>
        </Box>
      </Box>
    );
  }

  // If we have location entries but no repos, we have no useful objects to show.
  // Redirect to Workspace overview to surface relevant errors to the user.
  if (locationEntries.length && allRepos.length === 0) {
    return <Redirect to="/workspace" />;
  }

  const reposWithAJob = allRepos.filter((r) => r.repository.pipelines.length > 0);

  // If we have exactly one job, route to it's overview / graph tab or
  // to the asset graph if it's an __ASSET_GROUP job.
  if (reposWithAJob.length === 1 && reposWithAJob[0].repository.pipelines.length === 1) {
    const repo = reposWithAJob[0];
    const job = repo.repository.pipelines[0];
    return job.name === __ASSET_GROUP ? (
      <Redirect to="/instance/asset-graph" />
    ) : (
      <Redirect
        to={workspacePipelinePath({
          repoName: repo.repository.name,
          repoLocation: repo.repositoryLocation.name,
          pipelineName: job.name,
          isJob: job.isJob,
        })}
      />
    );
  }

  // If we have more than one job, route to the instance overview
  if (reposWithAJob.length > 1) {
    return <Redirect to="/instance" />;
  }

  const repoWithNoJob = allRepos[0];

  return (
    <Box padding={{vertical: 64}}>
      <NonIdealState
        icon="no-results"
        title={repoWithNoJob ? 'No jobs' : 'No repositories'}
        description={
          repoWithNoJob
            ? 'Your repository is loaded, but no jobs were found.'
            : 'Add a repository to get started.'
        }
        action={
          <ExternalAnchorButton href="https://docs.dagster.io/getting-started">
            View documentation
          </ExternalAnchorButton>
        }
      />
    </Box>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default FallthroughRoot;
