import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Line} from 'react-chartjs-2';

import {RowContainer} from 'src/ListComponents';
import {colorHash} from 'src/Util';
import {PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs} from 'src/partitions/types/PartitionLongitudinalQuery';

type Run = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs;
type PointValue = number | null | undefined;
type Point = {x: string; y: PointValue};

export const PIPELINE_LABEL = 'Total pipeline';
interface PartitionGraphProps {
  runsByPartitionName: {[name: string]: Run[]};
  getPipelineDataForRun: (run: Run) => PointValue;
  getStepDataForRun: (run: Run) => {[key: string]: PointValue[]};
  title?: string;
  yLabel?: string;
}
interface PartitionGraphState {
  hiddenPartitions: {[name: string]: boolean};
}

export class PartitionGraph extends React.Component<PartitionGraphProps, PartitionGraphState> {
  constructor(props: PartitionGraphProps) {
    super(props);
    this.state = {hiddenPartitions: {}};
  }

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
              scaleLabel: {display: true, labelString: 'Partition'},
            },
          ],
        }
      : undefined;
    return {
      title: titleOptions,
      scales,
      legend: {
        display: false,
        onClick: (_e: MouseEvent, _legendItem: any) => {},
      },
      onClick: this.onGraphClick,
    };
  };

  onGraphClick = (event: MouseEvent) => {
    const instance = this.chart?.current?.chartInstance;
    if (!instance) {
      return;
    }
    const xAxis = instance.scales['x-axis-0'];
    if (!xAxis) {
      return;
    }
    const {offsetX, offsetY} = event;

    const isChartClick =
      event.type === 'click' &&
      offsetX <= instance.chartArea.right &&
      offsetX >= instance.chartArea.left &&
      offsetY <= instance.chartArea.bottom &&
      offsetY >= instance.chartArea.top;

    if (!isChartClick || !event.shiftKey) {
      return;
    }

    // category scale returns index here for some reason
    const labelIndex = xAxis.getValueForPixel(offsetX);
    const partitionName = instance.data.labels[labelIndex];
    const {hiddenPartitions} = this.state;
    this.setState({
      hiddenPartitions: {
        ...hiddenPartitions,
        [partitionName]: !hiddenPartitions[partitionName],
      },
    });
  };

  selectRun(runs?: Run[]) {
    if (!runs || !runs.length) {
      return null;
    }

    // get most recent run
    const toSort = runs.slice();
    toSort.sort(_reverseSortRunCompare);
    return toSort[0];
  }

  buildDatasetData() {
    const {runsByPartitionName, getPipelineDataForRun, getStepDataForRun} = this.props;

    const pipelineData: Point[] = [];
    const stepData = {};

    const partitionNames = Object.keys(runsByPartitionName);
    partitionNames.forEach((partitionName) => {
      const run = this.selectRun(runsByPartitionName[partitionName]);
      const hidden = !!this.state.hiddenPartitions[partitionName];
      pipelineData.push({
        x: partitionName,
        y: run && !hidden ? getPipelineDataForRun(run) : undefined,
      });

      if (!run) {
        return;
      }

      const stepDataforRun = getStepDataForRun(run);
      Object.keys(stepDataforRun).forEach((stepKey) => {
        stepData[stepKey] = [
          ...(stepData[stepKey] || []),
          {x: partitionName, y: !hidden ? stepDataforRun[stepKey] : undefined},
        ];
      });
    });

    // stepData may have holes due to missing runs or missing steps.  For these to
    // render properly, fill in the holes with `undefined` values.
    Object.keys(stepData).forEach((stepKey) => {
      stepData[stepKey] = _fillPartitions(partitionNames, stepData[stepKey]);
    });

    return {pipelineData, stepData};
  }

  render() {
    const {runsByPartitionName} = this.props;
    const {pipelineData, stepData} = this.buildDatasetData();
    const graphData = {
      labels: Object.keys(runsByPartitionName),
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

const _fillPartitions = (partitionNames: string[], points: Point[]) => {
  const pointData = {};
  points.forEach((point) => {
    pointData[point.x] = point.y;
  });

  return partitionNames.map((partitionName) => ({
    x: partitionName,
    y: pointData[partitionName],
  }));
};

const _reverseSortRunCompare = (a: Run, b: Run) => {
  if (!a.stats || a.stats.__typename !== 'PipelineRunStatsSnapshot' || !a.stats.startTime) {
    return 1;
  }
  if (!b.stats || b.stats.__typename !== 'PipelineRunStatsSnapshot' || !b.stats.startTime) {
    return -1;
  }
  return b.stats.startTime - a.stats.startTime;
};
