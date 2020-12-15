import {gql, NetworkStatus, useQuery} from '@apollo/client';
import {IBreadcrumbProps} from '@blueprintjs/core';
import * as React from 'react';

import {ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {SensorTickHistory} from 'src/jobs/TickHistory';
import {TopNav} from 'src/nav/TopNav';
import {SensorDetails} from 'src/sensors/SensorDetails';
import {SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {SensorPreviousRuns} from 'src/sensors/SensorPreviousRuns';
import {SensorTimeline} from 'src/sensors/SensorTimeline';
import {SensorRootQuery} from 'src/sensors/types/SensorRootQuery';
import {Group} from 'src/ui/Group';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

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
    pollInterval: 15 * 1000,
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
            text: 'Sensors',
            href: workspacePathFromAddress(repoAddress, '/sensors'),
          },
        ];

        return (
          <ScrollContainer>
            <TopNav breadcrumbs={breadcrumbs} />
            <Group direction="column" spacing={24} padding={{vertical: 20, horizontal: 24}}>
              <SensorDetails
                repoAddress={repoAddress}
                sensor={sensorOrError}
                daemonHealth={instance.daemonHealth.daemonStatus.healthy}
                countdownDuration={INTERVAL}
                countdownStatus={countdownStatus}
                onRefresh={() => onRefresh()}
              />
              <SensorTimeline
                repoAddress={repoAddress}
                sensor={sensorOrError}
                daemonHealth={instance.daemonHealth.daemonStatus.healthy}
                onSelectRunIds={(runIds: string[]) => setSelectedRunIds(runIds)}
              />
              <SensorTickHistory repoAddress={repoAddress} sensor={sensorOrError} />
              <SensorPreviousRuns
                repoAddress={repoAddress}
                sensor={sensorOrError}
                highlightedIds={selectedRunIds}
              />
            </Group>
          </ScrollContainer>
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
      daemonHealth {
        daemonStatus(daemonType: SENSOR) {
          healthy
        }
      }
    }
  }
  ${SENSOR_FRAGMENT}
`;
