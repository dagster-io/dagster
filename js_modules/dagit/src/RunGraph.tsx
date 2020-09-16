import {Colors} from '@blueprintjs/core';
import {ChartOptions} from 'chart.js';
import * as React from 'react';
import {Line} from 'react-chartjs-2';

import {RowContainer} from 'src/ListComponents';
import {colorHash} from 'src/Util';
import {RunGraphFragment} from 'src/types/RunGraphFragment';

type PointValue = number | null | undefined;
type Point = {x: PointValue; y: PointValue};

export const PIPELINE_LABEL = 'Total pipeline';

interface GraphProps {
  runs: RunGraphFragment[];
  getPipelineDataForRun: (run: RunGraphFragment) => PointValue;
  getStepDataForRun: (run: RunGraphFragment) => {[key: string]: PointValue[]};
  title?: string;
  yLabel?: string;
}

export class RunGraph extends React.Component<GraphProps> {
  chart = React.createRef<any>();
  getDefaultOptions = () => {
    const {title, yLabel} = this.props;
    const titleOptions = title ? {display: true, text: title} : undefined;
    const scales = yLabel
      ? {
          yAxes: [
            {
              scaleLabel: {display: true, labelString: yLabel},
            },
          ],
          xAxes: [
            {
              type: 'time',
              time: {
                parser: 'X',
                tooltipFormat: 'll',
              },
              scaleLabel: {display: true, labelString: 'Pipeline Start Time'},
            },
          ],
        }
      : undefined;
    const defaultOptions: ChartOptions = {
      title: titleOptions,
      scales,
      legend: {
        display: false,
        onClick: (_e: MouseEvent, _legendItem: any) => {},
      },
    };
    return defaultOptions;
  };

  buildDatasetData() {
    const {runs, getPipelineDataForRun, getStepDataForRun} = this.props;

    const pipelineData: Point[] = [];
    const stepData = {};

    runs.forEach((run) => {
      pipelineData.push({
        x: _getRunStartTime(run),
        y: getPipelineDataForRun(run),
      });

      const stepDataforRun = getStepDataForRun(run);
      Object.keys(stepDataforRun).forEach((stepKey) => {
        stepData[stepKey] = [
          ...(stepData[stepKey] || []),
          {
            x: _getRunStartTime(run),
            y: stepDataforRun[stepKey],
          },
        ];
      });
    });

    // stepData may have holes due to missing runs or missing steps.  For these to
    // render properly, fill in the holes with `undefined` values.
    Object.keys(stepData).forEach((stepKey) => {
      stepData[stepKey] = _fillPartitions(runs, stepData[stepKey]);
    });

    return {pipelineData, stepData};
  }

  render() {
    const {pipelineData, stepData} = this.buildDatasetData();
    const graphData = {
      // labels: Object.keys(runs),
      datasets: [
        {
          label: PIPELINE_LABEL,
          data: pipelineData,
          borderColor: Colors.GRAY2,
          backgroundColor: 'rgba(0,0,0,0)',
        },
        ...Object.keys(stepData).map((stepKey) => ({
          label: stepKey,
          data: stepData[stepKey],
          borderColor: colorHash(stepKey),
          backgroundColor: 'rgba(0,0,0,0)',
        })),
      ],
    };
    const options = this.getDefaultOptions();
    return (
      <RowContainer style={{margin: '20px 0'}}>
        <Line data={graphData} height={100} options={options} ref={this.chart} />
      </RowContainer>
    );
  }
}

const _getRunStartTime = (run: RunGraphFragment) => {
  if (run.stats.__typename === 'PipelineRunStatsSnapshot') {
    return run.stats.startTime ? run.stats.startTime * 1000 : null;
  }
  return undefined;
};

const _fillPartitions = (runs: RunGraphFragment[], points: Point[]) => {
  const pointData = {};
  points.forEach((point) => {
    if (point.x) {
      pointData[point.x] = point.y;
    }
  });

  return runs.map((run) => {
    const x = _getRunStartTime(run);
    const y = x ? pointData[x] : undefined;
    return {x, y};
  });
};
