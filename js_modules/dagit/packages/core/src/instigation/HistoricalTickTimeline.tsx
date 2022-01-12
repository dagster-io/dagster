import {Box, ButtonLink, ColorsWIP} from '@dagster-io/ui';
import {ActiveElement, Chart, TimeUnit} from 'chart.js';
import 'chartjs-adapter-date-fns';
import zoomPlugin from 'chartjs-plugin-zoom';
import moment from 'moment-timezone';
import * as React from 'react';
import {Line} from 'react-chartjs-2';

import {InstigationTickStatus} from '../types/globalTypes';

import {TickHistoryQuery_instigationStateOrError_InstigationState_ticks} from './types/TickHistoryQuery';

Chart.register(zoomPlugin);

type InstigationTick = TickHistoryQuery_instigationStateOrError_InstigationState_ticks;

const MIN_ZOOM_RANGE = 30 * 60 * 1000; // 30 minutes

const COLOR_MAP = {
  [InstigationTickStatus.SUCCESS]: ColorsWIP.Blue500,
  [InstigationTickStatus.FAILURE]: ColorsWIP.Red500,
  [InstigationTickStatus.STARTED]: ColorsWIP.Gray400,
  [InstigationTickStatus.SKIPPED]: ColorsWIP.Yellow500,
};

interface Bounds {
  min: number;
  max: number;
}

export const HistoricalTickTimeline: React.FC<{
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
