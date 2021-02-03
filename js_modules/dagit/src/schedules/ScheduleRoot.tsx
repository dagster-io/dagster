import {gql, NetworkStatus, useQuery} from '@apollo/client';
import {IBreadcrumbProps} from '@blueprintjs/core';
import * as React from 'react';

import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {JobTickHistory} from 'src/jobs/TickHistory';
import {TopNav} from 'src/nav/TopNav';
import {DagsterTag} from 'src/runs/RunTag';
import {ScheduleDetails} from 'src/schedules/ScheduleDetails';
import {SCHEDULE_FRAGMENT} from 'src/schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT, SchedulerInfo} from 'src/schedules/SchedulerInfo';
import {PreviousRunsForScheduleQuery} from 'src/schedules/types/PreviousRunsForScheduleQuery';
import {
  ScheduleRootQuery,
  ScheduleRootQuery_scheduleOrError_Schedule as Schedule,
} from 'src/schedules/types/ScheduleRootQuery';
import {Group} from 'src/ui/Group';
import {ScrollContainer} from 'src/ui/ListComponents';
import {Loading} from 'src/ui/Loading';
import {Page} from 'src/ui/Page';
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

  const [selectedRunIds, setSelectedRunIds] = React.useState<string[]>([]);
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
      {({scheduleOrError, scheduler, instance}) => {
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
            text: 'Schedules',
            href: workspacePathFromAddress(repoAddress, '/schedules'),
          },
        ];

        return (
          <ScrollContainer>
            <TopNav breadcrumbs={breadcrumbs} />
            <Page>
              <Group direction="column" spacing={20}>
                <SchedulerInfo
                  schedulerOrError={scheduler}
                  daemonHealth={instance.daemonHealth}
                  errorsOnly={true}
                />
                <ScheduleDetails
                  repoAddress={repoAddress}
                  schedule={scheduleOrError}
                  countdownDuration={INTERVAL}
                  countdownStatus={countdownStatus}
                  onRefresh={() => onRefresh()}
                />
                <JobTickHistory
                  repoAddress={repoAddress}
                  jobName={scheduleOrError.name}
                  onHighlightRunIds={(runIds: string[]) => setSelectedRunIds(runIds)}
                />
                <SchedulePreviousRuns
                  repoAddress={repoAddress}
                  schedule={scheduleOrError}
                  highlightedIds={selectedRunIds}
                  runTab={runTab}
                />
              </Group>
            </Page>
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
  highlightedIds: string[];
}

const SchedulePreviousRuns: React.FC<SchedulePreviousRunsProps> = (props) => {
  const {schedule, highlightedIds} = props;
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

  return (
    <PreviousRunsSection
      loading={loading}
      data={data?.pipelineRunsOrError}
      highlightedIds={highlightedIds}
    />
  );
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
    instance {
      ...InstanceHealthFragment
    }
  }

  ${SCHEDULER_FRAGMENT}
  ${SCHEDULE_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
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
