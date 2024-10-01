import {Colors} from '@dagster-io/ui-components';
import {ActiveElement, ChartEvent, ChartOptions} from 'chart.js';
import 'chartjs-adapter-date-fns';
import * as React from 'react';
import {useContext} from 'react';
import {Line} from 'react-chartjs-2';

import {TimeContext} from '../app/time/TimeContext';
import {timestampToString} from '../app/time/timestampToString';
import {useRGBColorsForTheme} from '../app/useRGBColorsForTheme';

export interface AssetValueGraphData {
  minY: number;
  maxY: number;
  minXNumeric: number;
  maxXNumeric: number;
  xAxis: 'time' | 'partition';
  values: {
    x: number | string; // time or partition
    xNumeric: number; // time or partition index
    y: number;
  }[];
}

export const AssetValueGraph = (props: {
  label: string;
  width: string;
  height?: number;
  yAxisLabel?: string;
  data: AssetValueGraphData;
  xHover: string | number | null;
  onHoverX: (value: string | number | null) => void;
}) => {
  const {
    timezone: [userTimezone],
    hourCycle: [hourCycle],
  } = useContext(TimeContext);

  const locale = navigator.language;

  const rgbColors = useRGBColorsForTheme();
  // Note: To get partitions on the X axis, we pass the partition names in as the `labels`,
  // and pass the partition index as the x value. This prevents ChartJS from auto-coercing
  // ISO date partition names to dates and then re-formatting the labels away from 2020-01-01.
  //
  if (!props.data) {
    return <span />;
  }

  let labels: React.ReactText[] | undefined = undefined;
  let xHover = props.xHover;
  if (props.data.xAxis === 'partition') {
    labels = props.data.values.map((v) => v.x);
    xHover = xHover ? labels.indexOf(xHover) : null;
  }

  const borderColor = rgbColors[Colors.accentBlue()];
  const backgroundColor = rgbColors[Colors.backgroundBlue()];
  const pointHoverBorderColor = rgbColors[Colors.accentBlue()];
  const tickColor = rgbColors[Colors.textLighter()];

  const graphData = {
    labels,
    datasets: [
      {
        label: props.label,
        lineTension: 0,
        data: props.data.values.map((v) => ({x: v.xNumeric, y: v.y})),
        borderColor,
        backgroundColor,
        pointBorderWidth: 2,
        pointHoverBorderWidth: 2,
        pointHoverRadius: 13,
        pointHoverBorderColor,
      },
    ],
  };

  const options: ChartOptions<'line'> = {
    animation: {
      duration: 0,
    },
    elements: {
      point: {
        radius: ((context: any) =>
          context.dataset.data[context.dataIndex]?.x === xHover ? 13 : 2) as any,
      },
    },
    scales: {
      x: {
        display: true,
        ...(props.data.xAxis === 'time'
          ? {
              type: 'time',
              ticks: {
                color: tickColor,
                autoSkip: true,
                autoSkipPadding: 12,
                callback: (label, index, ticks) => {
                  const ms = ticks[index]?.value || 0;
                  return timestampToString({
                    timestamp: {ms},
                    locale,
                    timezone: userTimezone,
                    timeFormat: {},
                    hourCycle,
                  });
                },
              },
              title: {
                display: true,
                text: 'Timestamp',
                color: tickColor,
              },
            }
          : {
              type: 'category',
              title: {
                display: true,
                text: 'Partition',
                color: tickColor,
              },
            }),
      },
      y: {
        display: true,
        ticks: {
          color: tickColor,
        },
        title: {display: true, color: tickColor, text: props.yAxisLabel || 'Value'},
      },
    },
    plugins: {
      tooltip: {
        callbacks: {
          title: (points) => {
            return points.map(({parsed}) => {
              if (props.data.xAxis === 'time') {
                return timestampToString({
                  timestamp: {ms: parsed.x},
                  locale,
                  timezone: userTimezone,
                  timeFormat: {},
                  hourCycle,
                });
              }
              return `${parsed.x}`;
            });
          },
        },
      },
      legend: {
        display: false,
      },
    },
    onHover(_: ChartEvent, activeElements: ActiveElement[]) {
      if (activeElements.length === 0) {
        props.onHoverX(null);
        return;
      }
      const itemIdx = (activeElements[0] as any).index;
      if (itemIdx === 0) {
        // ChartJS errantly selects the first item when you're moving the mouse off the line
        props.onHoverX(null);
        return;
      }
      props.onHoverX(props.data.values[itemIdx]!.x);
    },
  };

  return (
    <Line
      data={graphData}
      height={props.height || 100}
      options={options as any}
      key={props.width}
    />
  );
};
