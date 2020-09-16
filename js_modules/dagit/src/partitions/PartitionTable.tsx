import * as React from 'react';
import {Line} from 'react-chartjs-2';
import {createGlobalStyle} from 'styled-components/macro';

import {RowContainer} from '../ListComponents';
import {RUN_STATUS_COLORS, RUN_STATUS_HOVER_COLORS} from '../runs/RunStatusDots';
import {openRunInBrowser} from '../runs/RunUtils';

import {PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs} from './types/PartitionLongitudinalQuery';

type Run = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs;
interface Point {
  x: string;
  y: number;
  runId: string;
  pipelineName: string;
  status: string;
}

export const PartitionTable: React.FunctionComponent<{
  title: string;
  runsByPartitionName: {[name: string]: Run[]};
}> = ({title, runsByPartitionName}) => {
  React.useEffect(() => {
    return destroyCustomTooltip;
  });
  const chart = React.useRef<any>(undefined);
  let max = 1;
  const runs: {[status: string]: Point[]} = {};
  Object.keys(runsByPartitionName).forEach((partitionName) => {
    const partitionRuns = runsByPartitionName[partitionName];
    max = Math.max(max, partitionRuns.length);
    partitionRuns
      .slice()
      .reverse()
      .forEach((run, i) => {
        const point: Point = {
          x: partitionName,
          y: i,
          runId: run.runId,
          pipelineName: run.pipelineName,
          status: run.status,
        };
        runs[run.status] = [...(runs[run.status] || []), point];
      });
  });
  max = 10 * (Math.floor(max / 10) + 1);

  const datasets = Object.keys(runs).map((status: string) => ({
    label: status,
    data: runs[status],
    showLine: false,
    pointStyle: 'rect',
    borderWidth: 1,
    pointBackgroundColor: RUN_STATUS_COLORS[status],
    pointHoverBackgroundColor: RUN_STATUS_HOVER_COLORS[status],
    radius: 8,
    pointHoverRadius: 8,
  }));
  const graphData = {
    labels: Object.keys(runsByPartitionName),
    datasets,
  };

  const onPointClick = (events: any[]) => {
    const [element] = events.slice().reverse();
    if (!element) {
      return;
    }
    const point = datasets[element._datasetIndex].data[element._index];
    if (point && point.runId) {
      openRunInBrowser(point, {openInNewWindow: true});
    }
  };

  const options = {
    title: {display: true, text: title},
    scales: {
      yAxes: [
        {
          scaleLabel: {display: true, labelString: 'Runs'},
          gridLines: {display: false},
          ticks: {
            display: false,
            suggestedMin: 0,
            suggestedMax: max,
          },
          position: 'left',
          afterFit: (scale: any) => {
            scale.width = 60;
          },
        },
        {
          scaleLabel: {display: true, labelString: ''},
          gridLines: {display: false},
          ticks: {
            display: false,
          },
          position: 'right',
          afterFit: (scale: any) => {
            scale.width = 60;
          },
        },
      ],
      xAxes: [
        {
          scaleLabel: {display: true, labelString: 'Partitions'},
          gridLines: {display: false},
          ticks: {padding: 10},
        },
      ],
    },
    legend: {
      display: false,
    },
    tooltips: {
      mode: 'point',
      position: 'nearest',
      enabled: false,
      custom: buildCustomTooltip(chart, datasets),
    },
    onHover: (e: any) => {
      const instance = chart?.current?.chartInstance;
      if (!instance) {
        return;
      }
      const [element] = instance.getElementAtEvent(e);

      if (element) {
        e.target.style.cursor = 'pointer';
      } else {
        e.target.style.cursor = 'auto';
      }
    },
  };

  return (
    <RowContainer style={{margin: '20px 0'}}>
      <Line
        data={graphData}
        height={max * 8}
        options={options}
        onElementsClick={onPointClick}
        ref={chart}
      />
      <TooltipStyles />
    </RowContainer>
  );
};

const buildCustomTooltip = (chart: any, datasets: any[]) => {
  // TODO: (prha) rewrite this to use a pre-constructed React component

  return (tooltipModel: any) => {
    let tooltipEl: HTMLElement | null = document.getElementById('partition-table-tooltip');

    // Create element
    if (!tooltipEl) {
      tooltipEl = document.createElement('div');
      tooltipEl.id = 'partition-table-tooltip';
      tooltipEl.innerHTML = '';
      document.body.appendChild(tooltipEl);
    }

    // Hide by default
    if (tooltipModel.opacity === 0) {
      tooltipEl.style.opacity = '0';
      return;
    }

    // Fetch the original data point
    const [pointRef] = tooltipModel.dataPoints || [];
    if (!pointRef) {
      return;
    }
    const point = datasets[pointRef.datasetIndex].data[pointRef.index];
    if (!point) {
      return;
    }

    // Set Text
    tooltipEl.innerHTML = [
      '<div class="carat"></div>',
      '<div class="contentContainer">',
      '<span class="label">Run id:</span> ',
      point.runId,
      '</div>',
    ].join('');

    // Position and show
    const position = chart?.current?.chartInstance?.canvas?.getBoundingClientRect();
    tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 20 + 'px';
    tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY - 18 + 'px';
    tooltipEl.style.opacity = '1';
  };
};

const destroyCustomTooltip = () => {
  const element: HTMLElement | null = document.getElementById('partition-table-tooltip');
  if (element) {
    element.parentNode?.removeChild(element);
  }
};

const TooltipStyles = createGlobalStyle`
  #partition-table-tooltip {
    position: absolute;

    .carat {
      width: 0;
      height: 0;
      border-top: 8px solid transparent;
      border-bottom: 8px solid transparent;
      border-right: 8px solid #000000;
      position: absolute;
      left: -6px;
      top: 11px;
    }

    .contentContainer {
      border: 1px solid #000000;
      border-radius: 5px;
      background-color: #000000;
      color: #ffffff;
      font-size: 12px;
      padding: 10px;

      .label {
        font-weight: 600;
      }
    }
  }
`;
