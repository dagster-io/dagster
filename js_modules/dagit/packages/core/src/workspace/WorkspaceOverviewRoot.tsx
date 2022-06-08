import {
  Box,
  Colors,
  Group,
  NonIdealState,
  Page,
  PageHeader,
  Table,
  Heading,
  Subheading,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {LoadingSpinner} from '../ui/Loading';

import {ReloadAllButton} from './ReloadAllButton';
import {RepositoryLocationsList} from './RepositoryLocationsList';
import {useRepositoryOptions} from './WorkspaceContext';
import {buildRepoPath} from './buildRepoAddress';
import {workspacePath} from './workspacePath';

export const WorkspaceOverviewRoot = () => {
  const {loading, error, options} = useRepositoryOptions();

  const content = () => {
    if (loading) {
      return <LoadingSpinner purpose="page" />;
    }

    if (error) {
      return (
        <Box padding={{vertical: 64}}>
          <NonIdealState
            icon="error"
            title="Error loading repositories"
            description="Could not load repositories in this workspace."
          />
        </Box>
      );
    }

    if (!options.length) {
      return (
        <Box padding={{vertical: 64}}>
          <NonIdealState
            icon="folder"
            title="No repositories"
            description="When you add a repository to this workspace, it will appear here."
          />
        </Box>
      );
    }

    const anyPipelinesInWorkspace = options.some((option) =>
      option.repository.pipelines.some((p) => !p.isJob),
    );

    return (
      <Table>
        <thead>
          <tr>
            <th>Repository</th>
            <th>Assets</th>
            <th>Jobs</th>
            {anyPipelinesInWorkspace ? <th>Pipelines</th> : null}
            <th>Graphs</th>
            <th>Ops</th>
            <th>Schedules</th>
            <th>Sensors</th>
          </tr>
        </thead>
        <tbody>
          {options.map((repository) => {
            const {
              repository: {name, pipelines},
              repositoryLocation: {name: location},
            } = repository;
            const repoString = buildRepoPath(name, location);
            const anyPipelines = pipelines.some((pipelineOrJob) => !pipelineOrJob.isJob);
            return (
              <tr key={repoString}>
                <td style={{width: '40%'}}>{repoString}</td>
                <td>
                  <Link to={workspacePath(name, location, '/assets')}>Assets</Link>
                </td>
                <td>
                  <Link to={workspacePath(name, location, '/jobs')}>Jobs</Link>
                </td>
                {anyPipelinesInWorkspace ? (
                  <td>
                    {anyPipelines ? (
                      <Link to={workspacePath(name, location, '/pipelines')}>Pipelines</Link>
                    ) : (
                      <span style={{color: Colors.Gray400}}>None</span>
                    )}
                  </td>
                ) : null}
                <td>
                  <Link to={workspacePath(name, location, '/graphs')}>Graphs</Link>
                </td>
                <td>
                  <Link to={workspacePath(name, location, '/ops')}>Ops</Link>
                </td>
                <td>
                  <Link to={workspacePath(name, location, '/schedules')}>Schedules</Link>
                </td>
                <td>
                  <Link to={workspacePath(name, location, '/sensors')}>Sensors</Link>
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
      <PageHeader title={<Heading>Workspace</Heading>} />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Group direction="row" spacing={12} alignItems="center">
          <Subheading id="repository-locations">Locations</Subheading>
          <ReloadAllButton />
        </Group>
      </Box>
      <Box padding={{bottom: 24}}>
        <RepositoryLocationsList />
      </Box>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'top', width: 1, color: Colors.KeylineGray}}
      >
        <Subheading id="repository-locations">Repositories</Subheading>
      </Box>
      {content()}
    </Page>
  );
};
