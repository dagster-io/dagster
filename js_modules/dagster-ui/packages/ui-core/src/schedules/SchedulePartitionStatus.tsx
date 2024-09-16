import {ButtonLink, Caption, Colors, Group} from '@dagster-io/ui-components';
import qs from 'qs';
import {memo, useCallback, useMemo} from 'react';
import {Link} from 'react-router-dom';

import {
  SchedulePartitionStatusFragment,
  SchedulePartitionStatusQuery,
  SchedulePartitionStatusQueryVariables,
  SchedulePartitionStatusResultFragment,
} from './types/SchedulePartitionStatus.types';
import {ScheduleFragment} from './types/ScheduleUtils.types';
import {gql, useLazyQuery} from '../apollo-client';
import {assertUnreachable} from '../app/Util';
import {RunStatus} from '../graphql/types';
import {StatusTable} from '../instigation/InstigationUtils';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

const RUN_STATUSES = ['Succeeded', 'Failed', 'Missing', 'Pending'];

const calculateDisplayStatus = (partition: SchedulePartitionStatusResultFragment) => {
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

interface Props {
  repoAddress: RepoAddress;
  schedule: ScheduleFragment;
}

export const SchedulePartitionStatus = memo((props: Props) => {
  const {repoAddress, schedule} = props;
  const repo = useRepository(repoAddress);
  const {name: scheduleName, partitionSet, pipelineName} = schedule;

  const partitionSetName = partitionSet?.name;
  const isJob = isThisThingAJob(repo, pipelineName);

  const partitionPath = useMemo(() => {
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

  const onClick = useCallback(() => retrievePartitionStatus(), [retrievePartitionStatus]);

  const loadable = () => {
    if (loading) {
      return <Caption style={{color: Colors.textLight()}}>Loading…</Caption>;
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

    return <Caption style={{color: Colors.textRed()}}>Partition set not found!</Caption>;
  };

  return (
    <Group direction="column" spacing={4}>
      <Link to={partitionURL}>{partitionSetName}</Link>
      {loadable()}
    </Group>
  );
});

const RetrievedSchedulePartitionStatus = ({
  schedule,
  partitionURL,
}: {
  schedule: SchedulePartitionStatusFragment;
  partitionURL: string;
}) => {
  const {partitionSet} = schedule;

  if (!partitionSet || partitionSet.partitionStatusesOrError.__typename !== 'PartitionStatuses') {
    return <span style={{color: Colors.textLight()}}>None</span>;
  }

  const partitions = partitionSet.partitionStatusesOrError.results;
  const partitionsByType = {};
  partitions.forEach((partition) => {
    const displayStatus = calculateDisplayStatus(partition);
    (partitionsByType as any)[displayStatus] = [
      ...((partitionsByType as any)[displayStatus] || []),
      partition,
    ];
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
                    style={{color: Colors.textDefault()}}
                  >
                    {(partitionsByType as any)[status].length}
                  </Link>
                ) : (
                  (partitionsByType as any)[status].length
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </StatusTable>
  );
};

const SCHEDULE_PARTITION_STATUS_QUERY = gql`
  query SchedulePartitionStatusQuery($scheduleSelector: ScheduleSelector!) {
    scheduleOrError(scheduleSelector: $scheduleSelector) {
      ... on Schedule {
        id
        ...SchedulePartitionStatusFragment
      }
    }
  }

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
            ...SchedulePartitionStatusResult
          }
        }
      }
    }
  }

  fragment SchedulePartitionStatusResult on PartitionStatus {
    id
    partitionName
    runStatus
  }
`;
