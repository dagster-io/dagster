import {
  Body,
  BodyLarge,
  BodySmall,
  Box,
  Button,
  Colors,
  Icon,
  MiddleTruncate,
  Mono,
  Spinner,
  Subheading,
} from '@dagster-io/ui-components';
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  ChartOptions,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js';
import React, {useCallback, useMemo, useState} from 'react';
import {Bar} from 'react-chartjs-2';

import styles from './AssetCatalogTopAssetsChart.module.css';
import {Context, useRenderChartTooltip} from './renderChartTooltip';
import {useRGBColorsForTheme} from '../../app/useRGBColorsForTheme';
import {TooltipCard} from '../../insights/InsightsChartShared';
import {numberFormatter} from '../../ui/formatters';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const PAGE_SIZE = 10;

export const AssetCatalogTopAssetsChart = React.memo(
  ({
    header,
    datasets,
    unitType,
    loading,
  }: {
    header: string;
    datasets: {labels: string[]; data: number[]};
    unitType: string;
    loading: boolean;
  }) => {
    const rgbColors = useRGBColorsForTheme();

    const [page, setPage] = useState(0);

    const values = useMemo(() => {
      return datasets.labels
        .map((label, i) => ({
          label,
          value: datasets.data[i]!,
        }))
        .filter(({value}) => value !== 0)
        .sort((a, b) => b.value - a.value);
    }, [datasets.data, datasets.labels]);

    // Compute the max value from all values for consistent X axis scaling
    const maxValue = useMemo(() => {
      return values.length > 0 ? Math.max(...values.map(({value}) => value)) : undefined;
    }, [values]);

    const totalPages = Math.ceil(values.length / PAGE_SIZE);

    const currentPageValues = useMemo(
      () => values.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE),
      [page, values],
    );

    const renderTooltipFn = useRenderChartTooltip(
      useCallback(
        ({context}: {context: Context}) => {
          const {tooltip} = context;
          const d = tooltip.dataPoints[0];
          return (
            <TooltipCard>
              <Box flex={{direction: 'column', gap: 4}} padding={{vertical: 8, horizontal: 12}}>
                <Box border="bottom" padding={{bottom: 4}} margin={{bottom: 4}}>
                  <Subheading>{d?.label}</Subheading>
                </Box>
                <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                  <Mono>{d?.formattedValue}</Mono>
                  <Body>{unitType}</Body>
                </Box>
              </Box>
            </TooltipCard>
          );
        },
        [unitType],
      ),
      useMemo(() => ({side: 'right', align: 'center'}), []),
    );

    const chartConfig = useMemo(
      () => ({
        labels: currentPageValues.map(({label}) => label),
        datasets: [
          {
            label: unitType,
            data: currentPageValues.map(({value}) => value),
            backgroundColor: rgbColors[Colors.accentBlue()],
            borderRadius: 0,
            maxBarThickness: 10,
          },
        ],
      }),
      [unitType, currentPageValues, rgbColors],
    );

    const options: ChartOptions<'bar'> = useMemo(
      () => ({
        indexAxis: 'y' as const,
        scales: {
          x: {
            beginAtZero: true,
            max: maxValue,
            grid: {color: rgbColors[Colors.keylineDefault()], borderDash: [4, 4]},
          },
          y: {grid: {display: false}, ticks: {display: false}, beginAtZero: true},
        },
        plugins: {
          legend: {display: false},
          tooltip: {
            enabled: false,
            position: 'nearest',
            external: renderTooltipFn,
          },
        },
      }),
      [maxValue, rgbColors, renderTooltipFn],
    );

    return (
      <div className={styles.container}>
        <Box flex={{direction: 'row', gap: 12, justifyContent: 'space-between'}}>
          <BodyLarge>{header}</BodyLarge>
          {loading ? <Spinner purpose="body-text" /> : null}
        </Box>
        <Box border="bottom" padding={{bottom: 12}} style={{position: 'relative'}}>
          <Bar data={chartConfig} options={options} />
        </Box>
        <div>
          <Box
            flex={{direction: 'row', justifyContent: 'space-between', gap: 12}}
            style={{color: Colors.textLighter()}}
            border="bottom"
            padding={{vertical: 8}}
          >
            <BodySmall>Asset</BodySmall>
            <BodySmall>{unitType}</BodySmall>
          </Box>
          <div className={styles.table}>
            {currentPageValues.map(({label, value}, i) => (
              <React.Fragment key={i}>
                <BodySmall as="div" color={Colors.textLight()}>
                  <MiddleTruncate text={label} />
                </BodySmall>
                <BodySmall color={Colors.textDefault()}>
                  {numberFormatter.format(Math.round(value))}
                </BodySmall>
              </React.Fragment>
            ))}
          </div>
        </div>
        {totalPages > 1 && (
          <Box
            flex={{
              alignItems: 'flex-end',
              grow: 1,
              direction: 'row',
            }}
          >
            <Box
              flex={{
                direction: 'row',
                grow: 1,
                alignItems: 'flex-end',
                justifyContent: 'stretch',
              }}
              border="top"
              padding={{top: 12, horizontal: 8}}
            >
              <Box
                flex={{
                  direction: 'row',
                  gap: 12,
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
                style={{width: '100%'}}
              >
                <BodySmall>
                  {page + 1} of {totalPages}
                </BodySmall>
                <Box flex={{direction: 'row', gap: 4}}>
                  <Button
                    outlined
                    onClick={() => setPage(page - 1)}
                    disabled={page === 0}
                    icon={<Icon name="arrow_back" />}
                  />
                  <Button
                    outlined
                    onClick={() => setPage(page + 1)}
                    disabled={page === totalPages - 1}
                    icon={<Icon name="arrow_forward" />}
                  />
                </Box>
              </Box>
            </Box>
          </Box>
        )}
      </div>
    );
  },
);
