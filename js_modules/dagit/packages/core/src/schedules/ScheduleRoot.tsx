import {gql, NetworkStatus, useQuery} from '@apollo/client';
import * as React from 'react';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {TickHistory} from '../instigation/TickHistory';
import {DagsterTag} from '../runs/RunTag';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {PreviousRunsSection, PREVIOUS_RUNS_FRAGMENT} from '../workspace/PreviousRunsSection';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {ScheduleDetails} from './ScheduleDetails';
import {SCHEDULE_FRAGMENT} from './ScheduleUtils';
import {SchedulerInfo} from './SchedulerInfo';
import {PreviousRunsForScheduleQuery} from './types/PreviousRunsForScheduleQuery';
import {
  ScheduleRootQuery,
  ScheduleRootQuery_scheduleOrError_Schedule as Schedule,
} from './types/ScheduleRootQuery';

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
      {({scheduleOrError, instance}) => {
        if (scheduleOrError.__typename !== 'Schedule') {
          return null;
        }

        return (
          <Page>
            <ScheduleDetails
              repoAddress={repoAddress}
              schedule={scheduleOrError}
              countdownDuration={INTERVAL}
              countdownStatus={countdownStatus}
              onRefresh={() => onRefresh()}
            />
            <Box
              padding={{vertical: 16, horizontal: 24}}
              border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
            >
              <SchedulerInfo daemonHealth={instance.daemonHealth} />
            </Box>
            <TickHistory
              repoAddress={repoAddress}
              name={scheduleOrError.name}
              onHighlightRunIds={(runIds: string[]) => setSelectedRunIds(runIds)}
            />
            <SchedulePreviousRuns
              repoAddress={repoAddress}
              schedule={scheduleOrError}
              highlightedIds={selectedRunIds}
              runTab={runTab}
            />
          </Page>
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
