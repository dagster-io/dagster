import {Box, ButtonGroup, Colors, NonIdealState, Page, Spinner} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import {Redirect, useParams} from 'react-router-dom';
import {DeclarativeAutomationBanner} from 'shared/assets/auto-materialization/DeclarativeAutomationBanner';
import {TickResultType} from 'shared/ticks/TickStatusTag';

import {SensorDetails} from './SensorDetails';
import {SENSOR_FRAGMENT} from './SensorFragment';
import {SensorInfo} from './SensorInfo';
import {SensorPreviousRuns} from './SensorPreviousRuns';
import {
  SensorAssetSelectionQuery,
  SensorAssetSelectionQueryVariables,
  SensorRootQuery,
  SensorRootQueryVariables,
} from './types/SensorRoot.types';
import {gql, useQuery} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useMergedRefresh, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {AUTOMATION_ASSET_SELECTION_FRAGMENT} from '../automation/AutomationAssetSelectionFragment';
import {InstigationTickStatus, SensorType} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {TickHistoryTimeline, TicksTable} from '../instigation/TickHistory';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

export const SensorRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  useTrackPageView();

  const {sensorName} = useParams<{sensorName: string}>();
  useDocumentTitle(`Sensor: ${sensorName}`);

  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName,
  };

  const [statuses, setStatuses] = useState<undefined | InstigationTickStatus[]>(undefined);
  const [timeRange, setTimerange] = useState<undefined | [number, number]>(undefined);
  const variables = useMemo(() => {
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
    useMemo(
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

  const selectionQueryResult = useQuery<
    SensorAssetSelectionQuery,
    SensorAssetSelectionQueryVariables
  >(SENSOR_ASSET_SELECTIONS_QUERY, {
    variables: {sensorSelector},
    notifyOnNetworkStatusChange: true,
  });

  const refreshState1 = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const refreshState2 = useQueryRefreshAtInterval(selectionQueryResult, FIFTEEN_SECONDS);
  const refreshState = useMergedRefresh(refreshState1, refreshState2);

  const {data, loading} = queryResult;

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

  if (!data && loading) {
    return (
      <Box
        margin={{top: 32}}
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'center', gap: 16}}
      >
        <Spinner purpose="body-text" />
        <div style={{color: Colors.textLight()}}>Loading sensor…</div>
      </Box>
    );
  }

  if (!data || data.sensorOrError.__typename === 'SensorNotFoundError') {
    return (
      <Box padding={{vertical: 32}}>
        <NonIdealState
          icon="error"
          title={`Could not find sensor \`${sensorName}\` in definitions for \`${repoAddress.name}\``}
        />
      </Box>
    );
  }

  const {sensorOrError} = data;
  if (sensorOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={sensorOrError} />;
  }

  if (sensorOrError.__typename === 'UnauthorizedError') {
    return <Redirect to="/overview/sensors" />;
  }

  const {instance} = data;
  const assetSelection =
    selectionQueryResult.data?.sensorOrError.__typename === 'Sensor'
      ? selectionQueryResult.data.sensorOrError.assetSelection
      : null;

  const isAutomationSensor =
    sensorOrError.sensorType === SensorType.AUTO_MATERIALIZE ||
    sensorOrError.sensorType === SensorType.AUTOMATION;

  const sensorDaemonStatus = instance.daemonHealth.sensorDaemonStatus;

  const tickResultType: TickResultType = isAutomationSensor ? 'materializations' : 'runs';

  return (
    <Page>
      <SensorDetails
        repoAddress={repoAddress}
        sensor={sensorOrError}
        daemonHealth={sensorDaemonStatus.healthy}
        refreshState={refreshState}
        assetSelection={assetSelection || null}
      />
      <SensorInfo
        sensorDaemonStatus={sensorDaemonStatus}
        padding={{vertical: 16, horizontal: 24}}
      />
      {isAutomationSensor && (
        <Box padding={{vertical: 12, horizontal: 24}}>
          <DeclarativeAutomationBanner />
        </Box>
      )}
      <TickHistoryTimeline
        tickResultType={tickResultType}
        repoAddress={repoAddress}
        name={sensorOrError.name}
        {...variables}
      />
      <Box margin={{top: 32}} border="top">
        {selectedTab === 'evaluations' ? (
          <TicksTable
            tabs={tabs}
            tickResultType={tickResultType}
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
        sensorDaemonStatus: daemonStatus(daemonType: "SENSOR") {
          id
          healthy
          required
        }
        ampDaemonStatus: daemonStatus(daemonType: "ASSET") {
          id
          healthy
          required
        }
      }
      ...InstanceHealthFragment
    }
  }

  ${SENSOR_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
`;

export const SENSOR_ASSET_SELECTIONS_QUERY = gql`
  query SensorAssetSelectionQuery($sensorSelector: SensorSelector!) {
    sensorOrError(sensorSelector: $sensorSelector) {
      ... on Sensor {
        id
        assetSelection {
          ...AutomationAssetSelectionFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${AUTOMATION_ASSET_SELECTION_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
