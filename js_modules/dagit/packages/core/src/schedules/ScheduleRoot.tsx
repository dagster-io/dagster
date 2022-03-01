import {gql, NetworkStatus, useQuery} from '@apollo/client';
import {Box, ColorsWIP, Page} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {TicksTable, TickHistoryTimeline} from '../instigation/TickHistory';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {ScheduleDetails} from './ScheduleDetails';
import {SCHEDULE_FRAGMENT} from './ScheduleUtils';
import {SchedulerInfo} from './SchedulerInfo';
import {ScheduleRootQuery} from './types/ScheduleRootQuery';

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
            <TickHistoryTimeline repoAddress={repoAddress} name={scheduleOrError.name} />
            <TicksTable repoAddress={repoAddress} name={scheduleName} />
          </Page>
        );
      }}
    </Loading>
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
