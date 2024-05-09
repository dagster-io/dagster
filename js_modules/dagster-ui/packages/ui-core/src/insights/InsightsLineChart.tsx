import {Colors, FontFamily, NonIdealState, SpinnerWithText} from '@dagster-io/ui-components';
import {
  ActiveElement,
  CategoryScale,
  Chart as ChartJS,
  ChartOptions,
  Filler,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js';
import debounce from 'lodash/debounce';
import * as React from 'react';
import {useCallback, useMemo} from 'react';
import {Line} from 'react-chartjs-2';

import {iconNameForMetric} from './IconForMetricName';
import {EmptyStateContainer, LoadingStateContainer} from './InsightsChartShared';
import {InsightsLineChartTooltip} from './InsightsLineChartTooltip';
import {COMPACT_COST_FORMATTER, TOTAL_COST_FORMATTER} from './costFormatters';
import {formatMetric, stripFormattingFromNumber} from './formatMetric';
import {RenderTooltipFn, renderInsightsChartTooltip} from './renderInsightsChartTooltip';
import {Datapoint, DatapointType, ReportingMetricsGranularity, ReportingUnitType} from './types';
import {useRGBColorsForTheme} from '../app/useRGBColorsForTheme';
import {useFormatDateTime} from '../ui/useFormatDateTime';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

interface Props {
  loading: boolean;
  datapointType: DatapointType;
  unitType: ReportingUnitType;
  granularity: ReportingMetricsGranularity;
  metricName: string;
  metricLabel: string;
  costMultiplier: number | null;
  timestamps: number[];
  datapoints: Record<string, Datapoint>;
  highlightKey: string | null;
  onHighlightKey?: (key: string | null) => void;
  emptyState?: React.ReactNode;
}

const SPINNER_WAIT_MSEC = 2000;

export const InsightsLineChart = (props: Props) => {
  const {
    loading,
    datapointType,
    unitType,
    granularity,
    metricLabel,
    metricName,
    costMultiplier,
    timestamps,
    datapoints,
    highlightKey,
    onHighlightKey,
    emptyState,
  } = props;

  const rgbColors = useRGBColorsForTheme();

  const dataValues = React.useMemo(() => Object.values(datapoints), [datapoints]);
  const dataEntries = React.useMemo(() => Object.entries(datapoints), [datapoints]);

  const [canShowSpinner, setCanShowSpinner] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setCanShowSpinner(true);
    }, SPINNER_WAIT_MSEC);
    return () => clearTimeout(timer);
  }, []);

  const yMax = React.useMemo(() => {
    const allData = dataValues
      .map(({values}) => values)
      .flat()
      .filter((value) => value !== null) as number[];
    const maxValue = Math.max(...allData);
    return Math.ceil(maxValue * 1.05);
  }, [dataValues]);

  const formatDateTime = useFormatDateTime();

  // Don't show the y axis while loading datapoints, to avoid jumping renders.
  const showYAxis = dataValues.length > 0;

  const data = React.useMemo(() => {
    const backgroundDefaultRGB = rgbColors[Colors.backgroundDefault()];
    const backgroundDefaultHoverRGB = rgbColors[Colors.backgroundDefaultHover()];
    return {
      labels: timestamps,
      datasets: dataEntries.map(([key, {label, lineColor, values}]) => {
        const rgbLineColor = rgbColors[lineColor]!;
        return {
          label,
          data: values,
          backgroundColor: (context: any) => {
            return buildFillGradient(context.chart.ctx, rgbLineColor);
          },
          borderColor:
            key === highlightKey || highlightKey === null
              ? rgbLineColor
              : rgbLineColor.replace(/, ?1\)/, ', 0.2)'),
          fill: key === highlightKey,
          pointBackgroundColor: backgroundDefaultRGB,
          pointHoverBackgroundColor: backgroundDefaultHoverRGB,
          pointBorderColor:
            key === highlightKey || highlightKey === null
              ? rgbLineColor
              : rgbLineColor.replace(/, ?1\)/, ', 0.2)'),
          pointRadius: key === highlightKey || highlightKey === null ? 3 : 0,
          tension: 0.1,
          // Render highlighted lines above non-highlighted lines, to avoid confusion at
          // intersections
          order: key === highlightKey || highlightKey === null ? 0 : 1,
        };
      }),
    };
  }, [timestamps, dataEntries, rgbColors, highlightKey]);

  const debouncedSetHighlightKey = React.useMemo(
    () => debounce((key: string | null) => onHighlightKey && onHighlightKey(key), 40),
    [onHighlightKey],
  );

  const onHover = React.useCallback(
    (element: ActiveElement | null) => {
      if (element) {
        const dataEntry = dataEntries[element.datasetIndex];
        if (dataEntry) {
          const [key] = dataEntry;
          debouncedSetHighlightKey(key);
          return;
        }
      }
      debouncedSetHighlightKey(null);
    },
    [dataEntries, debouncedSetHighlightKey],
  );

  const keylineDefaultRGB = rgbColors[Colors.keylineDefault()];
  const textLighterRGB = rgbColors[Colors.textLighter()];

  const yCount = useMemo(() => {
    return {
      display: showYAxis,
      grid: {
        color: keylineDefaultRGB,
      },
      title: {
        display: true,
        text: metricLabel,
        color: textLighterRGB,
        font: {
          weight: '700',
          size: 12,
        },
      },
      ticks: {
        color: textLighterRGB,
        font: {
          size: 12,
          family: FontFamily.monospace,
        },
        callback(value: string | number) {
          return formatMetric(value, unitType, {
            integerFormat: 'compact',
            floatPrecision: 'maximum-precision',
            floatFormat: 'compact-above-threshold',
          });
        },
      },
      min: 0,
      suggestedMax: yMax,
    };
  }, [keylineDefaultRGB, metricLabel, showYAxis, textLighterRGB, unitType, yMax]);

  const yCost = useMemo(() => {
    const yCostMax = yMax * Number(costMultiplier);
    return {
      display: !!(showYAxis && costMultiplier),
      grid: {
        display: false,
      },
      position: 'right' as const,
      title: {
        display: true,
        text: 'Estimated cost',
        color: textLighterRGB,
        font: {
          weight: '700',
          size: 12,
        },
      },
      ticks: {
        color: textLighterRGB,
        font: {
          size: 12,
          family: FontFamily.monospace,
        },
        callback(value: string | number) {
          const num = stripFormattingFromNumber(value);
          return yCostMax > 5
            ? COMPACT_COST_FORMATTER.format(num)
            : TOTAL_COST_FORMATTER.format(num);
        },
      },
      min: 0,
      suggestedMax: yCostMax,
    };
  }, [costMultiplier, showYAxis, textLighterRGB, yMax]);

  const renderTooltipFn: RenderTooltipFn = useCallback(
    (config) => {
      const {color, label, date, formattedValue} = config;
      return (
        <InsightsLineChartTooltip
          color={color}
          type={datapointType}
          label={label || ''}
          date={date}
          formattedValue={formattedValue}
          granularity={granularity}
          unitType={unitType}
          costMultiplier={costMultiplier}
          metricLabel={metricLabel}
        />
      );
    },
    [costMultiplier, datapointType, granularity, metricLabel, unitType],
  );

  const options: ChartOptions<'line'> = React.useMemo(() => {
    return {
      responsive: true,
      maintainAspectRatio: false,
      onHover: (_event, elements) => onHover(elements[0] || null),
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: false,
          position: 'nearest',
          external: (context) =>
            renderInsightsChartTooltip({...context, renderFn: renderTooltipFn}),
        },
      },
      interaction: {
        intersect: false,
      },
      scales: {
        x: {
          display: true,
          grid: {
            display: false,
          },
          title: {
            display: true,
            color: rgbColors[Colors.textLighter()],
          },
          ticks: {
            color: rgbColors[Colors.textLighter()],
            font: {
              size: 12,
              family: FontFamily.monospace,
            },
            callback(timestamp) {
              const label = this.getLabelForValue(Number(timestamp));
              return formatDateTime(new Date(label), {
                month: 'short',
                day: 'numeric',
                timeZone: 'UTC',
              });
            },
          },
        },
        yCount,
        yCost,
      },
    };
  }, [rgbColors, yCount, yCost, onHover, renderTooltipFn, formatDateTime]);

  const emptyContent = () => {
    const anyDatapoints = Object.keys(datapoints).length > 0;

    // If there is some data, we don't want to show a loading or empty state.
    // Or, if we shouldn't show the spinner yet (due to the delay) we also shouldn't
    // show anything yet.
    if (anyDatapoints || !canShowSpinner) {
      return null;
    }

    if (loading) {
      return (
        <LoadingStateContainer>
          <SpinnerWithText label="Loading…" />
        </LoadingStateContainer>
      );
    }

    return (
      <EmptyStateContainer>
        {emptyState || (
          <NonIdealState
            icon={iconNameForMetric(metricName)}
            title="No results found"
            description={
              <span>
                No data was found for <strong>{metricLabel}</strong> for these filters.
              </span>
            }
          />
        )}
      </EmptyStateContainer>
    );
  };

  return (
    <div style={{height: '100%', position: 'relative'}}>
      {emptyContent()}
      <Line key={datapointType} data={data} options={options} />
    </div>
  );
};

const buildFillGradient = (ctx: CanvasRenderingContext2D, lineColor: string) => {
  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, lineColor.replace(/, ?1\)/, ', 0.2)'));
  gradient.addColorStop(1, lineColor.replace(/, ?1\)/, ', 0.0)'));
  return gradient;
};
