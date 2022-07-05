import {gql, useQuery} from '@apollo/client';
import {Box, Tabs, Tab, Page, NonIdealState} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
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
import {
  PreviousRunsForScheduleQuery,
  PreviousRunsForScheduleQueryVariables,
} from './types/PreviousRunsForScheduleQuery';
import {
  ScheduleRootQuery,
  ScheduleRootQueryVariables,
  ScheduleRootQuery_scheduleOrError_Schedule as Schedule,
} from './types/ScheduleRootQuery';

interface Props {
  repoAddress: RepoAddress;
}

export const ScheduleRoot: React.FC<Props> = (props) => {
  useTrackPageView();

  const {repoAddress} = props;
  const {scheduleName} = useParams<{scheduleName: string}>();

  useDocumentTitle(`Schedule: ${scheduleName}`);

  const scheduleSelector = {
    ...repoAddressToSelector(repoAddress),
    scheduleName,
  };

  const [selectedTab, setSelectedTab] = React.useState<string>('ticks');

  const queryResult = useQuery<ScheduleRootQuery, ScheduleRootQueryVariables>(SCHEDULE_ROOT_QUERY, {
    variables: {
      scheduleSelector,
    },
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    notifyOnNetworkStatusChange: true,
  });

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

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
              refreshState={refreshState}
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
  const queryResult = useQuery<PreviousRunsForScheduleQuery, PreviousRunsForScheduleQueryVariables>(
    PREVIOUS_RUNS_FOR_SCHEDULE_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {
        limit: 20,
        filter: {
          pipelineName: schedule.pipelineName,
          tags: [{key: DagsterTag.ScheduleName, value: schedule.name}],
        },
      },
      partialRefetch: true,
      notifyOnNetworkStatusChange: true,
    },
  );

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {data} = queryResult;

  if (!data) {
    return null;
  } else if (data.pipelineRunsOrError.__typename !== 'Runs') {
    return (
      <NonIdealState
        icon="error"
        title="Query Error"
        description={data.pipelineRunsOrError.message}
      />
    );
  }

  const runs = data?.pipelineRunsOrError.results;
  return <RunTable actionBarComponents={tabs} runs={runs} highlightedIds={highlightedIds} />;
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
      ...PythonErrorFragment
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
  ${PYTHON_ERROR_FRAGMENT}
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
      ... on Error {
        message
      }
    }
  }
  ${RUN_TABLE_RUN_FRAGMENT}
`;
