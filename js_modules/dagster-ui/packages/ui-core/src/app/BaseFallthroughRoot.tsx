import {Box, Colors, Spinner} from '@dagster-io/ui-components';
import {useContext} from 'react';
import {Redirect, Switch} from 'react-router-dom';

import {Route} from './Route';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {DagsterRepoOption} from '../workspace/WorkspaceContext/util';
import {workspacePath, workspacePipelinePath} from '../workspace/workspacePath';

export const BaseFallthroughRoot = () => {
  return (
    <Switch>
      <Route path="*" isNestingRoute>
        <FinalRedirectOrLoadingRoot />
      </Route>
    </Switch>
  );
};

const getVisibleJobs = (r: DagsterRepoOption) =>
  r.repository.pipelines.filter((j) => !isHiddenAssetGroupJob(j.name));

const FinalRedirectOrLoadingRoot = () => {
  const workspaceContext = useContext(WorkspaceContext);
  const {allRepos, loading, locationEntries} = workspaceContext;

  if (loading) {
    return (
      <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
          <Spinner purpose="section" />
          <div style={{color: Colors.textLight()}}>Loading definitions…</div>
        </Box>
      </Box>
    );
  }

  // If we have location entries but no repos, we have no useful objects to show.
  // Redirect to Workspace overview to surface relevant errors to the user.
  if (locationEntries.length && allRepos.length === 0) {
    return <Redirect to="/locations" />;
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
            `/asset-groups/${repoWithAssetGroup.repository.assetGroups[0]!.groupName}`,
          )}
        />
      );
    }
  }

  // If we have exactly one repo with one job, route to the job overview
  if (reposWithVisibleJobs.length === 1) {
    const repo = reposWithVisibleJobs[0]!;
    const visibleJobs = getVisibleJobs(repo);
    if (visibleJobs.length === 1) {
      const job = visibleJobs[0]!;
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
  }

  // If we have more than one repo with a job, route to the instance overview
  if (reposWithVisibleJobs.length > 0) {
    return <Redirect to="/overview" />;
  }

  return <Redirect to="/locations" />;
};
