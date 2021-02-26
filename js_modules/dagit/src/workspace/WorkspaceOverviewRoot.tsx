import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Group} from 'src/ui/Group';
import {LoadingSpinner} from 'src/ui/Loading';
import {Page} from 'src/ui/Page';
import {PageHeader} from 'src/ui/PageHeader';
import {Table} from 'src/ui/Table';
import {Heading} from 'src/ui/Text';
import {useRepositoryOptions} from 'src/workspace/WorkspaceContext';
import {workspacePath} from 'src/workspace/workspacePath';

export const WorkspaceOverviewRoot = () => {
  const {loading, error, options} = useRepositoryOptions();

  const content = () => {
    if (loading) {
      return <LoadingSpinner purpose="page" />;
    }

    if (error) {
      return (
        <NonIdealState
          icon="cube"
          title="Error loading repositories"
          description="Could not load repositories in this workspace."
        />
      );
    }

    if (!options.length) {
      return (
        <NonIdealState
          icon="cube"
          title="Empty workspace"
          description="There are no repositories in this workspace."
        />
      );
    }

    return (
      <Table>
        <thead>
          <tr>
            <th>Repository</th>
            <th>Pipelines</th>
            <th>Solids</th>
            <th>Schedules</th>
          </tr>
        </thead>
        <tbody>
          {options.map((repository) => {
            const {
              repository: {name},
              repositoryLocation: {name: location},
            } = repository;
            const repoString = `${name}@${location}`;
            return (
              <tr key={repoString}>
                <td style={{width: '40%'}}>{repoString}</td>
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
  };

  return (
    <Page>
      <Group direction="column" spacing={16}>
        <PageHeader title={<Heading>Workspace</Heading>} />
        {content()}
      </Group>
    </Page>
  );
};
