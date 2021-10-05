import * as React from 'react';
import {Line} from 'react-chartjs-2';

import {useFeatureFlags} from '../app/Flags';
import {colorHash} from '../app/Util';
import {ColorsWIP} from '../ui/Colors';
import {RowContainer} from '../ui/ListComponents';

import {PartitionGraphFragment} from './types/PartitionGraphFragment';

type PointValue = number | null | undefined;
type Point = {x: string; y: PointValue};

interface PartitionGraphProps {
  runsByPartitionName: {[name: string]: PartitionGraphFragment[]};
  getPipelineDataForRun: (run: PartitionGraphFragment) => PointValue;
  getStepDataForRun: (run: PartitionGraphFragment) => {[key: string]: PointValue[]};
  title?: string;
  yLabel?: string;
}

export const PartitionGraph = React.forwardRef((props: PartitionGraphProps, ref) => {
  const {runsByPartitionName, getPipelineDataForRun, getStepDataForRun, title, yLabel} = props;
  const {flagPipelineModeTuples} = useFeatureFlags();
  const [hiddenPartitions, setHiddenPartitions] = React.useState<{[name: string]: boolean}>(
    () => ({}),
  );
  const chart = React.useRef<any>(null);

  React.useImperativeHandle(ref, () => ({
    getChartInstance: () => chart.current?.chartInstance,
  }));

  const onGraphClick = React.useCallback((event: MouseEvent) => {
    const instance = chart.current?.chartInstance;
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
            title: {display: true, text: 'Partition'},
          },
        }
      : undefined;
    return {
      title: titleOptions,
      scales,
      plugins: {
        legend: {
          display: false,
          onClick: (_e: MouseEvent, _legendItem: any) => {},
        },
      },
      onClick: onGraphClick,
    };
  }, [onGraphClick, title, yLabel]);

  const selectRun = (runs?: PartitionGraphFragment[]) => {
    if (!runs || !runs.length) {
      return null;
    }

    // get most recent run
    const toSort = runs.slice();
    toSort.sort(_reverseSortRunCompare);
    return toSort[0];
  };

  const buildDatasetData = () => {
    const pipelineData: Point[] = [];
    const stepData = {};

    const partitionNames = Object.keys(runsByPartitionName);
    partitionNames.forEach((partitionName) => {
      const run = selectRun(runsByPartitionName[partitionName]);
      const hidden = !!hiddenPartitions[partitionName];
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
  };

  const {pipelineData, stepData} = buildDatasetData();
  const graphData = {
    labels: Object.keys(runsByPartitionName),
    datasets: [
      {
        label: flagPipelineModeTuples ? 'Total job' : 'Total pipeline',
        data: pipelineData,
        borderColor: ColorsWIP.Gray500,
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

  return (
    <RowContainer style={{margin: '20px 0'}}>
      <Line type="line" data={graphData} height={100} options={defaultOptions} ref={chart} />
    </RowContainer>
  );
});

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

const _reverseSortRunCompare = (a: PartitionGraphFragment, b: PartitionGraphFragment) => {
  if (!a.stats || a.stats.__typename !== 'PipelineRunStatsSnapshot' || !a.stats.startTime) {
    return 1;
  }
  if (!b.stats || b.stats.__typename !== 'PipelineRunStatsSnapshot' || !b.stats.startTime) {
    return -1;
  }
  return b.stats.startTime - a.stats.startTime;
};
