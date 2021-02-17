import {gql, NetworkStatus, useQuery} from '@apollo/client';
import * as React from 'react';

import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {JobTickHistory} from 'src/jobs/TickHistory';
import {SensorDetails} from 'src/sensors/SensorDetails';
import {SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {SensorInfo} from 'src/sensors/SensorInfo';
import {SensorPreviousRuns} from 'src/sensors/SensorPreviousRuns';
import {SensorRootQuery} from 'src/sensors/types/SensorRootQuery';
import {Group} from 'src/ui/Group';
import {Loading} from 'src/ui/Loading';
import {Page} from 'src/ui/Page';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';

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
              <SensorInfo daemonHealth={instance.daemonHealth} />
              <SensorDetails
                repoAddress={repoAddress}
                sensor={sensorOrError}
                daemonHealth={instance.daemonHealth.daemonStatus.healthy}
                daemonInterval={instance.sensorDaemonInterval}
                countdownDuration={INTERVAL}
                countdownStatus={countdownStatus}
                onRefresh={() => onRefresh()}
              />
              <JobTickHistory
                repoAddress={repoAddress}
                jobName={sensorOrError.name}
                showRecent={true}
                onHighlightRunIds={(runIds: string[]) => setSelectedRunIds(runIds)}
              />
              <SensorPreviousRuns
                repoAddress={repoAddress}
                sensor={sensorOrError}
                highlightedIds={selectedRunIds}
              />
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
        daemonStatus(daemonType: "SENSOR") {
          id
          healthy
        }
      }
      sensorDaemonInterval
    }
  }
  ${SENSOR_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
`;
