import {Colors} from '@blueprintjs/core';
import {ActiveElement} from 'chart.js';
import * as React from 'react';
import {Line} from 'react-chartjs-2';

import {Group} from '../ui/Group';
import {Subheading} from '../ui/Text';

import {AssetNumericHistoricalData} from './types';

import 'chartjs-adapter-date-fns';

export const AssetValueGraph: React.FC<{
  label: string;
  width: string;
  data: AssetNumericHistoricalData[0];
  xHover: string | number | null;
  onHoverX: (value: string | number | null) => void;
}> = (props) => {
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

  const graphData = {
    labels: labels,
    datasets: [
      {
        label: props.label,
        lineTension: 0,
        data: props.data.values.map((v) => ({x: v.xNumeric, y: v.y})),
        borderColor: Colors.BLUE3,
        backgroundColor: 'rgba(0,0,0,0)',
        pointBorderWidth: 2,
        pointHoverBorderWidth: 2,
        pointHoverRadius: 13,
        pointHoverBorderColor: Colors.BLUE3,
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
          context.dataset.data[context.dataIndex].x === xHover ? 13 : 2) as any,
      },
    },
    scales: {
      x: {
        id: 'x',
        display: true,
        ...(props.data.xAxis === 'time'
          ? {
              type: 'time',
              title: {
                display: true,
                text: 'Timestamp',
              },
            }
          : {
              type: 'category',
              title: {
                display: true,
                text: 'Partition',
              },
            }),
      },
      y: {id: 'y', display: true, title: {display: true, text: 'Value'}},
    },
    plugins: {
      legend: {
        display: false,
      },
    },
    onHover(_: MouseEvent, activeElements: ActiveElement[]) {
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
      props.onHoverX(props.data.values[itemIdx].x);
    },
  };

  return (
    <div style={{marginBottom: 30, width: props.width}}>
      <Group direction="column" spacing={12}>
        <Subheading>{props.label}</Subheading>
        <Line type="line" data={graphData} height={100} options={options} key={props.width} />
      </Group>
    </div>
  );
};
