import {gql, useQuery} from '@apollo/client';
import {Button, ButtonGroup, Colors, Spinner} from '@blueprintjs/core';
import {TimeUnit} from 'chart.js';
import * as React from 'react';
import {Line, ChartComponentProps} from 'react-chartjs-2';
import styled from 'styled-components/macro';

import {TICK_TAG_FRAGMENT, TickTag} from 'src/JobTick';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {JobHistoryFragment, JobHistoryFragment_ticks} from 'src/jobs/types/JobHistoryFragment';
import {ScheduleTickHistoryQuery} from 'src/jobs/types/ScheduleTickHistoryQuery';
import {SensorTickHistoryQuery} from 'src/jobs/types/SensorTickHistoryQuery';
import {TimestampDisplay} from 'src/schedules/TimestampDisplay';
import {ScheduleFragment} from 'src/schedules/types/ScheduleFragment';
import {SensorFragment} from 'src/sensors/types/SensorFragment';
import {JobTickStatus} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Table} from 'src/ui/Table';
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
}> = ({schedule, repoAddress}) => {
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
  return <JobTickHistory jobState={data.scheduleOrError.scheduleState} showSkipped={true} />;
};

export const SensorTickHistory: React.FC<{
  sensor: SensorFragment;
  repoAddress: RepoAddress;
}> = ({sensor, repoAddress}) => {
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
  return <JobTickHistory jobState={data.sensorOrError.sensorState} showSkipped={false} />;
};

const JobTickHistory = ({
  jobState,
  showSkipped,
}: {
  jobState: JobHistoryFragment;
  showSkipped: boolean;
}) => {
  const [selectedTick, setSelectedTick] = React.useState<JobHistoryFragment_ticks | null>(null);
  const [shownStates, setShownStates] = React.useState<ShownStatusState>(
    DEFAULT_SHOWN_STATUS_STATE,
  );
  const {ticks} = jobState;
  const displayedTicks = ticks.filter((tick) =>
    tick.status === JobTickStatus.SKIPPED
      ? showSkipped && shownStates[tick.status]
      : shownStates[tick.status],
  );
  const StatusButton = ({status}: {status: JobTickStatus}) => {
    return (
      <Button
        title={STATUS_TEXT_MAP[status]}
        active={shownStates[status]}
        disabled={!ticks.filter((tick) => tick.status === status).length}
        onClick={() => setShownStates({...shownStates, [status]: !shownStates[status]})}
      >
        <Group direction="row" spacing={4} alignItems="center">
          <TickStatusDot status={status} />
          {STATUS_TEXT_MAP[status]}
        </Group>
      </Button>
    );
  };

  return (
    <Group direction="column" spacing={12}>
      <Subheading>Tick History</Subheading>
      <ButtonGroup>
        <StatusButton status={JobTickStatus.SUCCESS} />
        <StatusButton status={JobTickStatus.FAILURE} />
        {showSkipped ? <StatusButton status={JobTickStatus.SKIPPED} /> : null}
      </ButtonGroup>
      {displayedTicks.length ? (
        <TickHistoryGraph
          ticks={displayedTicks}
          selectedTick={selectedTick}
          onSelectTick={setSelectedTick}
        />
      ) : (
        <Box margin={{vertical: 8}} flex={{justifyContent: 'center'}}>
          No ticks recorded
        </Box>
      )}
      <Box
        background={Colors.LIGHT_GRAY5}
        border={{side: 'all', width: 1, color: Colors.LIGHT_GRAY3}}
        padding={20}
        margin={{top: 20}}
        flex={{justifyContent: 'center'}}
      >
        {selectedTick ? (
          <TickTable ticks={[selectedTick]} />
        ) : (
          <span>
            No tick selected. Select a tick from the tick history timeline to view more details.
          </span>
        )}
      </Box>
    </Group>
  );
};

interface Bounds {
  min: number;
  max: number;
}

const TickHistoryGraph: React.FC<{
  ticks: JobHistoryFragment_ticks[];
  selectedTick: JobHistoryFragment_ticks | null;
  onSelectTick: (tick: JobHistoryFragment_ticks) => void;
}> = ({ticks, selectedTick, onSelectTick}) => {
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
      },
    ],
  };

  const calculateBounds = () => {
    if (bounds) {
      return bounds;
    }
    const dataMin = Math.min(...tickData.map((_) => _.x));
    const dataMax = Math.max(...tickData.map((_) => _.x));
    const buffer = (dataMax - dataMin) / 25;
    return {min: dataMin - buffer, max: dataMax + buffer};
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

  const options: ChartComponentProps['options'] = {
    scales: {
      yAxes: [{scaleLabel: {display: false}, ticks: {display: false}, gridLines: {display: false}}],
      xAxes: [
        {
          type: 'time',
          scaleLabel: {
            display: false,
          },
          bounds: 'ticks',
          ticks: {
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
          onZoomComplete: ({chart}: {chart: Chart}) => {
            const {min, max} = chart.options.scales?.xAxes?.[0].ticks || {};
            if (min && max) {
              setBounds({min, max});
            }
          },
        },
        pan: {
          enabled: true,
          mode: 'x',
        },
      },
    },
  };

  return (
    <div>
      <Line data={graphData} height={30} options={options} key="100%" />
      <Box flex={{justifyContent: 'center'}}>
        <div style={{fontSize: 13, opacity: 0.5}}>
          Tip: Scroll / pinch to zoom, drag to pan, click to see tick details
        </div>
      </Box>
    </div>
  );
};

const TickTable = ({ticks}: {ticks: JobHistoryFragment_ticks[]}) => (
  <Table style={{width: '100%'}}>
    <thead>
      <tr>
        <th>Evaluation Time</th>
        <th>Tick Status</th>
      </tr>
    </thead>
    <tbody>
      {ticks.map((tick) => (
        <tr key={tick.id}>
          <td>
            <TimestampDisplay timestamp={tick.timestamp} />
          </td>
          <td>
            <TickTag tick={tick} />
          </td>
        </tr>
      ))}
    </tbody>
  </Table>
);

const JOB_HISTORY_FRAGMENT = gql`
  fragment JobHistoryFragment on JobState {
    id
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

const TickStatusDot = styled.div<{
  status: JobTickStatus;
}>`
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 4px;
  align-self: center;
  background: ${({status}) => COLOR_MAP[status]};
`;
