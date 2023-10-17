import {gql, useQuery} from '@apollo/client';
import {Box, Page, NonIdealState, ButtonGroup} from '@dagster-io/ui-components';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {TicksTable, TickHistoryTimeline} from '../instigation/TickHistory';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {SensorDetails} from './SensorDetails';
import {SENSOR_FRAGMENT} from './SensorFragment';
import {SensorInfo} from './SensorInfo';
import {SensorPreviousRuns} from './SensorPreviousRuns';
import {SensorRootQuery, SensorRootQueryVariables} from './types/SensorRoot.types';

export const SensorRoot: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  useTrackPageView();

  const {sensorName} = useParams<{sensorName: string}>();
  useDocumentTitle(`Sensor: ${sensorName}`);

  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName,
  };

  const [statuses, setStatuses] = React.useState<undefined | InstigationTickStatus[]>(undefined);
  const [timeRange, setTimerange] = React.useState<undefined | [number, number]>(undefined);
  const variables = React.useMemo(() => {
    if (timeRange || statuses) {
      return {
        afterTimestamp: timeRange?.[0],
        beforeTimestamp: timeRange?.[1],
        statuses,
      };
    }
    return {};
  }, [statuses, timeRange]);

  const [selectedTab, setSelectedTab] = useQueryPersistedState<'evaluations' | 'runs'>(
    React.useMemo(
      () => ({
        queryKey: 'view',
        decode: ({view}) => (view === 'runs' ? 'runs' : 'evaluations'),
        encode: (raw) => {
          return {view: raw, cursor: undefined, statuses: undefined};
        },
      }),
      [],
    ),
  );
  const queryResult = useQuery<SensorRootQuery, SensorRootQueryVariables>(SENSOR_ROOT_QUERY, {
    variables: {sensorSelector},
    notifyOnNetworkStatusChange: true,
  });

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const tabs = (
    <ButtonGroup
      activeItems={new Set([selectedTab])}
      buttons={[
        {id: 'evaluations', label: 'Evaluations'},
        {id: 'runs', label: 'Runs'},
      ]}
      onClick={(id: 'evaluations' | 'runs') => {
        setSelectedTab(id);
      }}
    />
  );
  return (
    <Loading queryResult={queryResult} allowStaleData={true}>
      {({sensorOrError, instance}) => {
        if (sensorOrError.__typename === 'SensorNotFoundError') {
          return (
            <Box padding={{vertical: 32}} flex={{justifyContent: 'center'}}>
              <NonIdealState
                icon="error"
                title={`Could not find sensor \`${sensorName}\` in definitions for \`${repoAddress.name}\``}
              />
            </Box>
          );
        } else if (sensorOrError.__typename === 'PythonError') {
          return <PythonErrorInfo error={sensorOrError} />;
        } else if (sensorOrError.__typename !== 'Sensor') {
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
              <SensorInfo
                daemonHealth={instance.daemonHealth}
                padding={{vertical: 16, horizontal: 24}}
              />
            ) : null}
            <TickHistoryTimeline
              repoAddress={repoAddress}
              name={sensorOrError.name}
              {...variables}
            />
            <Box margin={{top: 32}} border="top">
              {selectedTab === 'evaluations' ? (
                <TicksTable
                  tabs={tabs}
                  repoAddress={repoAddress}
                  name={sensorOrError.name}
                  setParentStatuses={setStatuses}
                  setTimerange={setTimerange}
                />
              ) : (
                <SensorPreviousRuns repoAddress={repoAddress} sensor={sensorOrError} tabs={tabs} />
              )}
            </Box>
          </Page>
        );
      }}
    </Loading>
  );
};

const SENSOR_ROOT_QUERY = gql`
  query SensorRootQuery($sensorSelector: SensorSelector!) {
    sensorOrError(sensorSelector: $sensorSelector) {
      ... on Sensor {
        id
        ...SensorFragment
      }
      ...PythonErrorFragment
    }
    instance {
      id
      daemonHealth {
        id
        daemonStatus(daemonType: "SENSOR") {
          id
          healthy
        }
      }
      ...InstanceHealthFragment
    }
  }

  ${SENSOR_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
`;
