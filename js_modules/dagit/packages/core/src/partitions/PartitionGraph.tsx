import {Colors} from '@dagster-io/ui';
import * as React from 'react';
import {Line} from 'react-chartjs-2';
import styled from 'styled-components/macro';

import {colorHash} from '../app/Util';

type PointValue = number | null | undefined;
type Point = {x: string; y: PointValue};

interface PartitionGraphProps {
  partitionNames: string[];
  jobDataByPartition?: {[partitionName: string]: PointValue};
  stepDataByPartition?: {[partitionName: string]: {[key: string]: PointValue[]}};
  title?: string;
  yLabel?: string;
  isJob: boolean;
  hiddenStepKeys?: string[];
}

export const PartitionGraph = ({
  partitionNames,
  jobDataByPartition,
  stepDataByPartition,
  title,
  yLabel,
  isJob,
  hiddenStepKeys,
}: PartitionGraphProps) => {
  const [hiddenPartitions, setHiddenPartitions] = React.useState<{[name: string]: boolean}>(
    () => ({}),
  );
  const chart = React.useRef<any>(null);

  const onGraphClick = React.useCallback((event: MouseEvent) => {
    const instance = chart.current;
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
    setHiddenPartitions((current) => ({
      ...current,
      [partitionName]: !current[partitionName],
    }));
  }, []);

  const defaultOptions = React.useMemo(() => {
    const titleOptions = title ? {display: true, text: title} : undefined;
    const scales = yLabel
      ? {
          y: {
            id: 'y',
            title: {display: true, text: yLabel},
          },
          x: {
            id: 'x',
            title: {display: true, text: title},
          },
        }
      : undefined;

    return {
      title: titleOptions,
      animation: false,
      scales,
      plugins: {
        legend: {
          display: false,
          onClick: (_e: MouseEvent, _legendItem: any) => {},
        },
      },
      onClick: onGraphClick,
      maintainAspectRatio: false,
    };
  }, [onGraphClick, title, yLabel]);

  const buildDatasetData = () => {
    const jobData: Point[] = [];
    const stepData = {};

    partitionNames.forEach((partitionName) => {
      const hidden = !!hiddenPartitions[partitionName];
      if (jobDataByPartition) {
        jobData.push({
          x: partitionName,
          y: !hidden ? jobDataByPartition[partitionName] : undefined,
        });
      }

      if (stepDataByPartition) {
        const stepDataByKey = stepDataByPartition[partitionName];
        Object.keys(stepDataByKey || {}).forEach((stepKey) => {
          if (hiddenStepKeys?.includes(stepKey) || !stepDataByKey[stepKey]) {
            return;
          }
          stepData[stepKey] = [
            ...(stepData[stepKey] || []),
            {
              x: partitionName,
              y: !hidden ? stepDataByKey[stepKey] : undefined,
            },
          ];
        });
      }
    });

    // stepData may have holes due to missing runs or missing steps.  For these to
    // render properly, fill in the holes with `undefined` values.
    Object.keys(stepData).forEach((stepKey) => {
      stepData[stepKey] = _fillPartitions(partitionNames, stepData[stepKey]);
    });

    return {jobData, stepData};
  };

  const {jobData, stepData} = buildDatasetData();
  const allLabel = isJob ? 'Total job' : 'Total pipeline';
  const graphData = {
    labels: partitionNames,
    datasets: [
      ...(!jobDataByPartition || (hiddenStepKeys && hiddenStepKeys.includes(allLabel))
        ? []
        : [
            {
              label: allLabel,
              data: jobData,
              borderColor: Colors.Gray500,
              backgroundColor: 'rgba(0,0,0,0)',
            },
          ]),
      ...Object.keys(stepData).map((stepKey) => ({
        label: stepKey,
        data: stepData[stepKey],
        borderColor: colorHash(stepKey),
        backgroundColor: 'rgba(0,0,0,0)',
      })),
    ],
  };

  // Passing graphData as a closure prevents ChartJS from trying to isEqual, which is fairly
  // unlikely to save a render and is time consuming given the size of the data structure.
  // We have a useMemo around the entire <PartitionGraphSet /> and there aren't many extra renders.
  return (
    <PartitionGraphContainer>
      <Line type="line" data={() => graphData} height={300} options={defaultOptions} ref={chart} />
    </PartitionGraphContainer>
  );
};

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

const PartitionGraphContainer = styled.div`
  display: flex;
  color: ${Colors.Gray700};
  padding: 24px 12px;
  text-decoration: none;
`;
