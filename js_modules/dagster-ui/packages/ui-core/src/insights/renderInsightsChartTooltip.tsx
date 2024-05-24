import {Colors} from '@dagster-io/ui-components';
import {Chart, TooltipModel} from 'chart.js';
import {ReactElement} from 'react';
import {Root, createRoot} from 'react-dom/client';

let target: HTMLDivElement | null = null;
let root: Root | null = null;

export type RenderTooltipFn = (config: {
  color: string;
  label: string;
  date: Date;
  formattedValue: string;
}) => ReactElement;

type TooltipContextWithCustomValues = {
  renderFn: RenderTooltipFn;
  chart: Chart;
  tooltip: TooltipModel<'bar' | 'line'>;
};

export const renderInsightsChartTooltip = (context: TooltipContextWithCustomValues) => {
  const {renderFn, chart, tooltip} = context;

  if (!target) {
    target = document.createElement('div');
    target.style.position = 'absolute';
    target.style.transition = 'all 100ms ease';
  }

  if (!root) {
    root = createRoot(target);
  }

  const canvasParent = chart.canvas.parentNode;
  if (!canvasParent) {
    return;
  }

  // If we render the chart on a new page, the global target node will be orphaned
  // and needs to be reattached to the newly rendered `canvas`.
  if (!canvasParent.contains(target)) {
    canvasParent.appendChild(target);
  }

  target.style.opacity = tooltip.opacity === 0 ? '0' : '1';
  target.style.pointerEvents = tooltip.opacity === 0 ? 'none' : 'auto';

  const dataPoints = tooltip.dataPoints;

  // It's possible to interact with the chart before any data appears, and the
  // tooltip plugin just plows right ahead with trying to render. Bail in this case
  // to avoid runtime errors.
  if (!dataPoints || !dataPoints[0]) {
    return;
  }

  const dataPoint = dataPoints[0];
  const {dataIndex, formattedValue, dataset} = dataPoint;

  // If this point is at the far left, push the tooltip to the right to prevent overflow.
  // Similarly, if it's at the far right, push it to the left. Otherwise, show it
  // directly above the point.
  if (dataIndex === 0) {
    target.style.transform = 'translate(2%, -120%)';
  } else if (dataIndex === dataset.data.length - 1) {
    target.style.transform = 'translate(-102%, -120%)';
  } else {
    target.style.transform = 'translate(-50%, -120%)';
  }

  const date = new Date(parseInt(dataPoint.label, 10));
  const color = (dataset.borderColor as string) || Colors.dataVizBlurpleAlt();
  const label = dataset.label || '';

  root.render(renderFn({color, label, date, formattedValue}));

  const {offsetLeft: positionX, offsetTop: positionY} = chart.canvas;
  target.style.left = positionX + tooltip.caretX + 'px';
  target.style.top = positionY + tooltip.caretY + 'px';
};
