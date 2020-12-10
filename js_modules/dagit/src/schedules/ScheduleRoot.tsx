import {gql, NetworkStatus, useQuery} from '@apollo/client';
import {IBreadcrumbProps} from '@blueprintjs/core';
import * as React from 'react';

import {ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {TopNav} from 'src/nav/TopNav';
import {DagsterTag} from 'src/runs/RunTag';
import {ScheduleDetails} from 'src/schedules/ScheduleDetails';
import {SCHEDULE_FRAGMENT} from 'src/schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT} from 'src/schedules/SchedulerInfo';
import {PreviousRunsForScheduleQuery} from 'src/schedules/types/PreviousRunsForScheduleQuery';
import {
  ScheduleRootQuery,
  ScheduleRootQuery_scheduleOrError_Schedule as Schedule,
} from 'src/schedules/types/ScheduleRootQuery';
import {Group} from 'src/ui/Group';
import {PreviousRunsSection, PREVIOUS_RUNS_FRAGMENT} from 'src/workspace/PreviousRunsSection';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface Props {
  scheduleName: string;
  repoAddress: RepoAddress;
  runTab?: string;
}

const INTERVAL = 15 * 1000;

export const ScheduleRoot: React.FC<Props> = (props) => {
  const {scheduleName, repoAddress, runTab} = props;
  useDocumentTitle(`Schedule: ${scheduleName}`);

  const scheduleSelector = {
    ...repoAddressToSelector(repoAddress),
    scheduleName,
  };

  const queryResult = useQuery<ScheduleRootQuery>(SCHEDULE_ROOT_QUERY, {
    variables: {
      scheduleSelector,
    },
    fetchPolicy: 'cache-and-network',
    pollInterval: INTERVAL,
    partialRefetch: true,
    notifyOnNetworkStatusChange: true,
  });

  const {networkStatus, refetch, stopPolling, startPolling} = queryResult;

  const onRefresh = async () => {
    stopPolling();
    await refetch();
    startPolling(INTERVAL);
  };

  const countdownStatus = networkStatus === NetworkStatus.ready ? 'counting' : 'idle';

  return (
    <Loading queryResult={queryResult} allowStaleData={true}>
      {({scheduleOrError}) => {
        if (scheduleOrError.__typename !== 'Schedule') {
          return null;
        }

        const breadcrumbs: IBreadcrumbProps[] = [
          {
            icon: 'cube',
            text: 'Workspace',
            href: '/workspace',
          },
          {
            text: repoAddressAsString(repoAddress),
            href: workspacePathFromAddress(repoAddress),
          },
          {
            icon: 'time',
            text: 'Schedules',
            href: workspacePathFromAddress(repoAddress, '/schedules'),
          },
        ];

        return (
          <ScrollContainer>
            <TopNav breadcrumbs={breadcrumbs} />
            <Group direction="vertical" spacing={24} padding={{vertical: 20, horizontal: 24}}>
              <ScheduleDetails
                repoAddress={repoAddress}
                schedule={scheduleOrError}
                countdownDuration={INTERVAL}
                countdownStatus={countdownStatus}
                onRefresh={() => onRefresh()}
              />
              <SchedulePreviousRuns
                repoAddress={repoAddress}
                schedule={scheduleOrError}
                runTab={runTab}
              />
            </Group>
          </ScrollContainer>
        );
      }}
    </Loading>
  );
};

const RUNS_LIMIT = 20;

interface SchedulePreviousRunsProps {
  repoAddress: RepoAddress;
  runTab?: string;
  schedule: Schedule;
}

const SchedulePreviousRuns: React.FC<SchedulePreviousRunsProps> = (props) => {
  const {schedule} = props;
  const {data, loading} = useQuery<PreviousRunsForScheduleQuery>(PREVIOUS_RUNS_FOR_SCHEDULE_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {
      limit: RUNS_LIMIT,
      filter: {
        pipelineName: schedule.pipelineName,
        tags: [{key: DagsterTag.ScheduleName, value: schedule.name}],
      },
    },
    partialRefetch: true,
    pollInterval: 15 * 1000,
  });

  return <PreviousRunsSection loading={loading} data={data?.pipelineRunsOrError} />;
};

const SCHEDULE_ROOT_QUERY = gql`
  query ScheduleRootQuery($scheduleSelector: ScheduleSelector!) {
    scheduler {
      ...SchedulerFragment
    }
    scheduleOrError(scheduleSelector: $scheduleSelector) {
      ... on Schedule {
        id
        ...ScheduleFragment
      }
      ... on ScheduleNotFoundError {
        message
      }
      ... on PythonError {
        message
        stack
      }
    }
  }

  ${SCHEDULER_FRAGMENT}
  ${SCHEDULE_FRAGMENT}
`;

const PREVIOUS_RUNS_FOR_SCHEDULE_QUERY = gql`
  query PreviousRunsForScheduleQuery($filter: PipelineRunsFilter, $limit: Int) {
    pipelineRunsOrError(filter: $filter, limit: $limit) {
      __typename
      ...PreviousRunsFragment
    }
  }
  ${PREVIOUS_RUNS_FRAGMENT}
`;
