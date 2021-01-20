import {gql, useQuery} from '@apollo/client';
import {Colors, Spinner} from '@blueprintjs/core';
import * as React from 'react';
import {Line, ChartComponentProps} from 'react-chartjs-2';

import {PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {JobHistoryFragment_ticks} from 'src/jobs/types/JobHistoryFragment';
import {
  SensorTimelineQuery,
  SensorTimelineQuery_sensorOrError_Sensor_nextTick,
  SensorTimelineQuery_sensorOrError_Sensor_sensorState_ticks,
} from 'src/sensors/types/SensorTimelineQuery';
import {JobTickStatus} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';

type SensorTick = SensorTimelineQuery_sensorOrError_Sensor_sensorState_ticks;
type FutureTick = SensorTimelineQuery_sensorOrError_Sensor_nextTick;

const COLOR_MAP = {
  [JobTickStatus.SUCCESS]: Colors.BLUE3,
  [JobTickStatus.FAILURE]: Colors.RED3,
  [JobTickStatus.STARTED]: Colors.GRAY3,
  [JobTickStatus.SKIPPED]: Colors.GOLD3,
};

export const SensorTimeline: React.FC<{
  sensorName: string;
  repoAddress: RepoAddress;
  onHighlightRunIds: (runIds: string[]) => void;
  onSelectTick: (tick?: JobHistoryFragment_ticks) => void;
}> = ({sensorName, repoAddress, onHighlightRunIds, onSelectTick}) => {
  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName,
  };

  const {data} = useQuery<SensorTimelineQuery>(SENSOR_TIMELINE_QUERY, {
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

  const {
    sensorState: {ticks},
    nextTick,
  } = data.sensorOrError;

  return (
    <Group direction="column" spacing={12}>
      <div style={{position: 'relative'}}>
        {ticks.length ? (
          <TickTimelineGraph
            ticks={ticks}
            nextTick={nextTick}
            onHighlightRunIds={onHighlightRunIds}
            onSelectTick={onSelectTick}
          />
        ) : (
          <Box margin={{vertical: 8}} flex={{justifyContent: 'center'}}>
            No ticks recorded
          </Box>
        )}
      </div>
    </Group>
  );
};

const REFRESH_INTERVAL = 100;

const TickTimelineGraph: React.FC<{
  ticks: SensorTick[];
  nextTick: FutureTick | null;
  onHighlightRunIds: (runIds: string[]) => void;
  onSelectTick: (tick?: JobHistoryFragment_ticks) => void;
}> = ({ticks, nextTick, onHighlightRunIds, onSelectTick}) => {
  const [now, setNow] = React.useState<number>(Date.now());
  const [graphNow, setGraphNow] = React.useState<number>(Date.now());
  const [isPaused, setPaused] = React.useState<boolean>(false);
  React.useEffect(() => {
    const interval = setInterval(() => {
      !isPaused && setNow(Date.now());
    }, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  });

  React.useEffect(() => {
    if (!isPaused && (!nextTick || now < 1000 * nextTick.timestamp)) {
      setGraphNow(now);
    }
  }, [isPaused, nextTick, now]);

  const tickData = ticks.map((tick) => ({x: 1000 * tick.timestamp, y: 0}));
  if (nextTick) {
    tickData.push({x: 1000 * nextTick.timestamp, y: 0});
  }

  const isAtFutureTick = nextTick && 1000 * nextTick.timestamp <= now;
  const PULSE_DURATION = 2000;
  const nextTickRadius = isAtFutureTick
    ? 4 + Math.sin((2 * Math.PI * (now % PULSE_DURATION)) / PULSE_DURATION)
    : 3;
  const graphData: ChartComponentProps['data'] = {
    labels: ['ticks'],
    datasets: [
      {
        label: 'now',
        data: [
          {x: graphNow - 60000 * 10, y: 0},
          {x: graphNow, y: 0},
        ],
        borderColor: Colors.LIGHT_GRAY4,
        borderWidth: 1,
        pointBorderWidth: 2,
        pointBorderColor: isAtFutureTick ? Colors.GRAY5 : Colors.GRAY5,
        pointRadius: 1,
        pointHoverRadius: 1,
      },
      {
        label: 'ticks',
        data: tickData,
        borderColor: Colors.LIGHT_GRAY4,
        borderWidth: 0,
        backgroundColor: 'rgba(0,0,0,0)',
        pointBackgroundColor: 'rgba(0,0,0,0)',
        pointBorderWidth: 2,
        pointBorderColor: ticks.map((tick) => COLOR_MAP[tick.status]),
        pointRadius: [...Array(ticks.length).fill(3), nextTickRadius],
        pointHoverBorderWidth: 2,
        pointHoverRadius: 5,
        pointHoverBorderColor: ticks.map((tick) => COLOR_MAP[tick.status]),
      },
    ],
  };

  const options: ChartComponentProps['options'] = {
    animation: {
      duration: 0,
    },
    scales: {
      yAxes: [{scaleLabel: {display: false}, ticks: {display: false}, gridLines: {display: false}}],
      xAxes: [
        {
          type: 'time',
          scaleLabel: {
            display: false,
          },
          gridLines: {display: true},
          bounds: 'ticks',
          ticks: {
            min: graphNow - 60000 * 5, // 5 minutes ago
            max: graphNow + 60000, // 1 minute from now
          },
          time: {
            minUnit: 'minute',
          },
        },
      ],
    },
    legend: {
      display: false,
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

    onHover: (event, elements: any[]) => {
      if (event?.target instanceof HTMLElement) {
        event.target.style.cursor = elements.length ? 'pointer' : 'default';
      }
      if (elements.length && !isPaused) {
        setPaused(true);
        const [element] = elements.filter(
          (x) => x._datasetIndex === 1 && x._index !== undefined && x._index < ticks.length,
        );
        if (!element) {
          return;
        }
        const tick = ticks[element._index];
        onHighlightRunIds(tick.runIds || []);
      } else if (!elements.length && isPaused) {
        setPaused(false);
        onHighlightRunIds([]);
      }
    },

    tooltips: {
      displayColors: false,
      callbacks: {
        label: function (tooltipItem, _data) {
          if (!tooltipItem.datasetIndex) {
            // this is the current time
            return 'Current time';
          }
          if (tooltipItem.index === undefined) {
            return '';
          }
          if (tooltipItem.index === ticks.length) {
            // This is the future tick
            return '';
          }
          const tick = ticks[tooltipItem.index];
          if (tick.status === JobTickStatus.SKIPPED && tick.skipReason) {
            return tick.skipReason;
          }
          if (tick.status === JobTickStatus.SUCCESS && tick.runIds.length) {
            onHighlightRunIds(tick.runIds);
            return tick.runIds;
          }
          if (tick.status == JobTickStatus.FAILURE && tick.error?.message) {
            return tick.error.message;
          }
          return '';
        },
      },
    },
  };
  return <Line data={graphData} height={30} options={options} key="100%" />;
};

const SENSOR_TIMELINE_QUERY = gql`
  query SensorTimelineQuery($sensorSelector: SensorSelector!) {
    sensorOrError(sensorSelector: $sensorSelector) {
      __typename
      ... on Sensor {
        id
        nextTick {
          timestamp
        }
        sensorState {
          id
          ticks(limit: 20) {
            id
            status
            timestamp
            skipReason
            runIds
            error {
              ...PythonErrorFragment
            }
          }
        }
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
