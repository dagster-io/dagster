import {gql, useQuery} from '@apollo/client';
import {ActiveElement, Chart, TimeUnit} from 'chart.js';
import 'chartjs-adapter-date-fns';
import zoomPlugin from 'chartjs-plugin-zoom';
import moment from 'moment-timezone';
import * as React from 'react';
import {Line} from 'react-chartjs-2';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {InstigationTickStatus, InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {ButtonLink} from '../ui/ButtonLink';
import {Checkbox} from '../ui/Checkbox';
import {ColorsWIP} from '../ui/Colors';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';
import {Group} from '../ui/Group';
import {NonIdealState} from '../ui/NonIdealState';
import {Spinner} from '../ui/Spinner';
import {Tab, Tabs} from '../ui/Tabs';
import {Subheading} from '../ui/Text';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {FailedRunList, RunList, TickTag, TICK_TAG_FRAGMENT} from './InstigationTick';
import {LiveTickTimeline} from './LiveTickTimeline';
import {
  TickHistoryQuery,
  TickHistoryQuery_instigationStateOrError_InstigationState_ticks,
} from './types/TickHistoryQuery';

Chart.register(zoomPlugin);

const MIN_ZOOM_RANGE = 30 * 60 * 1000; // 30 minutes

const COLOR_MAP = {
  [InstigationTickStatus.SUCCESS]: ColorsWIP.Blue500,
  [InstigationTickStatus.FAILURE]: ColorsWIP.Red500,
  [InstigationTickStatus.STARTED]: ColorsWIP.Gray400,
  [InstigationTickStatus.SKIPPED]: ColorsWIP.Yellow500,
};

interface ShownStatusState {
  [InstigationTickStatus.SUCCESS]: boolean;
  [InstigationTickStatus.FAILURE]: boolean;
  [InstigationTickStatus.STARTED]: boolean;
  [InstigationTickStatus.SKIPPED]: boolean;
}

const DEFAULT_SHOWN_STATUS_STATE = {
  [InstigationTickStatus.SUCCESS]: true,
  [InstigationTickStatus.FAILURE]: true,
  [InstigationTickStatus.STARTED]: true,
  [InstigationTickStatus.SKIPPED]: true,
};
const STATUS_TEXT_MAP = {
  [InstigationTickStatus.SUCCESS]: 'Requested',
  [InstigationTickStatus.FAILURE]: 'Failed',
  [InstigationTickStatus.STARTED]: 'Started',
  [InstigationTickStatus.SKIPPED]: 'Skipped',
};

const TABS = [
  {
    id: 'recent',
    label: 'Recent',
    range: 1,
  },
  {
    id: '1d',
    label: '1 day',
    range: 1,
  },
  {
    id: '7d',
    label: '7 days',
    range: 7,
  },
  {
    id: '14d',
    label: '14 days',
    range: 14,
  },
  {
    id: '30d',
    label: '30 days',
    range: 30,
  },
  {id: 'all', label: 'All'},
];

type InstigationTick = TickHistoryQuery_instigationStateOrError_InstigationState_ticks;
const MILLIS_PER_DAY = 86400 * 1000;

export const TickHistory = ({
  name,
  repoAddress,
  onHighlightRunIds,
  showRecent,
}: {
  name: string;
  repoAddress: RepoAddress;
  onHighlightRunIds: (runIds: string[]) => void;
  showRecent?: boolean;
}) => {
  const [selectedTab, setSelectedTab] = React.useState<string>('recent');
  const [shownStates, setShownStates] = React.useState<ShownStatusState>(
    DEFAULT_SHOWN_STATUS_STATE,
  );
  const [pollingPaused, pausePolling] = React.useState<boolean>(false);
  const [selectedTick, setSelectedTick] = React.useState<
    TickHistoryQuery_instigationStateOrError_InstigationState_ticks | undefined
  >();
  React.useEffect(() => {
    if (!showRecent && selectedTab === 'recent') {
      setSelectedTab('1d');
    }
  }, [selectedTab, showRecent]);
  const selectedRange = TABS.find((x) => x.id === selectedTab)?.range;
  const {data} = useQuery<TickHistoryQuery>(JOB_TICK_HISTORY_QUERY, {
    variables: {
      instigationSelector: {
        ...repoAddressToSelector(repoAddress),
        name,
      },
      dayRange: selectedRange,
      limit: selectedTab === 'recent' ? 15 : undefined,
    },
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    pollInterval: selectedTab === 'recent' && !pollingPaused ? 1000 : 0,
  });

  const tabs = (
    <Tabs selectedTabId={selectedTab}>
      {TABS.map((tab) =>
        tab.id === 'recent' && !showRecent ? null : (
          <Tab id={tab.id} key={tab.id} title={tab.label} onClick={() => setSelectedTab(tab.id)} />
        ),
      ).filter(Boolean)}
    </Tabs>
  );

  if (!data) {
    return (
      <Group direction="column" spacing={12}>
        <Subheading>Tick History</Subheading>
        {tabs}
        <Spinner purpose="section" />
      </Group>
    );
  }

  if (data.instigationStateOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={data.instigationStateOrError} />;
  }

  const {ticks, nextTick, instigationType} = data.instigationStateOrError;
  const displayedTicks = ticks.filter((tick) =>
    tick.status === InstigationTickStatus.SKIPPED
      ? instigationType === InstigationType.SCHEDULE && shownStates[tick.status]
      : shownStates[tick.status],
  );
  const StatusFilter = ({status}: {status: InstigationTickStatus}) => (
    <Checkbox
      label={STATUS_TEXT_MAP[status]}
      checked={shownStates[status]}
      disabled={!ticks.filter((tick) => tick.status === status).length}
      onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
        setShownStates({...shownStates, [status]: e.target.checked});
      }}
    />
  );
  const onTickClick = (tick?: InstigationTick) => {
    setSelectedTick(tick);
    if (!tick) {
      return;
    }
    if (tick.error && tick.status === InstigationTickStatus.FAILURE) {
      showCustomAlert({
        title: 'Python Error',
        body: <PythonErrorInfo error={tick.error} />,
      });
    }
  };
  const onTickHover = (tick?: InstigationTick) => {
    if (!tick) {
      pausePolling(false);
    }
    if (tick?.runIds) {
      onHighlightRunIds(tick.runIds);
      pausePolling(true);
    }
  };

  const now = Date.now();
  return (
    <Group direction="column" spacing={12}>
      <Subheading>Tick History</Subheading>
      {tabs}
      {showRecent && selectedTab === 'recent' ? (
        <LiveTickTimeline
          ticks={ticks}
          nextTick={nextTick}
          onHoverTick={onTickHover}
          onSelectTick={onTickClick}
        />
      ) : ticks.length ? (
        <>
          <Box flex={{justifyContent: 'flex-end'}}>
            <Group direction="row" spacing={16}>
              <StatusFilter status={InstigationTickStatus.SUCCESS} />
              <StatusFilter status={InstigationTickStatus.FAILURE} />
              {instigationType === InstigationType.SCHEDULE ? (
                <StatusFilter status={InstigationTickStatus.SKIPPED} />
              ) : null}
            </Group>
          </Box>
          <TickHistoryGraph
            ticks={displayedTicks}
            selectedTick={selectedTick}
            onSelectTick={onTickClick}
            onHoverTick={onTickHover}
            selectedTab={selectedTab}
            maxBounds={
              selectedTab === 'all'
                ? undefined
                : {min: now - (selectedRange || 0) * MILLIS_PER_DAY, max: Date.now()}
            }
          />
        </>
      ) : (
        <Box margin={{top: 16, bottom: 32}} flex={{justifyContent: 'center'}}>
          <NonIdealState icon="no-results" description="No ticks to display" />
        </Box>
      )}
      <DialogWIP
        isOpen={
          !!(
            selectedTick &&
            (selectedTick.status === InstigationTickStatus.SUCCESS ||
              selectedTick.status === InstigationTickStatus.SKIPPED)
          )
        }
        onClose={() => setSelectedTick(undefined)}
        style={{
          width:
            selectedTick && selectedTick.status === InstigationTickStatus.SUCCESS ? '90vw' : '50vw',
        }}
        title={selectedTick ? <TimestampDisplay timestamp={selectedTick.timestamp} /> : null}
      >
        {selectedTick ? (
          <DialogBody>
            {selectedTick.status === InstigationTickStatus.SUCCESS ? (
              selectedTick.runIds.length ? (
                <RunList runIds={selectedTick.runIds} />
              ) : (
                <FailedRunList originRunIds={selectedTick.originRunIds} />
              )
            ) : null}
            {selectedTick.status === InstigationTickStatus.SKIPPED ? (
              <Group direction="row" spacing={16}>
                <TickTag tick={selectedTick} />
                <span>{selectedTick.skipReason || 'No skip reason provided'}</span>
              </Group>
            ) : null}
          </DialogBody>
        ) : null}
        <DialogFooter>
          <ButtonWIP intent="primary" onClick={() => setSelectedTick(undefined)}>
            OK
          </ButtonWIP>
        </DialogFooter>
      </DialogWIP>
    </Group>
  );
};

interface Bounds {
  min: number;
  max: number;
}

const TickHistoryGraph: React.FC<{
  ticks: InstigationTick[];
  selectedTick?: InstigationTick;
  onSelectTick: (tick: InstigationTick) => void;
  onHoverTick: (tick?: InstigationTick) => void;
  selectedTab: string;
  maxBounds?: Bounds;
}> = ({ticks, selectedTick, onSelectTick, onHoverTick, selectedTab, maxBounds}) => {
  const [bounds, setBounds] = React.useState<Bounds | null>(null);
  const [hoveredTick, setHoveredTick] = React.useState<InstigationTick | undefined>();
  const [now] = React.useState(() => Date.now());

  React.useEffect(() => {
    setBounds(null);
  }, [selectedTab]);

  const tickData = ticks.map((tick) => ({x: 1000 * tick.timestamp, y: 0}));
  const graphData = {
    labels: ['ticks'],
    datasets: [
      {
        label: 'ticks',
        data: tickData,
        borderColor: ColorsWIP.Gray100,
        borderWidth: 0,
        backgroundColor: 'rgba(0,0,0,0)',
        pointBackgroundColor: ticks.map((tick) => COLOR_MAP[tick.status]),
        pointBorderWidth: 1,
        pointBorderColor: ticks.map((tick) =>
          selectedTick && selectedTick.id === tick.id ? ColorsWIP.Gray700 : COLOR_MAP[tick.status],
        ),
        pointRadius: ticks.map((tick) => (selectedTick && selectedTick.id === tick.id ? 5 : 3)),
        pointHoverBorderWidth: 1,
        pointHoverRadius: 5,
        showLine: true,
      },
    ],
  };

  const getMaxBounds = () => {
    if (maxBounds) {
      return maxBounds;
    }
    const dataMin = Math.min(...tickData.map((_) => _.x));
    const dataMax = Math.max(...tickData.map((_) => _.x));
    const buffer = (dataMax - dataMin) / 25;
    return {
      min: dataMax ? dataMin - buffer : now - MIN_ZOOM_RANGE,
      max: dataMax ? dataMax + buffer : now,
    };
  };

  const calculateBounds = () => {
    if (bounds) {
      return bounds;
    }
    return getMaxBounds();
  };

  const calculateUnit: () => TimeUnit = () => {
    const {min, max} = calculateBounds();
    const range = max - min;
    const factor = 2;
    const hour = 3600000;
    const day = 24 * hour;
    const month = 30 * day;
    const year = 365 * day;

    if (range < factor * hour) {
      return 'minute';
    }
    if (range < factor * day) {
      return 'hour';
    }
    if (range < factor * month) {
      return 'day';
    }
    if (range < factor * year) {
      return 'month';
    }
    return 'year';
  };

  const dateFormat = (x: number) => moment(x).format('MMM D');
  const snippet = (x: string, length = 100, buffer = 20) => {
    const snipped = x.slice(0, length);
    return snipped.length < x.length - buffer ? `${snipped}...` : x;
  };

  const title = bounds
    ? dateFormat(bounds.min) === dateFormat(bounds.max)
      ? dateFormat(bounds.min)
      : `${dateFormat(bounds.min)} - ${dateFormat(bounds.max)}`
    : undefined;

  const options = {
    indexAxis: 'x',
    scales: {
      y: {id: 'y', display: false},
      x: {
        id: 'x',
        type: 'time',
        title: {
          display: false,
        },
        bounds: 'ticks',
        grid: {display: true, drawBorder: true},
        ticks: {
          source: 'auto',
        },
        ...calculateBounds(),
        time: {
          minUnit: calculateUnit(),
        },
      },
    },

    onHover: (event: MouseEvent, activeElements: ActiveElement[]) => {
      if (event?.target instanceof HTMLElement) {
        event.target.style.cursor = activeElements.length ? 'pointer' : 'default';
      }

      if (activeElements.length && activeElements[0] && activeElements[0].index < ticks.length) {
        const tick = ticks[activeElements[0].index];
        setHoveredTick(tick);
        onHoverTick(tick);
      } else {
        onHoverTick(undefined);
      }
    },

    onClick: (_event: MouseEvent, activeElements: ActiveElement[]) => {
      if (!activeElements.length) {
        return;
      }
      const [item] = activeElements;
      if (item.datasetIndex === undefined || item.index === undefined) {
        return;
      }
      const tick = ticks[item.index];
      onSelectTick(tick);
    },

    plugins: {
      title: {
        display: !!title,
        text: title,
      },
      legend: {
        display: false,
      },
      tooltip: {
        displayColors: false,
        callbacks: {
          title: () => {
            if (!hoveredTick) {
              return '';
            }
            return moment(hoveredTick.timestamp * 1000).format('MMM D, YYYY h:mm:ss A z');
          },
          label: () => {
            if (!hoveredTick) {
              return '';
            }
            if (hoveredTick.status === InstigationTickStatus.SKIPPED && hoveredTick.skipReason) {
              return snippet(hoveredTick.skipReason);
            }
            if (hoveredTick.status === InstigationTickStatus.SUCCESS && hoveredTick.runIds.length) {
              return hoveredTick.runIds;
            }
            if (
              hoveredTick.status === InstigationTickStatus.FAILURE &&
              hoveredTick.error?.message
            ) {
              return snippet(hoveredTick.error.message);
            }
            return '';
          },
        },
      },
      zoom: {
        limits: {
          x: {
            min: getMaxBounds().min,
            max: getMaxBounds().max,
          },
        },
        zoom: {
          mode: 'x',
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true,
          },
          onZoom: ({chart}: {chart: Chart}) => {
            const {min, max} = chart.scales.x;
            if (min && max) {
              const diff = max - min;
              if (diff > MIN_ZOOM_RANGE) {
                setBounds({min, max});
              } else if (bounds) {
                const offset = (bounds.max - bounds.min - MIN_ZOOM_RANGE) / 2;
                setBounds({min: bounds.min + offset, max: bounds.max - offset});
              } else {
                const offset = (getMaxBounds().max - getMaxBounds().min - MIN_ZOOM_RANGE) / 2;
                setBounds({min: getMaxBounds().min + offset, max: getMaxBounds().max - offset});
              }
            }
          },
        },
        pan: {
          enabled: true,
          mode: 'x',
          onPan: ({chart}: {chart: Chart}) => {
            const {min, max} = chart.scales.x;
            if (min && max) {
              setBounds({min, max});
            }
          },
        },
      },
    },
  };

  return (
    <div>
      <Line type="line" data={graphData} options={options} height={30} />
      <div style={{fontSize: 13, opacity: 0.5}}>
        <Box flex={{justifyContent: 'center'}} margin={{top: 8}}>
          Tip: Scroll / pinch to zoom, drag to pan, click to see tick details.
          {bounds ? (
            <Box margin={{left: 8}}>
              <ButtonLink onClick={() => setBounds(null)}>Reset zoom</ButtonLink>
            </Box>
          ) : null}
        </Box>
      </div>
    </div>
  );
};

const JOB_TICK_HISTORY_QUERY = gql`
  query TickHistoryQuery($instigationSelector: InstigationSelector!, $dayRange: Int, $limit: Int) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      __typename
      ... on InstigationState {
        id
        instigationType
        nextTick {
          timestamp
        }
        ticks(dayRange: $dayRange, limit: $limit) {
          id
          status
          timestamp
          skipReason
          runIds
          originRunIds
          error {
            ...PythonErrorFragment
          }
          ...TickTagFragment
        }
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
  ${TICK_TAG_FRAGMENT}
`;
