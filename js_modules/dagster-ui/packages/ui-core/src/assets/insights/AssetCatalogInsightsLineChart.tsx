import {Box} from '@dagster-io/ui-components';
import {
  CategoryScale,
  Chart as ChartJS,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js';
import React from 'react';
import {Line} from 'react-chartjs-2';

import styles from './AssetCatalogLineChart.module.css';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip);

const L_FORMAT = new Intl.DateTimeFormat(navigator.language, {
  month: 'short',
  day: 'numeric',
  timeZone: 'UTC',
});

export type LineChartMetrics = {
  title: string;
  color: string;
  timestamps: number[];
  pctChange: number | null;
  currentPeriod: {
    label: string;
    data: (number | null)[];
    aggregateValue: number | null;
    color: string;
  };
  prevPeriod: {
    label: string;
    data: (number | null)[];
    color: string;
  };
};

const getDataset = (metrics: LineChartMetrics) => {
  const start = metrics.timestamps.length
    ? L_FORMAT.format(new Date(metrics.timestamps[0]! * 1000))
    : '';
  const end = metrics.timestamps.length
    ? L_FORMAT.format(new Date(metrics.timestamps[metrics.timestamps.length - 1]! * 1000))
    : '';

  const labels = metrics.timestamps.length
    ? [start, ...Array(metrics.timestamps.length - 2).fill(''), end]
    : [];

  return {
    labels,
    datasets: [
      {
        label: metrics.currentPeriod.label,
        data: metrics.currentPeriod.data,
        borderColor: metrics.currentPeriod.color,
        backgroundColor: 'transparent',
        pointRadius: 0,
        borderWidth: 2,
      },
      {
        label: metrics.prevPeriod.label,
        data: metrics.prevPeriod.data,
        borderColor: metrics.prevPeriod.color,
        backgroundColor: 'transparent',
        pointRadius: 0,
        borderWidth: 1,
      },
    ],
  };
};

const options = {
  plugins: {legend: {display: false}, tooltip: {enabled: false}},
  scales: {
    x: {
      grid: {display: false},
      ticks: {color: '#9ca3af'},
    },
    y: {
      display: false,
    },
  },
  responsive: true,
  maintainAspectRatio: false,
};

export const AssetCatalogInsightsLineChart = React.memo(
  ({metrics}: {metrics: LineChartMetrics}) => {
    return (
      <div className={styles.chartContainer}>
        <div className={styles.chartHeader}>{metrics.title}</div>
        <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
          <div className={styles.chartCount}>{metrics.currentPeriod.aggregateValue}</div>
          {metrics.pctChange && <div className={styles.chartChange}>{metrics.pctChange}</div>}
        </Box>
        <div className={styles.chartWrapper}>
          <div className={styles.chartGraph}>
            <Line data={getDataset(metrics)} options={options} />
          </div>
        </div>
      </div>
    );
  },
);
