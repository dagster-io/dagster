import {Box, NonIdealState, Table} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {StatusBar} from './BackfillAssetPartitionsTable';
import {BackfillTarget} from './BackfillRow';
import {BackfillDetailsBackfillFragment} from './types/useBackfillDetailsQuery.types';
import {failedStatuses, inProgressStatuses, successStatuses} from '../../runs/RunStatuses';
import {numberFormatter} from '../../ui/formatters';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';

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
            <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
              <BackfillTarget backfill={backfill} repoAddress={repoAddress} />
              <StatusBar
                targeted={results.length}
                inProgress={inProgress.length}
                completed={succeeded.length}
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
