import {gql, useQuery} from '@apollo/client';
import {Button, Checkbox, Classes, Colors, Dialog, Tabs, Tab} from '@blueprintjs/core';
import {TimeUnit} from 'chart.js';
import moment from 'moment-timezone';
import * as React from 'react';
import {Line, ChartComponentProps} from 'react-chartjs-2';

import {showCustomAlert} from 'src/app/CustomAlertProvider';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {TICK_TAG_FRAGMENT, RunList, TickTag} from 'src/jobs/JobTick';
import {LiveTickTimeline} from 'src/jobs/LiveTickTimeline';
import {
  JobTickHistoryQuery,
  JobTickHistoryQuery_jobStateOrError_JobState_ticks,
} from 'src/jobs/types/JobTickHistoryQuery';
import {TimestampDisplay} from 'src/schedules/TimestampDisplay';
import {JobTickStatus, JobType} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';
import {Spinner} from 'src/ui/Spinner';
import {Subheading} from 'src/ui/Text';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';

import 'chartjs-plugin-zoom';

const MIN_ZOOM_RANGE = 30 * 60 * 1000; // 30 minutes

const COLOR_MAP = {
  [JobTickStatus.SUCCESS]: Colors.BLUE3,
  [JobTickStatus.FAILURE]: Colors.RED3,
  [JobTickStatus.STARTED]: Colors.GRAY3,
  [JobTickStatus.SKIPPED]: Colors.GOLD3,
};

interface ShownStatusState {
  [JobTickStatus.SUCCESS]: boolean;
  [JobTickStatus.FAILURE]: boolean;
  [JobTickStatus.STARTED]: boolean;
  [JobTickStatus.SKIPPED]: boolean;
}

const DEFAULT_SHOWN_STATUS_STATE = {
  [JobTickStatus.SUCCESS]: true,
  [JobTickStatus.FAILURE]: true,
  [JobTickStatus.STARTED]: true,
  [JobTickStatus.SKIPPED]: true,
};
const STATUS_TEXT_MAP = {
  [JobTickStatus.SUCCESS]: 'Requested',
  [JobTickStatus.FAILURE]: 'Failed',
  [JobTickStatus.STARTED]: 'Started',
  [JobTickStatus.SKIPPED]: 'Skipped',
};

const TABS = [
  {
    id: 'recent',
    label: 'Recent',
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

type JobTick = JobTickHistoryQuery_jobStateOrError_JobState_ticks;
const MILLIS_PER_DAY = 86400 * 1000;

export const JobTickHistory = ({
  jobName,
  repoAddress,
  onHighlightRunIds,
  showRecent,
}: {
  jobName: string;
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
    JobTickHistoryQuery_jobStateOrError_JobState_ticks | undefined
  >();
  const selectedRange = TABS.find((x) => x.id === selectedTab)?.range;
  const {data} = useQuery<JobTickHistoryQuery>(JOB_TICK_HISTORY_QUERY, {
    variables: {
      jobSelector: {
        ...repoAddressToSelector(repoAddress),
        jobName,
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
          <Tab
            id={tab.id}
            key={tab.id}
            title={
              <ButtonLink underline={false} onClick={() => setSelectedTab(tab.id)}>
                {tab.label}
              </ButtonLink>
            }
          />
        ),
      )}
    </Tabs>
  );

  if (!data || data?.jobStateOrError.__typename !== 'JobState') {
    return (
      <Group direction="column" spacing={12}>
        <Subheading>Tick History</Subheading>
        {tabs}
        <Spinner purpose="section" />
      </Group>
    );
  }

  const {ticks, nextTick, jobType} = data.jobStateOrError;
  const displayedTicks = ticks.filter((tick) =>
    tick.status === JobTickStatus.SKIPPED
      ? jobType === JobType.SCHEDULE && shownStates[tick.status]
      : shownStates[tick.status],
  );
  const StatusFilter = ({status}: {status: JobTickStatus}) => (
    <Checkbox
      label={STATUS_TEXT_MAP[status]}
      checked={shownStates[status]}
      disabled={!ticks.filter((tick) => tick.status === status).length}
      onClick={() => setShownStates({...shownStates, [status]: !shownStates[status]})}
    />
  );
  const onTickClick = (tick?: JobTick) => {
    setSelectedTick(tick);
    if (!tick) {
      return;
    }
    if (tick.error && tick.status === JobTickStatus.FAILURE) {
      showCustomAlert({
        title: 'Python Error',
        body: <PythonErrorInfo error={tick.error} />,
      });
    }
  };
  const onTickHover = (tick?: JobTick) => {
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
      ) : (
        <>
          <Box flex={{justifyContent: 'flex-end'}}>
            <Group direction="row" spacing={16}>
              <StatusFilter status={JobTickStatus.SUCCESS} />
              <StatusFilter status={JobTickStatus.FAILURE} />
              {jobType === JobType.SCHEDULE ? (
                <StatusFilter status={JobTickStatus.SKIPPED} />
              ) : null}
            </Group>
          </Box>
          {displayedTicks.length || selectedTab !== 'all' ? (
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
          ) : (
            <Box margin={{vertical: 8}} flex={{justifyContent: 'center'}}>
              No ticks recorded
            </Box>
          )}
        </>
      )}
      <Dialog
        isOpen={
          selectedTick &&
          (selectedTick.status === JobTickStatus.SUCCESS ||
            selectedTick.status === JobTickStatus.SKIPPED)
        }
        onClose={() => setSelectedTick(undefined)}
        style={{
          width: selectedTick && selectedTick.status === JobTickStatus.SUCCESS ? '90vw' : '50vw',
        }}
        title={selectedTick ? <TimestampDisplay timestamp={selectedTick.timestamp} /> : null}
      >
        {selectedTick ? (
          <Box background={Colors.WHITE} padding={16} margin={{bottom: 16}}>
            {selectedTick.status === JobTickStatus.SUCCESS ? (
              <RunList runIds={selectedTick?.runIds} />
            ) : null}
            {selectedTick.status === JobTickStatus.SKIPPED ? (
              <Group direction="row" spacing={16}>
                <TickTag tick={selectedTick} />
                <span>{selectedTick.skipReason || 'No skip reason provided'}</span>
              </Group>
            ) : null}
          </Box>
        ) : null}
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button intent="primary" onClick={() => setSelectedTick(undefined)}>
              OK
            </Button>
          </div>
        </div>
      </Dialog>
    </Group>
  );
};

interface Bounds {
  min: number;
  max: number;
}

const TickHistoryGraph: React.FC<{
  ticks: JobTick[];
  selectedTick?: JobTick;
  onSelectTick: (tick: JobTick) => void;
  onHoverTick: (tick?: JobTick) => void;
  selectedTab: string;
  maxBounds?: Bounds;
}> = ({ticks, selectedTick, onSelectTick, onHoverTick, selectedTab, maxBounds}) => {
  const [bounds, setBounds] = React.useState<Bounds | null>(null);
  const [hoveredTick, setHoveredTick] = React.useState<JobTick | undefined>();
  React.useEffect(() => {
    setBounds(null);
  }, [selectedTab]);
  const tickData = ticks.map((tick) => ({x: 1000 * tick.timestamp, y: 0}));
  const graphData: ChartComponentProps['data'] = {
    labels: ['ticks'],
    datasets: [
      {
        label: 'ticks',
        data: tickData,
        borderColor: Colors.LIGHT_GRAY4,
        borderWidth: 0,
        backgroundColor: 'rgba(0,0,0,0)',
        pointBackgroundColor: ticks.map((tick) => COLOR_MAP[tick.status]),
        pointBorderWidth: 1,
        pointBorderColor: ticks.map((tick) =>
          selectedTick && selectedTick.id === tick.id ? Colors.DARK_GRAY5 : COLOR_MAP[tick.status],
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
    const now = Date.now();
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

  const options: ChartComponentProps['options'] = {
    title: {
      display: !!title,
      text: title,
    },
    scales: {
      yAxes: [{scaleLabel: {display: false}, ticks: {display: false}, gridLines: {display: false}}],
      xAxes: [
        {
          type: 'time',
          scaleLabel: {
            display: false,
          },
          bounds: 'ticks',
          gridLines: {display: true, drawBorder: true},
          ticks: {
            source: 'auto',
            ...calculateBounds(),
          },
          time: {
            minUnit: calculateUnit(),
          },
        },
      ],
    },
    legend: {
      display: false,
    },
    tooltips: {
      displayColors: false,
      callbacks: {
        title: function (_item, _data) {
          if (!hoveredTick) {
            return '';
          }
          return moment(hoveredTick.timestamp * 1000).format('MMM D, YYYY h:mm:ss A z');
        },
        label: function (_tooltipItem, _data) {
          if (!hoveredTick) {
            return '';
          }
          if (hoveredTick.status === JobTickStatus.SKIPPED && hoveredTick.skipReason) {
            return snippet(hoveredTick.skipReason);
          }
          if (hoveredTick.status === JobTickStatus.SUCCESS && hoveredTick.runIds.length) {
            return hoveredTick.runIds;
          }
          if (hoveredTick.status == JobTickStatus.FAILURE && hoveredTick.error?.message) {
            return snippet(hoveredTick.error.message);
          }
          return '';
        },
      },
    },

    onHover: (event: MouseEvent, activeElements: any[]) => {
      if (event?.target instanceof HTMLElement) {
        event.target.style.cursor = activeElements.length ? 'pointer' : 'default';
      }

      if (activeElements.length && activeElements[0] && activeElements[0]._index < ticks.length) {
        const tick = ticks[activeElements[0]._index];
        setHoveredTick(tick);
        onHoverTick(tick);
      } else {
        onHoverTick(undefined);
      }
    },

    onClick: (_event: MouseEvent, activeElements: any[]) => {
      if (!activeElements.length) {
        return;
      }
      const [item] = activeElements;
      if (item._datasetIndex === undefined || item._index === undefined) {
        return;
      }
      const tick = ticks[item._index];
      onSelectTick(tick);
    },
    plugins: {
      zoom: {
        zoom: {
          enabled: true,
          mode: 'x',
          rangeMin: {
            x: getMaxBounds().min,
          },
          rangeMax: {
            x: getMaxBounds().max,
          },
          onZoom: ({chart}: {chart: Chart}) => {
            const {min, max} = chart.options.scales?.xAxes?.[0].ticks || {};
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
          rangeMin: {
            x: getMaxBounds().min,
          },
          rangeMax: {
            x: getMaxBounds().max,
          },
          enabled: true,
          mode: 'x',
          onPan: ({chart}: {chart: Chart}) => {
            const {min, max} = chart.options.scales?.xAxes?.[0].ticks || {};
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
      <Line data={graphData} height={30} options={options} key="100%" />
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
  query JobTickHistoryQuery($jobSelector: JobSelector!, $dayRange: Int, $limit: Int) {
    jobStateOrError(jobSelector: $jobSelector) {
      __typename
      ... on JobState {
        id
        jobType
        nextTick {
          timestamp
        }
        ticks(dayRange: $dayRange, limit: $limit) {
          id
          status
          timestamp
          skipReason
          runIds
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
