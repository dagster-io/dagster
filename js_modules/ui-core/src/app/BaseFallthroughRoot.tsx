import {Box, Colors, Spinner} from '@dagster-io/ui-components';
import {useContext} from 'react';
import {Redirect, Switch} from 'react-router-dom';

import {Route} from './Route';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {DagsterRepoOption} from '../workspace/WorkspaceContext/util';

export const BaseFallthroughRoot = () => {
  return (
    <Switch>
      <Route path="*" isNestingRoute>
        <FinalRedirectOrLoadingRoot />
      </Route>
    </Switch>
  );
};

const FinalRedirectOrLoadingRoot = () => {
  const workspaceContext = useContext(WorkspaceContext);
  const {allRepos, loadingNonAssets: loading, locationEntries} = workspaceContext;

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

  // If there are visible jobs, redirect to overview
  const anyVisibleJobs = ({repository}: DagsterRepoOption) => {
    return repository.pipelines.some(({name}) => !isHiddenAssetGroupJob(name));
  };
  const anyReposWithVisibleJobs = allRepos.some((r) => anyVisibleJobs(r));
  if (anyReposWithVisibleJobs) {
    return <Redirect to="/overview" />;
  }

  // If there are jobs but they are all hidden, route to the overview timeline grouped by automation.
  const hasAnyJobs = allRepos.some((r) => r.repository.pipelines.length > 0);
  if (hasAnyJobs) {
    return <Redirect to="/overview/activity/timeline?groupBy=automation" />;
  }

  // If we have no repos with jobs, see if we have an asset group and route to it.
  const hasAnyAssets = allRepos.some((r) => r.repository.assetGroups.length);
  if (hasAnyAssets) {
    return <Redirect to="/asset-groups" />;
  }

  // Ben note: We only reach here if anyReposWithVisibleJobs is false,
  // hasAnyJobs is false, AND there is no asset group.
  //
  // In this case, the overview would be blank so we go to the locations page.
  return <Redirect to="/locations" />;
};
