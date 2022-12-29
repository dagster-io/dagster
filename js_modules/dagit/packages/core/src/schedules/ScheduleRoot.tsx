import {useQuery} from '@apollo/client';
import {Tabs, Tab, Page, NonIdealState} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {graphql} from '../graphql';
import {ScheduleFragmentFragment} from '../graphql/graphql';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {TicksTable} from '../instigation/TickHistory';
import {RunTable} from '../runs/RunTable';
import {DagsterTag} from '../runs/RunTag';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {ScheduleDetails} from './ScheduleDetails';
import {SchedulerInfo} from './SchedulerInfo';

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

  const queryResult = useQuery(SCHEDULE_ROOT_QUERY, {
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
              <SchedulerInfo
                daemonHealth={instance.daemonHealth}
                padding={{vertical: 16, horizontal: 24}}
              />
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
  schedule: ScheduleFragmentFragment;
  tabs?: React.ReactElement;
  highlightedIds?: string[];
}> = ({schedule, highlightedIds, tabs}) => {
  const queryResult = useQuery(PREVIOUS_RUNS_FOR_SCHEDULE_QUERY, {
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
  });

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

const SCHEDULE_ROOT_QUERY = graphql(`
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
        daemonStatus(daemonType: "SCHEDULER") {
          id
          healthy
        }
      }
    }
  }
`);

const PREVIOUS_RUNS_FOR_SCHEDULE_QUERY = graphql(`
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
`);
