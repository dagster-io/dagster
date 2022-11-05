import {
  Box,
  Colors,
  Page,
  PageHeader,
  Heading,
  Icon,
  NonIdealState,
  Spinner,
  Tag,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';

import {DagsterRepoOption, useRepositoryOptions} from './WorkspaceContext';
import {buildRepoAddress} from './buildRepoAddress';
import {repoAddressAsString} from './repoAddressAsString';
import {workspacePath} from './workspacePath';

export const WorkspaceOverviewWithGrid = () => {
  const {loading, error, options} = useRepositoryOptions();

  const content = () => {
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

    return (
      <CardGrid>
        {options.map((option) => {
          const repoAddress = buildRepoAddress(
            option.repository.name,
            option.repositoryLocation.name,
          );
          return <RepositoryGridItem key={repoAddressAsString(repoAddress)} repo={option} />;
        })}
      </CardGrid>
    );
  };

  return (
    <Page>
      <PageHeader title={<Heading>Workspace</Heading>} />
      {content()}
    </Page>
  );
};

const RepositoryGridItem: React.FC<{repo: DagsterRepoOption}> = React.memo(({repo}) => {
  const repoName = repo.repository.name;
  const repoLocation = repo.repositoryLocation.name;
  const assetCount = repo.repository.assetGroups.length;
  const jobCount = repo.repository.pipelines.filter(({name}) => !isHiddenAssetGroupJob(name))
    .length;
  const scheduleCount = repo.repository.schedules.length;
  const sensorCount = repo.repository.sensors.length;

  return (
    <CardLink to={workspacePath(repoName, repoLocation)}>
      <Card>
        <Box
          flex={{direction: 'column', gap: 8}}
          padding={{bottom: 12}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <Box flex={{direction: 'row', alignItems: 'flex-start', gap: 8}}>
            <Icon name="folder" style={{marginTop: 1}} />
            <RepoName>{repoName}</RepoName>
          </Box>
          <RepoLocation>{`@${repoLocation}`}</RepoLocation>
        </Box>
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}} padding={{top: 12}}>
          <Tag icon="asset">{assetCount}</Tag>
          <Tag icon="job">{jobCount}</Tag>
          <Tag icon="schedule">{scheduleCount}</Tag>
          <Tag icon="sensors">{sensorCount}</Tag>
        </Box>
      </Card>
    </CardLink>
  );
});

const CardLink = styled(Link)`
  color: ${Colors.Dark};
  text-decoration: none;
  border-radius: 12px;

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
