import {Box, ButtonGroup, Colors, NonIdealState, Page, Spinner} from '@dagster-io/ui-components';
import {useCallback, useMemo} from 'react';
import {Redirect, useParams} from 'react-router-dom';

import {SensorDetails} from './SensorDetails';
import {SENSOR_FRAGMENT} from './SensorFragment';
import {SensorInfo} from './SensorInfo';
import {SensorPreviousRuns} from './SensorPreviousRuns';
import {gql, useQuery} from '../apollo-client';
import {
  SensorAssetSelectionQuery,
  SensorAssetSelectionQueryVariables,
  SensorRootQuery,
  SensorRootQueryVariables,
} from './types/SensorRoot.types';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useMergedRefresh, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {AUTOMATION_ASSET_SELECTION_FRAGMENT} from '../automation/AutomationAssetSelectionFragment';
import {SensorType} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {
  TickHistoryTimeline,
  TickStatusFilter,
  TicksTable,
  useTickStatusFilter,
} from '../instigation/TickHistory';
import {TickTimelineControls, TickWindow, tickWindowMs} from '../instigation/TickTimelineControls';
import {useTimelineRange} from '../overview/OverviewTimelineRoot';
import {TickResultType} from '../ticks/TickStatusTag';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

const TICK_WINDOW_KEY = 'dagster.tick-timeline-window';

// Matches the lookahead the live timeline draws for itself, so the now indicator and any
// in-progress tick stay inside the window between refreshes.
const LOOKAHEAD_MINUTES = 1;

const validateTickWindow = (json: any): TickWindow =>
  json === '1' || json === '6' || json === '12' || json === '24' || json === 'live' ? json : 'live';

export const SensorRoot = ({repoAddress}: {repoAddress: RepoAddress}) => {
  useTrackPageView();

  const {sensorName} = useParams<{sensorName: string}>();
  useDocumentTitle(`Sensors | ${sensorName}`);

  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName,
  };

  // The status filter sits with the time controls because it narrows the timeline as well as
  // the table, and stays in effect while the Runs tab is showing.
  const {tickStatus, setTickStatus, statuses} = useTickStatusFilter();

  // The tick timeline and the tick table share one window, so paging through time updates both.
  // "Live" is the default and keeps the timeline on the last few minutes, refreshing every
  // second; the hour windows are for looking back at what a sensor did earlier.
  const [tickWindow, setTickWindow] = useStateWithStorage<TickWindow>(
    TICK_WINDOW_KEY,
    validateTickWindow,
  );
  // The window size is always supplied here, so the hook's own hour-window state is never
  // consulted and `tickWindow` stays the only thing that decides what is shown.
  const {rangeMs, offsetMsec, onPageEarlier, onPageLater, onPageNow} = useTimelineRange({
    lookaheadHours: LOOKAHEAD_MINUTES / 60,
    windowMsOverride: tickWindowMs(tickWindow),
  });

  const onSelectTickWindow = useCallback(
    (nextWindow: TickWindow) => {
      setTickWindow(nextWindow);
      onPageNow();
    },
    [onPageNow, setTickWindow],
  );

  // Live only means live while the window still ends at the present; paging back turns it
  // into an ordinary window of the last few minutes of some earlier time.
  const windowRangeMs = tickWindow === 'live' && offsetMsec === 0 ? undefined : rangeMs;

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
      {selectedTab === 'evaluations' ? (
        <>
          {/* The window and status controls narrow the timeline and the tick list below it,
          and have nothing to say about the runs feed, so they head this tab alone. */}
          <Box
            padding={{vertical: 12, horizontal: 24}}
            flex={{
              direction: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 16,
            }}
          >
            {tabs}
            <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
              <TickStatusFilter status={tickStatus} onChange={setTickStatus} />
              <TickTimelineControls
                tickWindow={tickWindow}
                onSelectTickWindow={onSelectTickWindow}
                onPageEarlier={onPageEarlier}
                onPageNow={onPageNow}
                onPageLater={onPageLater}
              />
            </Box>
          </Box>
          <TickHistoryTimeline
            tickResultType={tickResultType}
            repoAddress={repoAddress}
            name={sensorOrError.name}
            rangeMs={windowRangeMs}
            statuses={statuses}
          />
          <Box margin={{top: 32}} border="top">
            <TicksTable
              tickResultType={tickResultType}
              repoAddress={repoAddress}
              name={sensorOrError.name}
              rangeMs={windowRangeMs}
              windowKey={`${tickWindow}:${offsetMsec}`}
            />
          </Box>
        </>
      ) : (
        // The runs feed has its own action bar, so the tabs ride along in it rather than
        // sitting in a bar of their own.
        <Box border="top">
          <SensorPreviousRuns repoAddress={repoAddress} sensor={sensorOrError} tabs={tabs} />
        </Box>
      )}
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
