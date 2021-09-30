import {gql, NetworkStatus, useQuery} from '@apollo/client';
import * as React from 'react';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {TickHistory} from '../instigation/TickHistory';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {SensorDetails} from './SensorDetails';
import {SENSOR_FRAGMENT} from './SensorFragment';
import {SensorInfo} from './SensorInfo';
import {SensorPreviousRuns, NoTargetSensorPreviousRuns} from './SensorPreviousRuns';
import {SensorRootQuery} from './types/SensorRootQuery';

const INTERVAL = 15 * 1000;

export const SensorRoot: React.FC<{
  repoAddress: RepoAddress;
  sensorName: string;
}> = ({sensorName, repoAddress}) => {
  useDocumentTitle(`Sensor: ${sensorName}`);

  const [selectedRunIds, setSelectedRunIds] = React.useState<string[]>([]);
  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName,
  };

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

  return (
    <Loading queryResult={queryResult} allowStaleData={true}>
      {({sensorOrError, instance}) => {
        if (sensorOrError.__typename !== 'Sensor') {
          return null;
        }

        return (
          <Page>
            <Group direction="column" spacing={24}>
              <Group direction="column" spacing={20} padding={{horizontal: 24}}>
                <SensorInfo daemonHealth={instance.daemonHealth} />
                <SensorDetails
                  repoAddress={repoAddress}
                  sensor={sensorOrError}
                  daemonHealth={instance.daemonHealth.daemonStatus.healthy}
                  countdownDuration={INTERVAL}
                  countdownStatus={countdownStatus}
                  onRefresh={() => onRefresh()}
                />
                <TickHistory
                  repoAddress={repoAddress}
                  name={sensorOrError.name}
                  showRecent={true}
                  onHighlightRunIds={(runIds: string[]) => setSelectedRunIds(runIds)}
                />
              </Group>
              {sensorOrError.targets && sensorOrError.targets.length ? (
                <SensorPreviousRuns
                  repoAddress={repoAddress}
                  sensor={sensorOrError}
                  highlightedIds={selectedRunIds}
                />
              ) : (
                <NoTargetSensorPreviousRuns
                  repoAddress={repoAddress}
                  sensor={sensorOrError}
                  highlightedIds={selectedRunIds}
                />
              )}
            </Group>
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
