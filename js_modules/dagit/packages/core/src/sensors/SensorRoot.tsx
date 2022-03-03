import {gql, NetworkStatus, useQuery} from '@apollo/client';
import {Box, Tab, Tabs, Page} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {TicksTable, TickHistoryTimeline} from '../instigation/TickHistory';
import {InstigationStatus} from '../types/globalTypes';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {SensorDetails} from './SensorDetails';
import {SENSOR_FRAGMENT} from './SensorFragment';
import {SensorInfo} from './SensorInfo';
import {SensorPreviousRuns} from './SensorPreviousRuns';
import {SensorRootQuery} from './types/SensorRootQuery';

const INTERVAL = 15 * 1000;

export const SensorRoot: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  const {sensorName} = useParams<{sensorName: string}>();
  useDocumentTitle(`Sensor: ${sensorName}`);

  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName,
  };

  const [selectedTab, setSelectedTab] = React.useState<string>('ticks');
  const queryResult = useQuery<SensorRootQuery>(SENSOR_ROOT_QUERY, {
    variables: {
      sensorSelector,
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
      {({sensorOrError, instance}) => {
        if (sensorOrError.__typename !== 'Sensor') {
          return null;
        }
        const showDaemonWarning = !instance.daemonHealth.daemonStatus.healthy;
        const showLiveTicks =
          instance.daemonHealth.daemonStatus.healthy &&
          sensorOrError.sensorState.status === InstigationStatus.RUNNING;

        return (
          <Page>
            <SensorDetails
              repoAddress={repoAddress}
              sensor={sensorOrError}
              daemonHealth={instance.daemonHealth.daemonStatus.healthy}
              countdownDuration={INTERVAL}
              countdownStatus={countdownStatus}
              onRefresh={() => onRefresh()}
            />
            {showDaemonWarning ? (
              <Box padding={{vertical: 16, horizontal: 24}}>
                <SensorInfo daemonHealth={instance.daemonHealth} />
              </Box>
            ) : null}
            {showLiveTicks ? (
              <TickHistoryTimeline repoAddress={repoAddress} name={sensorOrError.name} />
            ) : null}
            {selectedTab === 'ticks' ? (
              <TicksTable tabs={tabs} repoAddress={repoAddress} name={sensorOrError.name} />
            ) : (
              <SensorPreviousRuns repoAddress={repoAddress} sensor={sensorOrError} tabs={tabs} />
            )}
          </Page>
        );
      }}
    </Loading>
  );
};

const SENSOR_ROOT_QUERY = gql`
  query SensorRootQuery($sensorSelector: SensorSelector!) {
    sensorOrError(sensorSelector: $sensorSelector) {
      __typename
      ... on Sensor {
        id
        ...SensorFragment
      }
    }
    instance {
      ...InstanceHealthFragment
      daemonHealth {
        id
        daemonStatus(daemonType: "SENSOR") {
          id
          healthy
        }
      }
    }
  }
  ${SENSOR_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
`;
