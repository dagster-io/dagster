import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Line, ChartComponentProps} from 'react-chartjs-2';

import {InstigationTickStatus} from '../types/globalTypes';

import {
  TickHistoryQuery_instigationStateOrError_InstigationState_ticks,
  TickHistoryQuery_instigationStateOrError_InstigationState_nextTick,
} from './types/TickHistoryQuery';

type FutureTick = TickHistoryQuery_instigationStateOrError_InstigationState_nextTick;
type InstigationTick = TickHistoryQuery_instigationStateOrError_InstigationState_ticks;

const COLOR_MAP = {
  [InstigationTickStatus.SUCCESS]: Colors.BLUE3,
  [InstigationTickStatus.FAILURE]: Colors.RED3,
  [InstigationTickStatus.STARTED]: Colors.GRAY3,
  [InstigationTickStatus.SKIPPED]: Colors.GOLD3,
};

const REFRESH_INTERVAL = 100;

export const LiveTickTimeline: React.FC<{
  ticks: InstigationTick[];
  nextTick: FutureTick | null;
  onHoverTick: (InstigationTick?: any) => void;
  onSelectTick: (InstigationTick?: any) => void;
}> = ({ticks, nextTick, onHoverTick, onSelectTick}) => {
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
        onHoverTick(tick);
      } else if (!elements.length && isPaused) {
        setPaused(false);
        onHoverTick(undefined);
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
          if (tick.status === InstigationTickStatus.SKIPPED && tick.skipReason) {
            return tick.skipReason;
          }
          if (tick.status === InstigationTickStatus.SUCCESS && tick.runIds.length) {
            return tick.runIds;
          }
          if (tick.status === InstigationTickStatus.SUCCESS && tick.originRunIds) {
            return tick.originRunIds;
          }
          if (tick.status === InstigationTickStatus.FAILURE && tick.error?.message) {
            return tick.error.message;
          }
          return '';
        },
      },
    },
  };
  return <Line data={graphData} height={30} options={options} key="100%" />;
};
