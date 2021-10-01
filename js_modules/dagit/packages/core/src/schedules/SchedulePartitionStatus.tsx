import {gql, useLazyQuery} from '@apollo/client';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {assertUnreachable} from '../app/Util';
import {StatusTable} from '../instigation/InstigationUtils';
import {PipelineRunStatus} from '../types/globalTypes';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {Caption} from '../ui/Text';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ScheduleFragment} from './types/ScheduleFragment';
import {
  SchedulePartitionStatusFragment,
  SchedulePartitionStatusFragment_partitionSet_partitionStatusesOrError_PartitionStatuses_results as Partition,
} from './types/SchedulePartitionStatusFragment';
import {SchedulePartitionStatusQuery} from './types/SchedulePartitionStatusQuery';

const RUN_STATUSES = ['Succeeded', 'Failed', 'Missing', 'Pending'];

const calculateDisplayStatus = (partition: Partition) => {
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
  const {name: scheduleName, mode, partitionSet, pipelineName} = schedule;

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

  const partitionURL = workspacePathFromAddress(repoAddress, partitionPath);

  const [retrievePartitionStatus, {data, loading}] = useLazyQuery<SchedulePartitionStatusQuery>(
    SCHEDULE_PARTITION_STATUS_QUERY,
    {
      variables: {
        scheduleSelector: {
          scheduleName,
          repositoryName: repoAddress.name,
          repositoryLocationName: repoAddress.location,
        },
      },
    },
  );

  const onClick = React.useCallback(() => retrievePartitionStatus(), [retrievePartitionStatus]);

  const loadable = () => {
    if (loading) {
      return <Caption style={{color: ColorsWIP.Gray400}}>Loading…</Caption>;
    }

    if (!data) {
      return (
        <ButtonLink onClick={onClick}>
          <Caption>Show coverage</Caption>
        </ButtonLink>
      );
    }

    const partitionFragment = data.scheduleOrError;
    if (partitionFragment.__typename === 'Schedule') {
      return (
        <RetrievedSchedulePartitionStatus
          schedule={partitionFragment}
          partitionURL={partitionURL}
        />
      );
    }

    return <Caption style={{color: ColorsWIP.Red700}}>Partition set not found!</Caption>;
  };

  return (
    <Group direction="column" spacing={4}>
      <Link to={partitionURL}>{partitionSetName}</Link>
      {loadable()}
    </Group>
  );
});

const RetrievedSchedulePartitionStatus: React.FC<{
  schedule: SchedulePartitionStatusFragment;
  partitionURL: string;
}> = ({schedule, partitionURL}) => {
  const {partitionSet} = schedule;

  if (!partitionSet || partitionSet.partitionStatusesOrError.__typename !== 'PartitionStatuses') {
    return <span style={{color: ColorsWIP.Gray300}}>None</span>;
  }

  const partitions = partitionSet.partitionStatusesOrError.results;
  const partitionsByType = {};
  partitions.forEach((partition) => {
    const displayStatus = calculateDisplayStatus(partition);
    partitionsByType[displayStatus] = [...(partitionsByType[displayStatus] || []), partition];
  });

  return (
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
                    to={`${partitionURL}?showFailuresAndGapsOnly=true`}
                    style={{color: ColorsWIP.Gray900}}
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

const SCHEDULE_PARTITION_STATUS_FRAGMENT = gql`
  fragment SchedulePartitionStatusFragment on Schedule {
    id
    mode
    pipelineName
    partitionSet {
      id
      name
      partitionStatusesOrError {
        ... on PartitionStatuses {
          results {
            id
            partitionName
            runStatus
          }
        }
      }
    }
  }
`;

const SCHEDULE_PARTITION_STATUS_QUERY = gql`
  query SchedulePartitionStatusQuery($scheduleSelector: ScheduleSelector!) {
    scheduleOrError(scheduleSelector: $scheduleSelector) {
      ... on Schedule {
        id
        ...SchedulePartitionStatusFragment
      }
    }
  }
  ${SCHEDULE_PARTITION_STATUS_FRAGMENT}
`;
