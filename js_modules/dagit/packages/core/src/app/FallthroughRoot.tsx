import {Box, Colors, ExternalAnchorButton, NonIdealState, Spinner} from '@dagster-io/ui';
import * as React from 'react';
import {Redirect, Route, Switch, useLocation} from 'react-router-dom';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {DagsterRepoOption, WorkspaceContext} from '../workspace/WorkspaceContext';
import {workspacePath, workspacePipelinePath} from '../workspace/workspacePath';

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

const getVisibleJobs = (r: DagsterRepoOption) =>
  r.repository.pipelines.filter((j) => !isHiddenAssetGroupJob(j.name));

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

  const reposWithVisibleJobs = allRepos.filter((r) => getVisibleJobs(r).length > 0);

  // If we have no repos with jobs, see if we have an asset group and route to it.
  if (reposWithVisibleJobs.length === 0) {
    const repoWithAssetGroup = allRepos.find((r) => r.repository.assetGroups.length);
    if (repoWithAssetGroup) {
      return (
        <Redirect
          to={workspacePath(
            repoWithAssetGroup.repository.name,
            repoWithAssetGroup.repositoryLocation.name,
            `/asset-groups/${repoWithAssetGroup.repository.assetGroups[0].groupName}`,
          )}
        />
      );
    }
  }

  // If we have exactly one repo with one job, route to the job overview
  if (reposWithVisibleJobs.length === 1 && getVisibleJobs(reposWithVisibleJobs[0]).length === 1) {
    const repo = reposWithVisibleJobs[0];
    const job = getVisibleJobs(repo)[0];
    return (
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

  // If we have more than one repo with a job, route to the instance overview
  if (reposWithVisibleJobs.length > 0) {
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
