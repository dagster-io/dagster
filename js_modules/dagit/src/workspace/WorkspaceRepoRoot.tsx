import {IBreadcrumbProps} from '@blueprintjs/core';
import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {TopNav} from 'src/nav/TopNav';
import {Page} from 'src/ui/Page';
import {RepositoryPipelinesList} from 'src/workspace/RepositoryPipelinesList';
import {RepositorySchedulesList} from 'src/workspace/RepositorySchedulesList';
import {RepositorySolidsList} from 'src/workspace/RepositorySolidsList';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface Props {
  tab?: string;
  repoAddress: RepoAddress;
}

export const WorkspaceRepoRoot: React.FC<Props> = (props) => {
  const {repoAddress, tab} = props;
  const path = repoAddressAsString(repoAddress);

  const breadcrumbs: IBreadcrumbProps[] = [
    {icon: 'cube', text: 'Workspace', href: '/workspace'},
    {text: path},
  ];

  const tabs = [
    {text: 'Pipelines', href: workspacePathFromAddress(repoAddress, '/pipelines')},
    {text: 'Solids', href: workspacePathFromAddress(repoAddress, '/solids')},
    {text: 'Schedules', href: workspacePathFromAddress(repoAddress, '/schedules')},
  ];

  const activeTab = () => {
    switch (tab) {
      case 'schedules':
        return 'Schedules';
      case 'solids':
        return 'Solids';
      default:
        return 'Pipelines';
    }
  };

  return (
    <div style={{height: '100%', width: '100%', overflowY: 'auto'}}>
      <TopNav activeTab={activeTab()} breadcrumbs={breadcrumbs} tabs={tabs} />
      <Page>
        <Switch>
          <Route
            path="/workspace/:repoPath/schedules"
            render={() => <RepositorySchedulesList repoAddress={repoAddress} />}
          />
          <Route
            path="/workspace/:repoPath/solids"
            render={() => <RepositorySolidsList repoAddress={repoAddress} />}
          />
          <Route
            path="/workspace/:repoPath/pipelines"
            render={() => <RepositoryPipelinesList repoAddress={repoAddress} />}
          />
          <Route
            path="/workspace/:repoPath/(.*)?"
            render={() => <Redirect to={workspacePathFromAddress(repoAddress, `/pipelines`)} />}
          />
        </Switch>
      </Page>
    </div>
  );
};
