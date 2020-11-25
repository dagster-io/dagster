import {gql, useQuery} from '@apollo/client';
import {IBreadcrumbProps} from '@blueprintjs/core';
import * as React from 'react';

import {ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {TopNav} from 'src/nav/TopNav';
import {SensorDetails} from 'src/sensors/SensorDetails';
import {SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {SensorPreviousRuns} from 'src/sensors/SensorPreviousRuns';
import {SensorRootQuery} from 'src/sensors/types/SensorRootQuery';
import {Group} from 'src/ui/Group';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface Props {
  repoAddress: RepoAddress;
  sensorName: string;
}

export const SensorRoot = (props: Props) => {
  const {sensorName, repoAddress} = props;
  useDocumentTitle(`Sensor: ${sensorName}`);

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
  });

  return (
    <Loading queryResult={queryResult} allowStaleData={true}>
      {({sensorOrError}) => {
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
            icon: 'send-to-graph',
            text: 'Sensors',
            href: workspacePathFromAddress(repoAddress, '/sensors'),
          },
        ];

        return (
          <ScrollContainer>
            <TopNav breadcrumbs={breadcrumbs} />
            <Group direction="vertical" spacing={24} padding={{vertical: 20, horizontal: 24}}>
              <SensorDetails repoAddress={repoAddress} sensor={sensorOrError} />
              <SensorPreviousRuns repoAddress={repoAddress} sensor={sensorOrError} />
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
  }
  ${SENSOR_FRAGMENT}
`;
