import * as React from 'react';
import {Route, Switch} from 'react-router-dom';

import {MainContent} from 'src/ui/MainContent';
import {WorkspaceOverviewRoot} from 'src/workspace/WorkspaceOverviewRoot';
import {WorkspacePipelineRoot} from 'src/workspace/WorkspacePipelineRoot';
import {WorkspaceRepoRoot} from 'src/workspace/WorkspaceRepoRoot';
import {WorkspaceRepositoryLocationsRoot} from 'src/workspace/WorkspaceRepositoryLocationsRoot';

export const WorkspaceRoot: React.FunctionComponent<{}> = () => {
  return (
    <MainContent>
      <Switch>
        <Route path="/workspace" exact component={WorkspaceOverviewRoot} />
        <Route
          path="/workspace/repository-locations"
          exact
          component={WorkspaceRepositoryLocationsRoot}
        />
        <Route path="/workspace/pipelines/:pipelinePath" render={WorkspacePipelineRoot} />
        <Route path="/workspace/:repoPath/:tab?" component={WorkspaceRepoRoot} />
      </Switch>
    </MainContent>
  );
};
