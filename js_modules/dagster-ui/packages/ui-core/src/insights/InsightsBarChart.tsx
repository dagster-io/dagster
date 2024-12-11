import {Colors, FontFamily, NonIdealState, SpinnerWithText} from '@dagster-io/ui-components';
import {
  ActiveElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  ChartOptions,
  Filler,
  LinearScale,
  Tooltip,
} from 'chart.js';
import * as React from 'react';
import {useCallback, useContext, useMemo} from 'react';
import {Bar} from 'react-chartjs-2';

import {iconNameForMetric} from './IconForMetricName';
import {InsightsBarChartTooltip} from './InsightsBarChartTooltip';
import {EmptyStateContainer, LoadingStateContainer} from './InsightsChartShared';
import {formatMetric} from './formatMetric';
import {RenderTooltipFn, renderInsightsChartTooltip} from './renderInsightsChartTooltip';
import {BarDatapoint, BarValue, DatapointType, ReportingUnitType} from './types';
import {TimeContext} from '../app/time/TimeContext';
import {useRGBColorsForTheme} from '../app/useRGBColorsForTheme';
import {useOpenInNewTab} from '../hooks/useOpenInNewTab';
import {useFormatDateTime} from '../ui/useFormatDateTime';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Filler);

interface Props {
  loading: boolean;
  datapointType: DatapointType;
  unitType: ReportingUnitType;
  costMultiplier: number | null;
  metricName: string;
  metricLabel: string;
  timestamps: number[];
  datapoint: BarDatapoint;
  emptyState?: React.ReactNode;
}

const SPINNER_WAIT_MSEC = 1000;

export const InsightsBarChart = (props: Props) => {
  const {
    loading,
    datapointType,
    unitType,
    metricLabel,
    metricName,
    timestamps,
    datapoint,
    costMultiplier,
    emptyState,
  } = props;
  const {label, barColor, values} = datapoint;

  const rgbColors = useRGBColorsForTheme();
  const [canShowSpinner, setCanShowSpinner] = React.useState(false);
  const openInNewTab = useOpenInNewTab();

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setCanShowSpinner(true);
    }, SPINNER_WAIT_MSEC);
    return () => clearTimeout(timer);
  }, []);

  const yMax = React.useMemo(() => {
    const allValues = values
      .filter((value): value is BarValue => value !== null)
      .map(({value}) => value);
    const maxValue = Math.max(...allValues);
    return Math.ceil(maxValue * 1.05);
  }, [values]);

  const formatDateTime = useFormatDateTime();
  const {
    timezone: [timezone],
    hourCycle: [hourCycle],
  } = useContext(TimeContext);

  // Don't show the y axis while loading datapoints, to avoid jumping renders.
  const showYAxis = values.length > 0;

  const barColorRGB = rgbColors[barColor]!;
  const keylineDefaultRGB = rgbColors[Colors.keylineDefault()];
  const textLighterRGB = rgbColors[Colors.textLighter()];

  const data = React.useMemo(() => {
    return {
      labels: timestamps,
      datasets: [
        {
          label,
          data: values.map((value) => value?.value),
          backgroundColor: barColorRGB.replace(/, 1\)/, ', 0.6)'),
          hoverBackgroundColor: barColorRGB,
        },
      ],
    };
  }, [timestamps, label, values, barColorRGB]);

  const onClick = useCallback(
    (element: ActiveElement | null) => {
      if (element) {
        const whichBar = values[element.index];
        if (whichBar?.href) {
          openInNewTab(whichBar.href);
        }
        return;
      }
    },
    [values, openInNewTab],
  );

  const renderTooltipFn: RenderTooltipFn = useCallback(
    (config) => {
      const {color, label, date, formattedValue} = config;
      return (
        <InsightsBarChartTooltip
          color={color}
          type={datapointType}
          label={label || ''}
          date={date}
          timezone={timezone}
          hourCycle={hourCycle}
          formattedValue={formattedValue}
          unitType={unitType}
          costMultiplier={costMultiplier}
          metricLabel={metricLabel}
        />
      );
    },
    [datapointType, timezone, hourCycle, unitType, costMultiplier, metricLabel],
  );

  const yAxis = useMemo(() => {
    return {
      display: showYAxis,
      grid: {
        color: keylineDefaultRGB,
      },
      title: {
        display: true,
        text: metricLabel,
        font: {
          weight: '700',
          size: 12,
        },
      },
      ticks: {
        font: {
          color: {
            color: textLighterRGB,
          },
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

  const options: ChartOptions<'bar'> = React.useMemo(() => {
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
            return renderInsightsChartTooltip({...context, renderFn: renderTooltipFn});
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
          grid: {
            display: false,
          },
          title: {
            display: true,
          },
          ticks: {
            font: {
              color: {
                color: textLighterRGB,
              },
              size: 12,
              family: FontFamily.monospace,
            },
            callback(timestamp) {
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
  }, [textLighterRGB, yAxis, onClick, renderTooltipFn, formatDateTime]);

  const emptyContent = () => {
    const anyDatapoints = values.length > 0;

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
      <Bar key={datapointType} data={data} options={options} />
    </div>
  );
};
