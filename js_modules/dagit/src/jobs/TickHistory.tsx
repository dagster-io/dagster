import {gql, useQuery} from '@apollo/client';
import {Button, Checkbox, Classes, Colors, Dialog, Spinner, Tabs, Tab} from '@blueprintjs/core';
import {TimeUnit} from 'chart.js';
import moment from 'moment-timezone';
import * as React from 'react';
import {Line, ChartComponentProps} from 'react-chartjs-2';

import {showCustomAlert} from 'src/CustomAlertProvider';
import {TICK_TAG_FRAGMENT, RunList, TickTag} from 'src/JobTick';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {JobHistoryFragment, JobHistoryFragment_ticks} from 'src/jobs/types/JobHistoryFragment';
import {ScheduleTickHistoryQuery} from 'src/jobs/types/ScheduleTickHistoryQuery';
import {SensorTickHistoryQuery} from 'src/jobs/types/SensorTickHistoryQuery';
import {TimestampDisplay} from 'src/schedules/TimestampDisplay';
import {ScheduleFragment} from 'src/schedules/types/ScheduleFragment';
import {SensorTimeline} from 'src/sensors/SensorTimeline';
import {SensorFragment} from 'src/sensors/types/SensorFragment';
import {JobTickStatus, JobType} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';
import {Subheading} from 'src/ui/Text';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';

import 'chartjs-plugin-zoom';

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

export const ScheduleTickHistory: React.FC<{
  schedule: ScheduleFragment;
  repoAddress: RepoAddress;
  onHighlightRunIds: (runIds: string[]) => void;
}> = ({schedule, repoAddress, onHighlightRunIds}) => {
  const scheduleSelector = {
    ...repoAddressToSelector(repoAddress),
    scheduleName: schedule.name,
  };
  const {data} = useQuery<ScheduleTickHistoryQuery>(SCHEDULE_TICK_HISTORY_QUERY, {
    variables: {
      scheduleSelector,
    },
    fetchPolicy: 'cache-and-network',
    pollInterval: 15 * 1000,
    partialRefetch: true,
  });

  if (!data || data?.scheduleOrError.__typename !== 'Schedule') {
    return <Spinner />;
  }

  return (
    <Box margin={{vertical: 20}}>
      <JobTickHistory
        jobName={schedule.name}
        jobState={data.scheduleOrError.scheduleState}
        repoAddress={repoAddress}
        onHighlightRunIds={onHighlightRunIds}
      />
    </Box>
  );
};

export const SensorTickHistory: React.FC<{
  sensor: SensorFragment;
  repoAddress: RepoAddress;
  daemonHealth: boolean | null;
  onHighlightRunIds: (runIds: string[]) => void;
}> = ({sensor, repoAddress, onHighlightRunIds}) => {
  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName: sensor.name,
  };
  const {data} = useQuery<SensorTickHistoryQuery>(SENSOR_TICK_HISTORY_QUERY, {
    variables: {
      sensorSelector,
    },
    fetchPolicy: 'cache-and-network',
    pollInterval: 15 * 1000,
    partialRefetch: true,
  });

  if (!data || data?.sensorOrError.__typename !== 'Sensor') {
    return <Spinner />;
  }

  return (
    <Box margin={{vertical: 20}}>
      <JobTickHistory
        jobName={sensor.name}
        jobState={data.sensorOrError.sensorState}
        repoAddress={repoAddress}
        onHighlightRunIds={onHighlightRunIds}
      />
    </Box>
  );
};

const JobTickHistory = ({
  jobName,
  jobState,
  repoAddress,
  onHighlightRunIds,
}: {
  jobName: string;
  jobState: JobHistoryFragment;
  repoAddress: RepoAddress;
  onHighlightRunIds: (runIds: string[]) => void;
}) => {
  const [shownStates, setShownStates] = React.useState<ShownStatusState>(
    DEFAULT_SHOWN_STATUS_STATE,
  );
  const [selectedTab, setSelectedTab] = React.useState<string>('recent');
  const [selectedTick, setSelectedTick] = React.useState<JobHistoryFragment_ticks | undefined>();

  const {ticks} = jobState;
  const displayedTicks = ticks.filter((tick) =>
    tick.status === JobTickStatus.SKIPPED
      ? jobState.jobType === JobType.SCHEDULE && shownStates[tick.status]
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
  const onTickClick = (tick?: JobHistoryFragment_ticks) => {
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

  return (
    <Group direction="column" spacing={12}>
      <Subheading>Tick History</Subheading>
      {jobState.jobType === JobType.SENSOR ? (
        <Tabs selectedTabId={selectedTab}>
          <Tab
            id="recent"
            title={
              <ButtonLink underline={false} onClick={() => setSelectedTab('recent')}>
                Recent
              </ButtonLink>
            }
          />
          <Tab
            id="history"
            title={
              <ButtonLink underline={false} onClick={() => setSelectedTab('history')}>
                All
              </ButtonLink>
            }
          />
        </Tabs>
      ) : null}
      {jobState.jobType === JobType.SENSOR && selectedTab === 'recent' ? (
        <SensorTimeline
          repoAddress={repoAddress}
          sensorName={jobName}
          onHighlightRunIds={onHighlightRunIds}
          onSelectTick={onTickClick}
        />
      ) : (
        <>
          <Box flex={{justifyContent: 'flex-end'}}>
            <Group direction="row" spacing={16}>
              <StatusFilter status={JobTickStatus.SUCCESS} />
              <StatusFilter status={JobTickStatus.FAILURE} />
              {jobState.jobType === JobType.SCHEDULE ? (
                <StatusFilter status={JobTickStatus.SKIPPED} />
              ) : null}
            </Group>
          </Box>
          {displayedTicks.length ? (
            <TickHistoryGraph
              ticks={displayedTicks}
              selectedTick={selectedTick}
              onSelectTick={onTickClick}
              onHighlightRunIds={onHighlightRunIds}
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
  ticks: JobHistoryFragment_ticks[];
  selectedTick?: JobHistoryFragment_ticks;
  onSelectTick: (tick: JobHistoryFragment_ticks) => void;
  onHighlightRunIds: (runIds: string[]) => void;
}> = ({ticks, selectedTick, onSelectTick, onHighlightRunIds}) => {
  const [bounds, setBounds] = React.useState<Bounds | null>(null);
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

  const dataMin = Math.min(...tickData.map((_) => _.x));
  const dataMax = Math.max(...tickData.map((_) => _.x));
  const buffer = (dataMax - dataMin) / 25;
  const dataBounds = {min: dataMin - buffer, max: dataMax + buffer};

  const calculateBounds = () => {
    if (bounds) {
      return bounds;
    }
    return dataBounds;
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
        label: function (tooltipItem, _data) {
          if (tooltipItem.index === undefined || tooltipItem.index === ticks.length) {
            return '';
          }
          const tick = ticks[tooltipItem.index];
          if (tick.status === JobTickStatus.SKIPPED && tick.skipReason) {
            return tick.skipReason;
          }
          if (tick.status === JobTickStatus.SUCCESS && tick.runIds.length) {
            return tick.runIds;
          }
          if (tick.status == JobTickStatus.FAILURE && tick.error?.message) {
            return tick.error.message;
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
        onHighlightRunIds(tick.runIds || []);
      } else {
        onHighlightRunIds([]);
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
            x: dataBounds.min,
          },
          rangeMax: {
            x: dataBounds.max,
          },
          onZoom: ({chart}: {chart: Chart}) => {
            const {min, max} = chart.options.scales?.xAxes?.[0].ticks || {};
            if (min && max) {
              setBounds({min, max});
            }
          },
        },
        pan: {
          rangeMin: {
            x: dataBounds.min,
          },
          rangeMax: {
            x: dataBounds.max,
          },
          enabled: true,
          mode: 'x',
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

const JOB_HISTORY_FRAGMENT = gql`
  fragment JobHistoryFragment on JobState {
    id
    jobType
    ticks {
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
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${TICK_TAG_FRAGMENT}
`;

const SCHEDULE_TICK_HISTORY_QUERY = gql`
  query ScheduleTickHistoryQuery($scheduleSelector: ScheduleSelector!) {
    scheduleOrError(scheduleSelector: $scheduleSelector) {
      __typename
      ... on Schedule {
        id
        scheduleState {
          id
          ...JobHistoryFragment
        }
      }
    }
  }
  ${JOB_HISTORY_FRAGMENT}
`;

const SENSOR_TICK_HISTORY_QUERY = gql`
  query SensorTickHistoryQuery($sensorSelector: SensorSelector!) {
    sensorOrError(sensorSelector: $sensorSelector) {
      __typename
      ... on Sensor {
        id
        sensorState {
          id
          ...JobHistoryFragment
        }
      }
    }
  }
  ${JOB_HISTORY_FRAGMENT}
`;
