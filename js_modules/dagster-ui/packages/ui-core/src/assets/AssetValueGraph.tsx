import {Colors} from '@dagster-io/ui-components';
import {ActiveElement, ChartEvent} from 'chart.js';
import 'chartjs-adapter-date-fns';
import * as React from 'react';
import {Line} from 'react-chartjs-2';

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
  yAxisLabel?: string;
  data: AssetValueGraphData;
  xHover: string | number | null;
  onHoverX: (value: string | number | null) => void;
}) => {
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

  const options = {
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
        id: 'x',
        display: true,
        ticks: {
          color: tickColor,
        },
        ...(props.data.xAxis === 'time'
          ? {
              type: 'time',
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
        id: 'y',
        display: true,
        ticks: {
          color: tickColor,
        },
        title: {display: true, color: tickColor, text: props.yAxisLabel || 'Value'},
      },
    },
    plugins: {
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

  return <Line data={graphData} height={100} options={options as any} key={props.width} />;
};
