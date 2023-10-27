import {Box, PageHeader, Tag, Heading} from '@dagster-io/ui-components';
import React from 'react';
import {useRouteMatch} from 'react-router-dom';

import {usePermissionsForLocation} from '../app/Permissions';
import {JobFeatureContext} from '../pipelines/JobFeatureContext';
import {JobTabs} from '../pipelines/JobTabs';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {JobMetadata} from './JobMetadata';
import {RepositoryLink} from './RepositoryLink';

interface Props {
  repoAddress: RepoAddress;
}

export const PipelineNav: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const permissions = usePermissionsForLocation(repoAddress.location);

  const {tabBuilder} = React.useContext(JobFeatureContext);

  const match = useRouteMatch<{tab?: string; selector: string}>([
    '/locations/:repoPath/pipelines/:selector/:tab?',
    '/locations/:repoPath/jobs/:selector/:tab?',
    '/locations/:repoPath/pipeline_or_job/:selector/:tab?',
  ]);

  const explorerPath = explorerPathFromString(match!.params.selector);
  const {pipelineName, snapshotId} = explorerPath;

  const repo = useRepository(repoAddress);
  const repoJobEntry = repo?.repository.pipelines.find(
    (pipelineOrJob) => pipelineOrJob.name === pipelineName,
  );
  const isJob = !!repoJobEntry?.isJob;
  const isAssetJob = !!repoJobEntry?.isAssetJob;

  // If using pipeline:mode tuple (crag flag), check for partition sets that are for this specific
  // pipeline:mode tuple. Otherwise, just check for a pipeline name match.
  const partitionSets = repo?.repository.partitionSets || [];
  const hasLaunchpad = !isAssetJob;
  const hasPartitionSet = partitionSets.some(
    (partitionSet) => partitionSet.pipelineName === pipelineName,
  );

  const tabs = tabBuilder({hasLaunchpad, hasPartitionSet});

  return (
    <>
      <PageHeader
        title={<Heading>{pipelineName}</Heading>}
        tags={
          <Box flex={{direction: 'row', alignItems: 'center', gap: 8, wrap: 'wrap'}}>
            <Tag icon="job">
              {isJob ? 'Job in ' : 'Pipeline in '}
              <RepositoryLink repoAddress={repoAddress} />
            </Tag>
            {snapshotId ? null : (
              <JobMetadata pipelineName={pipelineName} repoAddress={repoAddress} />
            )}
          </Box>
        }
        tabs={
          <JobTabs
            repoAddress={repoAddress}
            isJob={isJob}
            explorerPath={explorerPath}
            permissions={permissions}
            matchingTab={match!.params.tab}
            tabs={tabs}
          />
        }
      />
    </>
  );
};
