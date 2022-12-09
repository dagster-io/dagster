import {Box, Colors, Page, PageHeader, Heading, Icon, NonIdealState, Spinner} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {InstanceTabs} from '../instance/InstanceTabs';

import {RepositoryCountTags} from './RepositoryCountTags';
import {DagsterRepoOption, useRepositoryOptions} from './WorkspaceContext';
import {buildRepoAddress, DUNDER_REPO_NAME} from './buildRepoAddress';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {workspacePath} from './workspacePath';

export const WorkspaceOverviewWithGrid = () => {
  return (
    <Page>
      <PageHeader title={<Heading>Deployment</Heading>} tabs={<InstanceTabs tab="definitions" />} />
      <WorkspaceOverviewGrid />
    </Page>
  );
};

export const WorkspaceOverviewGrid = () => {
  const {loading, error, options} = useRepositoryOptions();

  if (loading) {
    return (
      <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
          <Spinner purpose="section" />
          <div style={{color: Colors.Gray600}}>Loading workspace…</div>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="error"
          title="Error loading definitions"
          description="Could not load definitions in this workspace."
        />
      </Box>
    );
  }

  if (!options.length) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="folder"
          title="No definitions"
          description="When you add a definition to this workspace, it will appear here."
        />
      </Box>
    );
  }

  return (
    <CardGrid>
      {options.map((option) => {
        const repoAddress = buildRepoAddress(
          option.repository.name,
          option.repositoryLocation.name,
        );
        return <RepositoryGridItem key={repoAddressAsHumanString(repoAddress)} repo={option} />;
      })}
    </CardGrid>
  );
};

const RepositoryGridItem: React.FC<{repo: DagsterRepoOption}> = React.memo(({repo}) => {
  const repoName = repo.repository.name;
  const repoLocation = repo.repositoryLocation.name;

  return (
    <Card>
      <Box
        flex={{direction: 'column', gap: 8}}
        padding={{bottom: 12}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <Box flex={{direction: 'row', alignItems: 'flex-start', gap: 8}}>
          <Icon name="folder" style={{marginTop: 1}} />
          <CardLink to={workspacePath(repoName, repoLocation)}>
            <RepoName>{repoName === DUNDER_REPO_NAME ? repoLocation : repoName}</RepoName>
          </CardLink>
        </Box>
        {repoName === DUNDER_REPO_NAME ? null : <RepoLocation>{`@${repoLocation}`}</RepoLocation>}
      </Box>
      <Box padding={{top: 12}}>
        <RepositoryCountTags
          repo={repo.repository}
          repoAddress={buildRepoAddress(repoName, repoLocation)}
        />
      </Box>
    </Card>
  );
});

const CardLink = styled(Link)`
  color: ${Colors.Dark};
  :hover,
  :active {
    color: ${Colors.Dark};
    text-decoration: none;
  }
`;

const CardGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  grid-column-gap: 12px;
  grid-row-gap: 12px;
  padding: 16px 24px;
`;

interface CardProps {
  $background?: string;
  $borderColor?: string;
}

export const Card = styled.div<CardProps>`
  ${({$background}) => ($background ? `background-color: ${$background};` : null)}
  border: 1px solid ${({$borderColor}) => $borderColor || Colors.KeylineGray};
  padding: 20px;
  border-radius: 12px;
  box-shadow: none;
  transition: box-shadow 150ms linear;

  :hover,
  :active {
    box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
  }
`;

const RepoName = styled.div`
  font-weight: 500;
  color: ${Colors.Link};
  word-break: break-word;
`;

const RepoLocation = styled.div`
  font-size: 12px;
  color: ${Colors.Gray700};
  word-break: break-word;
`;
