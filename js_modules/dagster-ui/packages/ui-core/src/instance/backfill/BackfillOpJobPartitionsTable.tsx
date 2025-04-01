import {Box, Colors, Icon, NonIdealState, Table} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link} from 'react-router-dom';

import {StatusBar} from './BackfillAssetPartitionsTable';
import {BackfillTableFragment} from './types/BackfillTable.types';
import {BackfillDetailsBackfillFragment} from './types/useBackfillDetailsQuery.types';
import {PipelineReference} from '../../pipelines/PipelineReference';
import {failedStatuses, inProgressStatuses, successStatuses} from '../../runs/RunStatuses';
import {numberFormatter} from '../../ui/formatters';
import {isThisThingAJob, useRepository} from '../../workspace/WorkspaceContext/util';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../../workspace/repoAddressAsString';
import {RepoAddress} from '../../workspace/types';
import {workspacePathFromAddress, workspacePipelinePath} from '../../workspace/workspacePath';

export const BackfillOpJobPartitionsTable = ({
  backfill,
}: {
  backfill: BackfillDetailsBackfillFragment;
}) => {
  const results = useMemo(() => backfill.partitionStatuses?.results || [], [backfill]);

  const repoAddress = backfill.partitionSet
    ? buildRepoAddress(
        backfill.partitionSet.repositoryOrigin.repositoryName,
        backfill.partitionSet.repositoryOrigin.repositoryLocationName,
      )
    : null;

  const inProgress = useMemo(
    () => results.filter((result) => inProgressStatuses.has(result.runStatus as any)),
    [results],
  );
  const succeeded = useMemo(
    () => results.filter((result) => successStatuses.has(result.runStatus as any)),
    [results],
  );
  const failed = useMemo(
    () => results.filter((result) => failedStatuses.has(result.runStatus as any)),
    [results],
  );

  if (!backfill.partitionStatuses) {
    return (
      <Box margin={48}>
        <NonIdealState
          title="Partition statuses unavailable"
          description="Unable to load per-partition statuses. This may occur if the backfilled assets or jobs no longer exist in your loaded code locations or their definition has changed."
        />
      </Box>
    );
  }
  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '50%'}}>Job name</th>
          <th>Partitions targeted</th>
          <th>In progress</th>
          <th>Succeeded</th>
          <th>Failed</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'baseline'}}>
              <BackfillOpJobTarget backfill={backfill} repoAddress={repoAddress} />
              <StatusBar
                targeted={results.length}
                inProgress={inProgress.length}
                succeeded={succeeded.length}
                failed={failed.length}
              />
            </Box>
          </td>
          <td>{numberFormatter.format(results.length)}</td>
          <td>{numberFormatter.format(inProgress.length)}</td>
          <td>{numberFormatter.format(succeeded.length)}</td>
          <td>{numberFormatter.format(failed.length)}</td>
        </tr>
      </tbody>
    </Table>
  );
};

export const BackfillOpJobTarget = ({
  backfill,
  repoAddress,
}: {
  backfill: Pick<BackfillTableFragment, 'partitionSet' | 'partitionSetName'>;
  repoAddress: RepoAddress | null;
}) => {
  const repo = useRepository(repoAddress);
  const {partitionSet, partitionSetName} = backfill;

  const buildHeader = () => {
    if (partitionSet && repo) {
      const link = workspacePipelinePath({
        repoName: partitionSet.repositoryOrigin.repositoryName,
        repoLocation: partitionSet.repositoryOrigin.repositoryLocationName,
        pipelineName: partitionSet.pipelineName,
        isJob: isThisThingAJob(repo, partitionSet.pipelineName),
        path: `/partitions?partitionSet=${encodeURIComponent(partitionSet.name)}`,
      });
      return (
        <Link style={{fontWeight: 500}} to={link}>
          {partitionSet.name}
        </Link>
      );
    }
    if (partitionSetName) {
      return <span style={{fontWeight: 500}}>{partitionSetName}</span>;
    }
    return null;
  };

  const repoLink = repoAddress ? (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}} style={{fontSize: '12px'}}>
      <Icon name="repo" color={Colors.textLight()} />
      <Link to={workspacePathFromAddress(repoAddress)}>
        {repoAddressAsHumanString(repoAddress)}
      </Link>
    </Box>
  ) : undefined;

  const pipelineLink =
    partitionSet && repoAddress && repo ? (
      <PipelineReference
        showIcon
        size="small"
        isJob={isThisThingAJob(repo, partitionSet.pipelineName)}
        pipelineName={partitionSet.pipelineName}
        pipelineHrefContext={repoAddress}
      />
    ) : null;

  return (
    <Box flex={{direction: 'column', gap: 4, alignItems: 'start'}}>
      {buildHeader()}
      <Box flex={{direction: 'column', gap: 4}} style={{fontSize: '12px'}}>
        {repoLink}
        {pipelineLink}
      </Box>
    </Box>
  );
};
