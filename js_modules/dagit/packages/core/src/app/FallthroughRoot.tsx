import * as React from 'react';
import {Redirect, Route, Switch, useLocation} from 'react-router-dom';

import {Box} from '../ui/Box';
import {ExternalAnchorButton} from '../ui/Button';
import {ColorsWIP} from '../ui/Colors';
import {NonIdealState} from '../ui/NonIdealState';
import {Spinner} from '../ui/Spinner';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
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
          <div style={{color: ColorsWIP.Gray600}}>Loading workspace…</div>
        </Box>
      </Box>
    );
  }

  // If we have location entries but no repos, we have no useful objects to show.
  // Redirect to Workspace overview to surface relevant errors to the user.
  if (!allRepos.length && locationEntries.length) {
    return <Redirect to="/workspace" />;
  }

  // Default to the first job available in the first repo. This is kind of a legacy
  // approach, and might be worth rethinking.
  const firstRepo = allRepos[0] || null;
  if (firstRepo?.repository.pipelines.length) {
    const first = firstRepo.repository.pipelines[0];
    return (
      <Redirect
        to={workspacePipelinePath({
          repoName: firstRepo.repository.name,
          repoLocation: firstRepo.repositoryLocation.name,
          pipelineName: first.name,
          isJob: first.isJob,
        })}
      />
    );
  }

  return (
    <Box padding={{vertical: 64}}>
      <NonIdealState
        icon="no-results"
        title={firstRepo ? 'No pipelines or jobs' : 'No repositories'}
        description={
          firstRepo
            ? 'Your repository is loaded but no pipelines or jobs were found.'
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
