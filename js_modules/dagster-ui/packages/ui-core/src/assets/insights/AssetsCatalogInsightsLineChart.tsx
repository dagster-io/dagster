import {Box, Colors} from '@dagster-io/ui-components';
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

import styles from './AssetsCatalogLineChart.module.css';
import {useRGBColorsForTheme} from '../../app/useRGBColorsForTheme';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip);

const getDataset = (color: string, previousPeriodColor: string) => ({
  labels: ['Apr 7', '', '', '', '', '', '', 'Apr 11'],
  datasets: [
    {
      label: 'Materialization Count',
      data: [20, 26, 22, 21, 20, 32, 27, 34],
      borderColor: color,
      backgroundColor: 'transparent',
      pointRadius: 0,
      borderWidth: 2,
    },
    {
      label: 'Previous Period',
      data: [28, 28, 20, 25, 30, 32, 27, 28],
      borderColor: previousPeriodColor,
      backgroundColor: 'transparent',
      pointRadius: 0,
      borderWidth: 1,
    },
  ],
});

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

export const AssetsCatalogInsightsLineChart = React.memo(({color}: {color: string}) => {
  const rgbColors = useRGBColorsForTheme();
  const previousPeriodColor = rgbColors[Colors.backgroundDisabled()]!;

  return (
    <div className={styles.chartContainer}>
      <div className={styles.chartHeader}>Materialization count</div>
      <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
        <div className={styles.chartCount}>34</div>
        <div className={styles.chartChange}>↘ 13%</div>
      </Box>
      <div className={styles.chartWrapper}>
        <div className={styles.chartGraph}>
          <Line data={getDataset(color, previousPeriodColor)} options={options} />
        </div>
      </div>
    </div>
  );
});
