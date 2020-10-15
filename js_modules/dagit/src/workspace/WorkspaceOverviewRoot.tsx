import {IBreadcrumbProps, NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {Link} from 'react-router-dom';

import {ROOT_REPOSITORIES_QUERY} from 'src/DagsterRepositoryContext';
import {Loading} from 'src/Loading';
import {TopNav} from 'src/nav/TopNav';
import {RootRepositoriesQuery} from 'src/types/RootRepositoriesQuery';
import {Page} from 'src/ui/Page';
import {Table} from 'src/ui/Table';
import {workspacePath} from 'src/workspace/workspacePath';

export const WorkspaceOverviewRoot: React.FunctionComponent<{}> = () => {
  const queryResult = useQuery<RootRepositoriesQuery>(ROOT_REPOSITORIES_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const breadcrumbs: IBreadcrumbProps[] = [{icon: 'cube', text: 'Workspace'}];

  return (
    <>
      <TopNav breadcrumbs={breadcrumbs} />
      <Page>
        <Loading queryResult={queryResult}>
          {(data) => {
            const {repositoriesOrError} = data;
            if (repositoriesOrError.__typename === 'PythonError') {
              return (
                <NonIdealState
                  icon="cube"
                  title="Error loading repositories"
                  description="Could not load repositories in this workspace."
                />
              );
            }

            const {nodes} = repositoriesOrError;

            if (!nodes.length) {
              return (
                <NonIdealState
                  icon="cube"
                  title="Empty workspace"
                  description="There are no repositories in this workspace."
                />
              );
            }

            return (
              <Table striped style={{width: '100%'}}>
                <thead>
                  <tr>
                    <th>Repository</th>
                    <th>Pipelines</th>
                    <th>Solids</th>
                    <th>Schedules</th>
                  </tr>
                </thead>
                <tbody>
                  {nodes.map((repository) => {
                    const {
                      name,
                      location: {name: location},
                    } = repository;
                    const repoAddress = `${name}@${location}`;
                    return (
                      <tr key={repoAddress}>
                        <td style={{width: '40%'}}>{repoAddress}</td>
                        <td>
                          <Link to={workspacePath(name, location, '/pipelines')}>Pipelines</Link>
                        </td>
                        <td>
                          <Link to={workspacePath(name, location, '/solids')}>Solids</Link>
                        </td>
                        <td>
                          <Link to={workspacePath(name, location, '/schedules')}>Schedules</Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Table>
            );
          }}
        </Loading>
      </Page>
    </>
  );
};
