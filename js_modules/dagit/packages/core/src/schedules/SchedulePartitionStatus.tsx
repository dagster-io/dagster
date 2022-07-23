import {gql, useLazyQuery} from '@apollo/client';
import {ButtonLink, Colors, Group, Caption} from '@dagster-io/ui';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {assertUnreachable} from '../app/Util';
import {StatusTable} from '../instigation/InstigationUtils';
import {RunStatus} from '../types/globalTypes';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ScheduleFragment} from './types/ScheduleFragment';
import {
  SchedulePartitionStatusFragment,
  SchedulePartitionStatusFragment_partitionSet_partitionStatusesOrError_PartitionStatuses_results as Partition,
} from './types/SchedulePartitionStatusFragment';
import {
  SchedulePartitionStatusQuery,
  SchedulePartitionStatusQueryVariables,
} from './types/SchedulePartitionStatusQuery';

const RUN_STATUSES = ['Succeeded', 'Failed', 'Missing', 'Pending'];

const calculateDisplayStatus = (partition: Partition) => {
  switch (partition.runStatus) {
    case null:
      return 'Missing';
    case RunStatus.SUCCESS:
      return 'Succeeded';
    case RunStatus.FAILURE:
    case RunStatus.CANCELED:
    case RunStatus.CANCELING:
      return 'Failed';
    case RunStatus.MANAGED:
    case RunStatus.QUEUED:
    case RunStatus.NOT_STARTED:
    case RunStatus.STARTED:
    case RunStatus.STARTING:
      return 'Pending';
    default:
      return assertUnreachable(partition.runStatus);
  }
};

export const SchedulePartitionStatus: React.FC<{
  repoAddress: RepoAddress;
  schedule: ScheduleFragment;
}> = React.memo(({repoAddress, schedule}) => {
  const repo = useRepository(repoAddress);
  const {name: scheduleName, partitionSet, pipelineName} = schedule;

  const partitionSetName = partitionSet?.name;
  const isJob = isThisThingAJob(repo, pipelineName);

  const partitionPath = React.useMemo(() => {
    const query = partitionSetName
      ? qs.stringify(
          {
            partitionSet: partitionSetName,
          },
          {addQueryPrefix: true},
        )
      : '';
    return `/${isJob ? 'jobs' : 'pipelines'}/${pipelineName}/partitions${query}`;
  }, [partitionSetName, isJob, pipelineName]);

  const partitionURL = workspacePathFromAddress(repoAddress, partitionPath);

  const [retrievePartitionStatus, {data, loading}] = useLazyQuery<
    SchedulePartitionStatusQuery,
    SchedulePartitionStatusQueryVariables
  >(SCHEDULE_PARTITION_STATUS_QUERY, {
    variables: {
      scheduleSelector: {
        scheduleName,
        repositoryName: repoAddress.name,
        repositoryLocationName: repoAddress.location,
      },
    },
  });

  const onClick = React.useCallback(() => retrievePartitionStatus(), [retrievePartitionStatus]);

  const loadable = () => {
    if (loading) {
      return <Caption style={{color: Colors.Gray400}}>Loading…</Caption>;
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

    return <Caption style={{color: Colors.Red700}}>Partition set not found!</Caption>;
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
    return <span style={{color: Colors.Gray300}}>None</span>;
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
                    style={{color: Colors.Gray900}}
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
