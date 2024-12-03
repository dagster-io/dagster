import {Box, Colors, Spinner} from '@dagster-io/ui-components';
import {useContext} from 'react';
import {Redirect, Switch} from 'react-router-dom';

import {Route} from './Route';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {DagsterRepoOption} from '../workspace/WorkspaceContext/util';
import {workspacePath} from '../workspace/workspacePath';

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
  if (reposWithVisibleJobs.length > 0) {
    return <Redirect to="/overview" />;
  }

  // Ben note: We only reach here if reposWithVisibleJobs === 0 AND there is no asset group.
  // In this case, the overview would be blank so we go to the locations page.
  return <Redirect to="/locations" />;
};
