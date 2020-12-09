import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {StatusTable} from 'src/JobUtils';
import {ScheduleFragment} from 'src/schedules/types/ScheduleFragment';
import {PartitionRunStatus} from 'src/types/globalTypes';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

const RUN_STATUSES = [
  PartitionRunStatus.SUCCESS,
  PartitionRunStatus.FAILURE,
  PartitionRunStatus.MISSING,
  PartitionRunStatus.PENDING,
];
const STATUS_LABELS = {
  [PartitionRunStatus.SUCCESS]: 'Succeeded',
  [PartitionRunStatus.FAILURE]: 'Failed',
  [PartitionRunStatus.MISSING]: 'Missing',
  [PartitionRunStatus.PENDING]: 'Pending',
};

export const SchedulePartitionStatus: React.FC<{
  repoAddress: RepoAddress;
  schedule: ScheduleFragment;
}> = ({repoAddress, schedule}) => {
  if (
    !schedule.partitionSet ||
    schedule.partitionSet.partitionsOrError.__typename !== 'Partitions'
  ) {
    return <div>&mdash;</div>;
  }

  const partitions = schedule.partitionSet.partitionsOrError.results;
  const partitionsByType = {};
  partitions.forEach((partition) => {
    partitionsByType[partition.status] = [...(partitionsByType[partition.status] || []), partition];
  });

  const partitionUrl = workspacePathFromAddress(
    repoAddress,
    `/pipelines/${schedule.pipelineName}/partitions`,
  );
  return (
    <StatusTable>
      <tbody>
        <tr>
          <th colSpan={2}>
            <Link style={{color: Colors.GRAY3}} to={partitionUrl}>
              {schedule.partitionSet.name}
            </Link>
          </th>
        </tr>
        {RUN_STATUSES.map((status) => {
          if (!(status in partitionsByType)) {
            return null;
          }
          return (
            <tr key={status}>
              <td style={{width: 100}}>{STATUS_LABELS[status]}</td>
              <td>
                {status == PartitionRunStatus.FAILURE || status == PartitionRunStatus.MISSING ? (
                  <Link
                    to={`${partitionUrl}?showFailuresAndGapsOnly=true`}
                    style={{color: Colors.DARK_GRAY1}}
                  >
                    {partitionsByType[status].length}
                  </Link>
                ) : (
                  partitionsByType[status].length
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </StatusTable>
  );
};
