import {Colors} from '@blueprintjs/core';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {assertUnreachable} from '../app/Util';
import {StatusTable} from '../instigation/InstigationUtils';
import {PipelineRunStatus} from '../types/globalTypes';
import {Group} from '../ui/Group';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {
  ScheduleFragment,
  ScheduleFragment_partitionSet_partitionStatusesOrError_PartitionStatuses_results,
} from './types/ScheduleFragment';

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
}> = React.memo(({repoAddress, schedule}) => {
  const {flagPipelineModeTuples} = useFeatureFlags();
  const {partitionSet, pipelineName, mode} = schedule;
  const partitionSetName = partitionSet?.name;

  const partitionPath = React.useMemo(() => {
    const query = partitionSetName
      ? qs.stringify(
          {
            partitionSet: partitionSetName,
          },
          {addQueryPrefix: true},
        )
      : '';
    return `/${
      flagPipelineModeTuples ? 'jobs' : 'pipelines'
    }/${pipelineName}:${mode}/partitions${query}`;
  }, [flagPipelineModeTuples, pipelineName, mode, partitionSetName]);

  if (
    !schedule.partitionSet ||
    schedule.partitionSet.partitionStatusesOrError.__typename !== 'PartitionStatuses'
  ) {
    return <span style={{color: Colors.GRAY4}}>None</span>;
  }

  const partitions = schedule.partitionSet.partitionStatusesOrError.results;
  const partitionsByType = {};
  partitions.forEach((partition) => {
    const displayStatus = calculateDisplayStatus(partition);
    partitionsByType[displayStatus] = [...(partitionsByType[displayStatus] || []), partition];
  });

  const partitionUrl = workspacePathFromAddress(repoAddress, partitionPath);

  return (
    <Group direction="column" spacing={4}>
      <Link to={partitionUrl}>{schedule.partitionSet.name}</Link>
      <StatusTable>
        <tbody>
          {RUN_STATUSES.map((status) => {
            if (!(status in partitionsByType)) {
              return null;
            }
            return (
              <tr key={status}>
                <td style={{width: '100px'}}>{status}</td>
                <td>
                  {status === 'Failed' || status === 'Missing' ? (
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
    </Group>
  );
});
