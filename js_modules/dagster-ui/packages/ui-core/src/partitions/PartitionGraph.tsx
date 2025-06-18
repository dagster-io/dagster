import {Box, Button, Colors, FontFamily, NonIdealState} from '@dagster-io/ui-components';
import {CategoryScale, ChartEvent, Chart as ChartJS, LinearScale} from 'chart.js';
import React, {useCallback, useMemo, useRef, useState} from 'react';
import {Line} from 'react-chartjs-2';
import styled from 'styled-components';

import {colorHash} from '../app/Util';
import {useRGBColorsForTheme} from '../app/useRGBColorsForTheme';
import {numberFormatter} from '../ui/formatters';

ChartJS.register(LinearScale, CategoryScale);

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

export const PartitionGraph = React.memo(
  ({
    partitionNames,
    jobDataByPartition,
    stepDataByPartition,
    title,
    yLabel,
    isJob,
    hiddenStepKeys,
  }: PartitionGraphProps) => {
    const [hiddenPartitions, setHiddenPartitions] = useState<{[name: string]: boolean}>(() => ({}));
    const chart = useRef<any>(null);

    const rgbColors = useRGBColorsForTheme();

    const [_showLargeGraphMessage, setShowLargeGraphMessage] = useState(
      partitionNames.length > 1000,
    );
    const showLargeGraphMessage = _showLargeGraphMessage && partitionNames.length > 1000;

    const onGraphClick = useCallback((event: ChartEvent) => {
      const instance = chart.current;
      if (!instance) {
        return;
      }
      const xAxis = instance.scales['x-axis-0'];
      if (!xAxis) {
        return;
      }

      const nativeEvent = event.native;
      if (!(nativeEvent instanceof MouseEvent)) {
        return;
      }

      const {offsetX, offsetY} = nativeEvent;

      const isChartClick =
        nativeEvent.type === 'click' &&
        offsetX <= instance.chartArea.right &&
        offsetX >= instance.chartArea.left &&
        offsetY <= instance.chartArea.bottom &&
        offsetY >= instance.chartArea.top;

      if (!isChartClick || !nativeEvent.shiftKey) {
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

    const defaultOptions = useMemo(() => {
      if (showLargeGraphMessage) {
        return null;
      }
      const titleOptions = title ? {display: true, text: title} : undefined;
      const scales = yLabel
        ? {
            y: {
              id: 'y',
              title: {display: true, text: yLabel, color: rgbColors[Colors.textLighter()]},
              grid: {
                color: rgbColors[Colors.keylineDefault()],
              },
              ticks: {
                color: rgbColors[Colors.textLighter()],
                font: {
                  size: 12,
                  family: FontFamily.monospace,
                },
              },
            },
            x: {
              id: 'x',
              title: {display: true, text: title, color: rgbColors[Colors.textLighter()]},
              grid: {
                color: rgbColors[Colors.keylineDefault()],
              },
              ticks: {
                color: rgbColors[Colors.textLighter()],
                font: {
                  size: 12,
                  family: FontFamily.monospace,
                },
              },
            },
          }
        : undefined;

      return {
        title: titleOptions,
        animation: false as const,
        scales,
        plugins: {
          legend: {
            display: false,
            onClick: (_e: ChartEvent, _legendItem: any) => {},
          },
        },
        onClick: onGraphClick,
        maintainAspectRatio: false,
      };
    }, [onGraphClick, rgbColors, showLargeGraphMessage, title, yLabel]);

    const {jobData, stepData} = useMemo(() => {
      if (showLargeGraphMessage) {
        return {jobData: [], stepData: {}};
      }
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
          Object.entries(stepDataByKey || {}).forEach(([stepKey, step]) => {
            if (hiddenStepKeys?.includes(stepKey) || !step) {
              return;
            }
            (stepData as any)[stepKey] = [
              ...((stepData as any)[stepKey] || []),
              {
                x: partitionName,
                y: !hidden ? step : undefined,
              },
            ];
          });
        }
      });

      // stepData may have holes due to missing runs or missing steps.  For these to
      // render properly, fill in the holes with `undefined` values.
      Object.keys(stepData).forEach((stepKey) => {
        (stepData as any)[stepKey] = _fillPartitions(partitionNames, (stepData as any)[stepKey]);
      });

      return {jobData, stepData};
    }, [
      hiddenPartitions,
      hiddenStepKeys,
      jobDataByPartition,
      partitionNames,
      showLargeGraphMessage,
      stepDataByPartition,
    ]);

    const allLabel = isJob ? 'Total job' : 'Total pipeline';
    const graphData = useMemo(
      () =>
        showLargeGraphMessage
          ? null
          : {
              labels: partitionNames,
              datasets: [
                ...(!jobDataByPartition || (hiddenStepKeys && hiddenStepKeys.includes(allLabel))
                  ? []
                  : [
                      {
                        label: allLabel,
                        data: jobData,
                        borderColor: rgbColors[Colors.borderDefault()],
                        backgroundColor: rgbColors[Colors.dataVizBlurple()],
                      },
                    ]),
                ...Object.keys(stepData).map((stepKey) => ({
                  label: stepKey,
                  data: stepData[stepKey as keyof typeof stepData],
                  borderColor: colorHash(stepKey),
                  backgroundColor: rgbColors[Colors.dataVizBlurple()],
                })),
              ],
            },
      [
        allLabel,
        hiddenStepKeys,
        jobData,
        jobDataByPartition,
        partitionNames,
        rgbColors,
        showLargeGraphMessage,
        stepData,
      ],
    );

    if (graphData && defaultOptions) {
      // Passing graphData as a closure prevents ChartJS from trying to isEqual, which is fairly
      // unlikely to save a render and is time consuming given the size of the data structure.
      // We have a useMemo around the entire <PartitionGraphSet /> and there aren't many extra renders.
      return (
        <PartitionGraphContainer>
          <Line data={graphData} height={300} options={defaultOptions} ref={chart} />
        </PartitionGraphContainer>
      );
    }
    return (
      <NonIdealState
        icon="warning"
        title="Large number of data points"
        description={
          <Box flex={{direction: 'column', gap: 8}}>
            There are {numberFormatter.format(partitionNames.length)} datapoints in this graph. This
            might crash the browser.
            <div>
              <Button
                intent="primary"
                onClick={() => {
                  setShowLargeGraphMessage(false);
                }}
              >
                Show anyway
              </Button>
            </div>
          </Box>
        }
      />
    );
  },
);

const _fillPartitions = (partitionNames: string[], points: Point[]) => {
  const pointData = {};
  points.forEach((point) => {
    (pointData as any)[point.x] = point.y;
  });

  return partitionNames.map((partitionName) => ({
    x: partitionName,
    y: (pointData as any)[partitionName],
  }));
};

const PartitionGraphContainer = styled.div`
  display: flex;
  color: ${Colors.textLight()};
  padding: 24px 12px;
  text-decoration: none;
`;
