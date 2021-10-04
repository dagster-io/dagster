import * as React from 'react';
import {Link} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {Box} from '../ui/Box';
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
        <NonIdealState
          icon="error"
          title="Error loading repositories"
          description="Could not load repositories in this workspace."
        />
      );
    }

    if (!options.length) {
      return (
        <NonIdealState
          icon="visibility"
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
      <Box padding={{horizontal: 24}}>
        <PageHeader title={<Heading>Workspace</Heading>} />
      </Box>
      <Box padding={{horizontal: 24, top: 24, bottom: 16}}>
        <Group direction="row" spacing={8} alignItems="center">
          <Subheading id="repository-locations">Locations</Subheading>
          <ReloadAllButton />
        </Group>
      </Box>
      <RepositoryLocationsList />
      <Box padding={{horizontal: 24, top: 32, bottom: 16}}>
        <Subheading id="repository-locations">Repositories</Subheading>
      </Box>
      {content()}
    </Page>
  );
};
