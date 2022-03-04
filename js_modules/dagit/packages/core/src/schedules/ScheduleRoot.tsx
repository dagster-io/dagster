import {gql, NetworkStatus, useQuery} from '@apollo/client';
import {Box, Tabs, Tab, Page} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {TicksTable} from '../instigation/TickHistory';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {DagsterTag} from '../runs/RunTag';
import {Loading} from '../ui/Loading';
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
  repoAddress: RepoAddress;
}

const INTERVAL = 15 * 1000;

export const ScheduleRoot: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const {scheduleName} = useParams<{scheduleName: string}>();

  useDocumentTitle(`Schedule: ${scheduleName}`);

  const scheduleSelector = {
    ...repoAddressToSelector(repoAddress),
    scheduleName,
  };

  const [selectedTab, setSelectedTab] = React.useState<string>('ticks');

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
  const tabs = (
    <Tabs selectedTabId={selectedTab} onChange={setSelectedTab}>
      <Tab id="ticks" title="Tick history" />
      <Tab id="runs" title="Run history" />
    </Tabs>
  );

  return (
    <Loading queryResult={queryResult} allowStaleData={true}>
      {({scheduleOrError, instance}) => {
        if (scheduleOrError.__typename !== 'Schedule') {
          return null;
        }

        const showDaemonWarning = !instance.daemonHealth.daemonStatus.healthy;

        return (
          <Page>
            <ScheduleDetails
              repoAddress={repoAddress}
              schedule={scheduleOrError}
              countdownDuration={INTERVAL}
              countdownStatus={countdownStatus}
              onRefresh={() => onRefresh()}
            />
            {showDaemonWarning ? (
              <Box padding={{vertical: 16, horizontal: 24}}>
                <SchedulerInfo daemonHealth={instance.daemonHealth} />
              </Box>
            ) : null}
            {selectedTab === 'ticks' ? (
              <TicksTable tabs={tabs} repoAddress={repoAddress} name={scheduleOrError.name} />
            ) : (
              <SchedulePreviousRuns
                repoAddress={repoAddress}
                schedule={scheduleOrError}
                tabs={tabs}
              />
            )}
          </Page>
        );
      }}
    </Loading>
  );
};

export const SchedulePreviousRuns: React.FC<{
  repoAddress: RepoAddress;
  schedule: Schedule;
  tabs?: React.ReactElement;
  highlightedIds?: string[];
}> = ({schedule, highlightedIds, tabs}) => {
  const {data} = useQuery<PreviousRunsForScheduleQuery>(PREVIOUS_RUNS_FOR_SCHEDULE_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {
      limit: 20,
      filter: {
        pipelineName: schedule.pipelineName,
        tags: [{key: DagsterTag.ScheduleName, value: schedule.name}],
      },
    },
    partialRefetch: true,
    pollInterval: 15 * 1000,
  });

  if (!data || data.pipelineRunsOrError.__typename !== 'Runs') {
    return null;
  }

  const runs = data?.pipelineRunsOrError.results;
  return (
    <RunTable
      actionBarComponents={tabs}
      onSetFilter={() => {}}
      runs={runs}
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
      daemonHealth {
        id
        daemonStatus(daemonType: "SCHEDULE") {
          id
          healthy
        }
      }
    }
  }

  ${SCHEDULE_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
`;

const PREVIOUS_RUNS_FOR_SCHEDULE_QUERY = gql`
  query PreviousRunsForScheduleQuery($filter: RunsFilter, $limit: Int) {
    pipelineRunsOrError(filter: $filter, limit: $limit) {
      __typename
      ... on Runs {
        results {
          id
          ... on PipelineRun {
            ...RunTableRunFragment
          }
        }
      }
    }
  }
  ${RUN_TABLE_RUN_FRAGMENT}
`;
