import * as React from 'react';
import {Link} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {LoadingSpinner} from '../ui/Loading';
import {NonIdealState} from '../ui/NonIdealState';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Table} from '../ui/Table';
import {Heading, Subheading} from '../ui/Text';

import {ReloadAllButton} from './ReloadAllButton';
import {RepositoryLocationsList} from './RepositoryLocationsList';
import {useRepositoryOptions} from './WorkspaceContext';
import {buildRepoPath} from './buildRepoAddress';
import {workspacePath} from './workspacePath';

export const WorkspaceOverviewRoot = () => {
  const {loading, error, options} = useRepositoryOptions();
  const {flagPipelineModeTuples, flagAssetGraph} = useFeatureFlags();

  const content = () => {
    if (loading) {
      return <LoadingSpinner purpose="page" />;
    }

    if (error) {
      return (
        <Box padding={{vertical: 32}}>
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
        <Box padding={{vertical: 32}}>
          <NonIdealState
            icon="folder"
            title="No repositories"
            description="When you add a repository to this workspace, it will appear here."
          />
        </Box>
      );
    }

    return (
      <Table>
        <thead>
          <tr>
            <th>Repository</th>
            {flagPipelineModeTuples ? (
              <>
                <th>Jobs</th>
                <th>Graphs</th>
              </>
            ) : (
              <th>Pipelines</th>
            )}
            <th>{flagPipelineModeTuples ? 'Ops' : 'Solids'}</th>
            {flagAssetGraph ? <th>Assets</th> : null}
            <th>Schedules</th>
            <th>Sensors</th>
          </tr>
        </thead>
        <tbody>
          {options.map((repository) => {
            const {
              repository: {name},
              repositoryLocation: {name: location},
            } = repository;
            const repoString = buildRepoPath(name, location);
            return (
              <tr key={repoString}>
                <td style={{width: '40%'}}>{repoString}</td>
                {flagPipelineModeTuples ? (
                  <>
                    <td>
                      <Link to={workspacePath(name, location, '/jobs')}>Jobs</Link>
                    </td>
                    <td>
                      <Link to={workspacePath(name, location, '/graphs')}>Graphs</Link>
                    </td>
                  </>
                ) : (
                  <td>
                    <Link to={workspacePath(name, location, '/pipelines')}>Pipelines</Link>
                  </td>
                )}
                <td>
                  <Link
                    to={workspacePath(name, location, flagPipelineModeTuples ? '/ops' : '/solids')}
                  >
                    {flagPipelineModeTuples ? 'Ops' : 'Solids'}
                  </Link>
                </td>
                {flagAssetGraph ? (
                  <td>
                    <Link to={workspacePath(name, location, '/assets')}>Assets</Link>
                  </td>
                ) : null}
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
        border={{side: 'top', width: 1, color: ColorsWIP.KeylineGray}}
      >
        <Subheading id="repository-locations">Repositories</Subheading>
      </Box>
      {content()}
    </Page>
  );
};
