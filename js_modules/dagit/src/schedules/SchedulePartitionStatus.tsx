import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {StatusTable} from 'src/JobUtils';
import {assertUnreachable} from 'src/Util';
import {
  ScheduleFragment,
  ScheduleFragment_partitionSet_partitionStatusesOrError_PartitionStatuses_results,
} from 'src/schedules/types/ScheduleFragment';
import {PipelineRunStatus} from 'src/types/globalTypes';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

const RUN_STATUSES = ['Succeeded', 'Failed', 'Missing', 'Pending'];

const calculateDisplayStatus = (
  partition: ScheduleFragment_partitionSet_partitionStatusesOrError_PartitionStatuses_results,
) => {
  switch (partition.runStatus) {
    case null:
      return 'Missing';
    case PipelineRunStatus.SUCCESS:
      return 'Succeeded';
    case PipelineRunStatus.FAILURE:
    case PipelineRunStatus.CANCELED:
    case PipelineRunStatus.CANCELING:
      return 'Failed';
    case PipelineRunStatus.MANAGED:
    case PipelineRunStatus.QUEUED:
    case PipelineRunStatus.NOT_STARTED:
    case PipelineRunStatus.STARTED:
    case PipelineRunStatus.STARTING:
      return 'Pending';
    default:
      return assertUnreachable(partition.runStatus);
  }
};

export const SchedulePartitionStatus: React.FC<{
  repoAddress: RepoAddress;
  schedule: ScheduleFragment;
}> = ({repoAddress, schedule}) => {
  if (
    !schedule.partitionSet ||
    schedule.partitionSet.partitionStatusesOrError.__typename !== 'PartitionStatuses'
  ) {
    return <div>&mdash;</div>;
  }

  const partitions = schedule.partitionSet.partitionStatusesOrError.results;
  const partitionsByType = {};
  partitions.forEach((partition) => {
    const displayStatus = calculateDisplayStatus(partition);
    partitionsByType[displayStatus] = [...(partitionsByType[displayStatus] || []), partition];
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
              <td style={{width: 100}}>{status}</td>
              <td>
                {status == 'Failed' || status == 'Missing' ? (
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
