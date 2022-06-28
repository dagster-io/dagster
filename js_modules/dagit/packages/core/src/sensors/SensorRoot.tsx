import {gql, useQuery} from '@apollo/client';
import {Box, Tab, Tabs, Page} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {TicksTable, TickHistoryTimeline} from '../instigation/TickHistory';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {SensorDetails} from './SensorDetails';
import {SENSOR_FRAGMENT} from './SensorFragment';
import {SensorInfo} from './SensorInfo';
import {SensorPreviousRuns} from './SensorPreviousRuns';
import {SensorRootQuery, SensorRootQueryVariables} from './types/SensorRootQuery';

export const SensorRoot: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  useTrackPageView();

  const {sensorName} = useParams<{sensorName: string}>();
  useDocumentTitle(`Sensor: ${sensorName}`);

  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName,
  };

  const [selectedTab, setSelectedTab] = React.useState<string>('ticks');
  const queryResult = useQuery<SensorRootQuery, SensorRootQueryVariables>(SENSOR_ROOT_QUERY, {
    variables: {sensorSelector},
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
      {({sensorOrError, instance}) => {
        if (sensorOrError.__typename !== 'Sensor') {
          return null;
        }
        const showDaemonWarning = !instance.daemonHealth.daemonStatus.healthy;

        return (
          <Page>
            <SensorDetails
              repoAddress={repoAddress}
              sensor={sensorOrError}
              daemonHealth={instance.daemonHealth.daemonStatus.healthy}
              refreshState={refreshState}
            />
            {showDaemonWarning ? (
              <Box padding={{vertical: 16, horizontal: 24}}>
                <SensorInfo daemonHealth={instance.daemonHealth} />
              </Box>
            ) : null}
            <TickHistoryTimeline repoAddress={repoAddress} name={sensorOrError.name} />
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
