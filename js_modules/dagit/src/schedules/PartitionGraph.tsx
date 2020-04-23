import * as React from "react";

import {
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs
} from "./types/PartitionLongitudinalQuery";
import { RowContainer } from "../ListComponents";

import { Line } from "react-chartjs-2";
import { colorHash } from "../Util";
import { Colors } from "@blueprintjs/core";

type Partition = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results;
type Run = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs;
type PointValue = number | null | undefined;
type Point = { x: string; y: PointValue };

export const PIPELINE_LABEL = "Total pipeline";
interface PartitionGraphProps {
  partitions: Partition[];
  getPipelineDataForRun: (run: Run) => PointValue;
  getStepDataForRun: (run: Run) => { [key: string]: PointValue[] };
  title?: string;
  yLabel?: string;
}

export class PartitionGraph extends React.Component<PartitionGraphProps> {
  chart = React.createRef<any>();

  getDefaultOptions = () => {
    const { title, yLabel } = this.props;
    const titleOptions = title ? { display: true, text: title } : undefined;
    const scales = yLabel
      ? {
          yAxes: [{ scaleLabel: { display: true, labelString: yLabel } }],
          xAxes: [{ scaleLabel: { display: true, labelString: "Partition" } }]
        }
      : undefined;
    return {
      title: titleOptions,
      scales,
      legend: {
        display: false,
        onClick: (_e: MouseEvent, _legendItem: any) => {}
      }
    };
  };

  selectRun(runs?: Run[]) {
    if (!runs || !runs.length) {
      return null;
    }

    // select the most recent run
    return runs[runs.length - 1];
  }

  buildDatasetData() {
    const { partitions, getPipelineDataForRun, getStepDataForRun } = this.props;

    const pipelineData: Point[] = [];
    const stepData = {};

    partitions.forEach(partition => {
      const run = this.selectRun(partition.runs);

      pipelineData.push({
        x: partition.name,
        y: run ? getPipelineDataForRun(run) : undefined
      });

      if (!run) {
        return;
      }

      const stepDataforRun = getStepDataForRun(run);
      Object.keys(stepDataforRun).forEach(stepKey => {
        stepData[stepKey] = [
          ...(stepData[stepKey] || []),
          { x: partition.name, y: stepDataforRun[stepKey] }
        ];
      });
    });

    // stepData may have holes due to missing runs or missing steps.  For these to
    // render properly, fill in the holes with `undefined` values.
    Object.keys(stepData).forEach(stepKey => {
      stepData[stepKey] = fillPartitions(partitions, stepData[stepKey]);
    });

    return { pipelineData, stepData };
  }

  render() {
    const { partitions } = this.props;
    const { pipelineData, stepData } = this.buildDatasetData();
    const graphData = {
      labels: partitions.map(partition => partition.name),
      datasets: [
        {
          label: PIPELINE_LABEL,
          data: pipelineData,
          borderColor: Colors.GRAY2,
          backgroundColor: "rgba(0,0,0,0)"
        },
        ...Object.keys(stepData).map(stepKey => ({
          label: stepKey,
          data: stepData[stepKey],
          borderColor: colorHash(stepKey),
          backgroundColor: "rgba(0,0,0,0)"
        }))
      ]
    };
    const options = this.getDefaultOptions();
    return (
      <RowContainer style={{ margin: "20px 0" }}>
        <Line
          data={graphData}
          height={100}
          options={options}
          ref={this.chart}
        />
      </RowContainer>
    );
  }
}

const fillPartitions = (partitions: Partition[], points: Point[]) => {
  const pointData = {};
  points.forEach(point => {
    pointData[point.x] = point.y;
  });

  return partitions.map(partition => ({
    x: partition.name,
    y: pointData[partition.name]
  }));
};
