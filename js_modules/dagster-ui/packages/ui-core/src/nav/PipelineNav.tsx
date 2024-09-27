import {Box, Heading, PageHeader, Tag} from '@dagster-io/ui-components';
import {Link, useRouteMatch} from 'react-router-dom';
import {buildJobTabs} from 'shared/pipelines/buildJobTabs.oss';

import {JobMetadata} from './JobMetadata';
import {RepositoryLink} from './RepositoryLink';
import {usePermissionsForLocation} from '../app/Permissions';
import {JobTabs} from '../pipelines/JobTabs';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
}

export const PipelineNav = (props: Props) => {
  const {repoAddress} = props;
  const permissions = usePermissionsForLocation(repoAddress.location);

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

  const tabs = buildJobTabs({hasLaunchpad, hasPartitionSet});

  return (
    <>
      <PageHeader
        title={
          <Heading style={{display: 'flex', flexDirection: 'row', gap: 4}}>
            <Link to="/jobs">Jobs</Link>
            <span>/</span>
            {pipelineName}
          </Heading>
        }
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
