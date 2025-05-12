import {BodySmall, Box, Colors, Mono, Spinner, Subheading} from '@dagster-io/ui-components';
import {
  CategoryScale,
  ChartData,
  Chart as ChartJS,
  ChartOptions,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js';
import React, {useCallback, useMemo} from 'react';
import {Line} from 'react-chartjs-2';

import styles from './AssetCatalogLineChart.module.css';
import {Context, useRenderChartTooltip} from './renderChartTooltip';
import {useRGBColorsForTheme} from '../../app/useRGBColorsForTheme';
import {TooltipCard} from '../../insights/InsightsChartShared';
import {numberFormatter, percentFormatter} from '../../ui/formatters';
import {useFormatDateTime} from '../../ui/useFormatDateTime';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip);

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

const getDataset = (
  metrics: LineChartMetrics,
  formatDatetime: (date: Date, options: Intl.DateTimeFormatOptions) => string,
): ChartData<'line', (number | null)[], string> => {
  const start = metrics.timestamps.length
    ? formatDatetime(new Date(metrics.timestamps[0]! * 1000), {
        month: 'short',
        day: 'numeric',
      })
    : '';
  const end = metrics.timestamps.length
    ? formatDatetime(new Date(metrics.timestamps[metrics.timestamps.length - 1]! * 1000), {
        month: 'short',
        day: 'numeric',
      })
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

export const AssetCatalogInsightsLineChart = React.memo(
  ({
    metrics,
    loading,
    unitType,
  }: {
    metrics: LineChartMetrics;
    loading: boolean;
    unitType: string;
  }) => {
    const formatDatetime = useFormatDateTime();
    const rgbColors = useRGBColorsForTheme();

    const renderTooltipFn = useRenderChartTooltip(
      useCallback(
        ({context}: {context: Context}) => {
          const {tooltip} = context;
          const currentPeriodDataPoint = tooltip.dataPoints[0]!;
          const prevPeriodDataPoint = tooltip.dataPoints[1]!;
          const date = formatDatetime(
            new Date(metrics.timestamps[currentPeriodDataPoint.dataIndex]! * 1000),
            {
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: 'numeric',
            },
          );
          return (
            <TooltipCard>
              <Box flex={{direction: 'column', gap: 4}} padding={{vertical: 8, horizontal: 12}}>
                <Box border="bottom" padding={{bottom: 4}} margin={{bottom: 4}}>
                  <Subheading>{date}</Subheading>
                </Box>
                <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                  <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                    <div
                      style={{
                        width: 12,
                        height: 12,
                        backgroundColor: metrics.currentPeriod.color,
                        border: `1px solid ${rgbColors[Colors.textDefault()]}`,
                      }}
                    />
                    <div>Current Period:</div>
                  </Box>
                  <Mono>{currentPeriodDataPoint?.formattedValue ?? 0}</Mono>
                  <BodySmall color={Colors.textLight()}>{unitType}</BodySmall>
                </Box>
                <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                  <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                    <div
                      style={{
                        width: 12,
                        height: 12,
                        backgroundColor: metrics.prevPeriod.color,
                        border: `1px solid ${rgbColors[Colors.textDefault()]}`,
                      }}
                    />
                    <div>Previous Period:</div>
                  </Box>
                  <Mono>{prevPeriodDataPoint?.formattedValue ?? 0}</Mono>
                  <BodySmall color={Colors.textLight()}>{unitType}</BodySmall>
                </Box>
              </Box>
            </TooltipCard>
          );
        },
        [formatDatetime, metrics, rgbColors, unitType],
      ),
      useMemo(() => ({side: 'top', sideOffset: 50, align: 'start', alignOffset: 50}), []),
    );

    const options: ChartOptions<'line'> = useMemo(
      () => ({
        plugins: {
          legend: {display: false},
          tooltip: {
            enabled: false,
            position: 'nearest',
            external: renderTooltipFn,
          },
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false,
        },
        scales: {
          x: {
            ticks: {
              color: rgbColors[Colors.textLight()],
              maxRotation: 0,
              minRotation: 0,
              autoSkip: false,
              includeBounds: true,
            },
          },
          y: {
            grid: {color: rgbColors[Colors.keylineDefault()]},
            beginAtZero: true,
          },
        },
        responsive: true,
        maintainAspectRatio: false,
      }),
      [renderTooltipFn, rgbColors],
    );
    return (
      <div className={styles.chartContainer}>
        <div className={styles.chartHeader}>
          <Box flex={{direction: 'row', gap: 4, justifyContent: 'space-between'}}>
            <Subheading>{metrics.title}</Subheading>
            {loading ? <Spinner purpose="body-text" /> : null}
          </Box>
        </div>
        <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
          <div className={styles.chartCount}>
            {metrics.currentPeriod.aggregateValue
              ? numberFormatter.format(Math.round(metrics.currentPeriod.aggregateValue))
              : 0}
            <BodySmall color={Colors.textLight()}>{unitType}</BodySmall>
          </div>
          <div className={styles.chartChange}>
            {percentFormatter.format(metrics.pctChange ?? 0)}
          </div>
        </Box>
        <div className={styles.chartWrapper}>
          <div className={styles.chartGraph}>
            <Line data={getDataset(metrics, formatDatetime)} options={options} />
          </div>
        </div>
      </div>
    );
  },
);
