import {useQuery} from '@apollo/client';
import {IBreadcrumbProps, NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {ROOT_REPOSITORIES_QUERY} from 'src/DagsterRepositoryContext';
import {Loading} from 'src/Loading';
import {TopNav} from 'src/nav/TopNav';
import {RootRepositoriesQuery} from 'src/types/RootRepositoriesQuery';
import {Page} from 'src/ui/Page';
import {RepositoryPipelinesList} from 'src/workspace/RepositoryPipelinesList';
import {RepositorySchedulesList} from 'src/workspace/RepositorySchedulesList';
import {RepositorySolidsList} from 'src/workspace/RepositorySolidsList';
import {repoAddressFromPath} from 'src/workspace/repoAddressFromPath';
import {workspacePath} from 'src/workspace/workspacePath';

type WorkspacePathParams = {
  repoPath: string;
  tab?: string;
};

export const WorkspaceRepoRoot: React.FunctionComponent<RouteComponentProps<
  WorkspacePathParams
>> = (props: RouteComponentProps<WorkspacePathParams>) => {
  const {match} = props;
  const {params} = match;
  const {repoPath, tab} = params;

  const repoAddress = React.useMemo(() => repoAddressFromPath(repoPath), [repoPath]);
  const matchingRepo = React.useCallback(
    (data: RootRepositoriesQuery) => {
      if (!repoAddress || data.repositoriesOrError.__typename !== 'RepositoryConnection') {
        return null;
      }
      const {name, location} = repoAddress;
      const repositories = data.repositoriesOrError;
      const match = repositories.nodes.find(
        (repo) => repo.name === name && repo.location.name === location,
      );
      return match || null;
    },
    [repoAddress],
  );

  const queryResult = useQuery<RootRepositoriesQuery>(ROOT_REPOSITORIES_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  return (
    <div style={{height: '100%', width: '100%', overflowY: 'auto'}}>
      <Loading queryResult={queryResult}>
        {(data) => {
          const match = matchingRepo(data);
          const name = match?.name;
          const location = match?.location.name;

          const content = () => {
            if (name && location) {
              return (
                <Page>
                  <Switch>
                    <Route
                      path="/workspace/:repoPath/schedules"
                      render={() => (
                        <RepositorySchedulesList repoName={name} repoLocation={location} />
                      )}
                    />
                    <Route
                      path="/workspace/:repoPath/solids"
                      render={() => (
                        <RepositorySolidsList repoName={name} repoLocation={location} />
                      )}
                    />
                    <Route
                      path="/workspace/:repoPath/pipelines"
                      render={() => (
                        <RepositoryPipelinesList repoName={name} repoLocation={location} />
                      )}
                    />
                    <Route
                      path="/workspace/:repoPath/(.*)?"
                      render={() => <Redirect to={workspacePath(name, location, `/pipelines`)} />}
                    />
                  </Switch>
                </Page>
              );
            }

            if (!repoAddress) {
              return (
                <NonIdealState
                  icon="cube"
                  title="Invalid repository"
                  description={
                    <div>
                      <div>
                        <strong>{`${repoPath}`}</strong>
                      </div>
                      {'  is not a valid repository path.'}
                    </div>
                  }
                />
              );
            }

            return (
              <NonIdealState
                icon="cube"
                title="Repository not found"
                description={
                  <div>
                    <div>
                      <strong>{`${repoAddress.name}@${repoAddress.location}`}</strong>
                    </div>
                    {' does not exist in this workspace.'}
                  </div>
                }
              />
            );
          };

          const breadcrumbs: IBreadcrumbProps[] = [
            {icon: 'cube', text: 'Workspace', href: '/workspace'},
          ];
          if (name && location) {
            breadcrumbs.push({text: `${name}@${location}`});
          }

          const tabs =
            name && location
              ? [
                  {text: 'Pipelines', href: workspacePath(name, location, '/pipelines')},
                  {text: 'Solids', href: workspacePath(name, location, '/solids')},
                  {text: 'Schedules', href: workspacePath(name, location, '/schedules')},
                ]
              : undefined;

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
            <>
              <TopNav activeTab={activeTab()} breadcrumbs={breadcrumbs} tabs={tabs} />
              {content()}
            </>
          );
        }}
      </Loading>
    </div>
  );
};
