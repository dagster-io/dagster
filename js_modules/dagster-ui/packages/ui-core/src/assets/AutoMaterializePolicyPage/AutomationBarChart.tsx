import {Colors, FontFamily, NonIdealState, SpinnerWithText} from '@dagster-io/ui-components';
import {ActiveElement, ChartOptions} from 'chart.js';
import {useCallback, useMemo} from 'react';
import {Bar} from 'react-chartjs-2';

import {AnimationBarChartTooltip} from './AnimationBarChartTooltip';
import {useRGBColorsForTheme} from '../../app/useRGBColorsForTheme';
import {EmptyStateContainer, LoadingStateContainer} from '../../insights/InsightsChartShared';
import {formatMetric} from '../../insights/formatMetric';
import {
  RenderTooltipFn,
  renderInsightsChartTooltip,
} from '../../insights/renderInsightsChartTooltip';
import {ReportingUnitType} from '../../insights/types';
import {useFormatDateTime} from '../../ui/useFormatDateTime';

interface Props {
  loading: boolean;
  timestamps: number[];
  values: {value: number | null; evaluationID: string}[];
  onClickEvaluation: (evaluationID: string) => void;
}

export const AutomationBarChart = ({loading, timestamps, values, onClickEvaluation}: Props) => {
  const numValues = values.length;
  const numTimestamps = timestamps.length;

  const rgbColors = useRGBColorsForTheme();
  const formatDateTime = useFormatDateTime();

  const yMax = useMemo(() => {
    if (values.length === 0) {
      return 1;
    }

    const allValues = values
      .map(({value}) => value)
      .filter((value): value is number => value !== null);
    const maxValue = Math.max(...allValues);
    return Math.ceil(maxValue * 1.05);
  }, [values]);

  // Don't show the y axis while loading datapoints, to avoid jumping renders.
  // const showYAxis = values.length > 0;

  const barColorRGB = rgbColors[Colors.accentBlue()]!;
  const keylineDefaultRGB = rgbColors[Colors.keylineDefault()];
  const textLighterRGB = rgbColors[Colors.textLighter()];

  const data = useMemo(() => {
    return {
      labels: timestamps,
      datasets: [
        {
          data: values.map(({value}) => value),
          backgroundColor: barColorRGB.replace(/, 1\)/, ', 0.6)'),
          hoverBackgroundColor: barColorRGB,
        },
      ],
    };
  }, [timestamps, values, barColorRGB]);

  const yAxis = useMemo(() => {
    return {
      display: true,
      border: {
        display: true,
        color: keylineDefaultRGB,
      },
      grid: {
        display: true,
        color: keylineDefaultRGB,
      },
      title: {
        display: true,
        text: 'Run requests',
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
        autoSkip: true,
        autoSkipPadding: 20,
        callback(value: string | number) {
          return formatMetric(value, ReportingUnitType.INTEGER, {
            integerFormat: 'compact',
            floatPrecision: 'maximum-precision',
            floatFormat: 'compact-above-threshold',
          });
        },
      },
      min: 0,
      suggestedMax: yMax,
    };
  }, [keylineDefaultRGB, textLighterRGB, yMax]);

  const onClick = useCallback(
    (element: ActiveElement | null) => {
      if (element) {
        const whichBar = values[element.index];
        if (whichBar?.evaluationID) {
          onClickEvaluation(whichBar.evaluationID);
        }
        return;
      }
    },
    [values, onClickEvaluation],
  );

  const renderTooltipFn: RenderTooltipFn = useCallback(
    (config) => {
      const {date, formattedValue} = config;
      return (
        <AnimationBarChartTooltip
          dateTimeString={formatDateTime(date, {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric',
            second: 'numeric',
          })}
          formattedValue={formattedValue}
          metricLabel="Run requests"
        />
      );
    },
    [formatDateTime],
  );

  const options: ChartOptions<'bar'> = useMemo(() => {
    return {
      // dish: Disable animation until I can figure out why it's acting crazy.
      // When rendering a responsive grid of charts, it's doing a distracting
      // zoom-like animation on initial render.
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      onClick: (_event, elements) => onClick(elements[0] || null),
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: false,
          external: (context) => {
            return renderInsightsChartTooltip({
              ...context,
              // Place the tooltip on the bottom of the chart.
              tooltip: {...context.tooltip, caretY: 260},
              renderFn: renderTooltipFn,
            });
          },
        },
      },
      interaction: {
        intersect: false,
        mode: 'x',
      },
      scales: {
        x: {
          display: true,
          border: {
            display: true,
            color: keylineDefaultRGB,
          },
          grid: {
            color: keylineDefaultRGB,
          },
          title: {
            display: true,
          },
          ticks: {
            font: {
              size: 12,
              family: FontFamily.monospace,
            },
            color: textLighterRGB,
            maxRotation: 0,
            autoSkip: true,
            autoSkipPadding: 20,
            callback(timestamp, index) {
              if (index > 0 && index < numTimestamps - 1) {
                return '';
              }
              const label = this.getLabelForValue(Number(timestamp));
              return formatDateTime(new Date(label), {
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: 'numeric',
              });
            },
          },
        },
        y: yAxis,
      },
    };
  }, [
    keylineDefaultRGB,
    textLighterRGB,
    yAxis,
    onClick,
    renderTooltipFn,
    numTimestamps,
    formatDateTime,
  ]);

  const emptyContent = () => {
    // If there is some data, we don't want to show a loading or empty state.
    // Or, if we shouldn't show the spinner yet (due to the delay) we also shouldn't
    // show anything yet.
    if (numValues) {
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
        <NonIdealState
          icon="search"
          title="No evaluations found"
          description="No evaluations were found for this asset"
        />
      </EmptyStateContainer>
    );
  };

  return (
    <div style={{height: '100%', position: 'relative'}}>
      {emptyContent()}
      <Bar key="materializations" data={data} options={options} />
    </div>
  );
};
