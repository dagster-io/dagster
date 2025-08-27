import {
  Body,
  BodyLarge,
  BodySmall,
  Box,
  Colors,
  Mono,
  Popover,
  Spinner,
  Subheading,
} from '@dagster-io/ui-components';
import {memo} from 'react';

import {TooltipCard} from './InsightsChartShared';
import {formatDuration} from '../ui/formatDuration';
import {numberFormatterWithMaxFractionDigits} from '../ui/formatters';
import {useFormatDateTime} from '../ui/useFormatDateTime';
import styles from './css/ActivityChart.module.css';

export type ActivityChartMetricsDialogData<T> = {
  current: {
    before: number;
    after: number;
  };
  metric: T;
};

export type ActivityChartDayData = {
  date: number;
  hourlyValues: Array<number | null>;
};

export type ActivityChartData = {
  max: number | null;
  dataByDay: ActivityChartDayData[];
  header: string;
  color: string;
  hoverColor: string;
};

interface Props<T> {
  metrics: ActivityChartData;
  unit: string;
  loading: boolean;
  openMetricDialog?: (data: ActivityChartMetricsDialogData<T>) => void;
  metric: T;
}

const InnerActivityChart = <T,>(props: Props<T>) => {
  const {metrics, unit, loading, openMetricDialog, metric} = props;
  const {header, color, dataByDay, max, hoverColor} = metrics;
  return (
    <div className={styles.activityChartContainer}>
      <Box
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        padding={{bottom: 12}}
      >
        <BodyLarge>{header}</BodyLarge>
        {loading ? <Spinner purpose="body-text" /> : null}
      </Box>
      <div className={styles.activityChart}>
        {dataByDay.map((dayData) => (
          <ActivityChartRow
            key={dayData.date}
            date={dayData.date}
            hourlyValues={dayData.hourlyValues}
            max={max}
            color={color}
            hoverColor={hoverColor}
            unit={unit}
            onClick={openMetricDialog}
            metric={metric}
          />
        ))}
        <div className={styles.activityChartRow}>
          <div />
          <div className={styles.activityChartBottomLegend}>
            <BodySmall>12AM</BodySmall>
            <BodySmall>6AM</BodySmall>
            <BodySmall>12PM</BodySmall>
            <BodySmall>6PM</BodySmall>
            <BodySmall>12AM</BodySmall>
          </div>
        </div>
      </div>
    </div>
  );
};

export const ActivityChart = memo(InnerActivityChart) as typeof InnerActivityChart;

interface RowProps<T> {
  date: number;
  hourlyValues: Array<number | null>;
  max: number | null;
  color: string;
  hoverColor: string;
  unit: string;
  onClick?: (data: ActivityChartMetricsDialogData<T>) => void;
  metric: T;
}

const InnerActivityChartRow = <T,>(props: RowProps<T>) => {
  const {date, hourlyValues, max, color, unit, hoverColor, onClick, metric} = props;
  const formatDate = useFormatDateTime();
  const dayString = formatDate(new Date(date), {month: 'short', day: 'numeric'});

  return (
    <div className={styles.activityChartRow}>
      <BodySmall>{dayString}</BodySmall>
      <div className={styles.activityChartRowInnerGrid}>
        {hourlyValues.map((value, index) => {
          if (value === null) {
            return <div key={index} />;
          }

          const opacity = value / (max || 1);
          const {value: displayValue, unit: displayUnit} = (() => {
            const unitLower = unit.toLowerCase();
            if (unitLower === 'seconds' || unitLower === 'milliseconds') {
              return formatDuration(value, {unit: unitLower})[0];
            }
            return {value, unit};
          })();

          return (
            <Popover
              key={index}
              targetTagName="div"
              interactionKind="hover"
              popoverClassName={styles.popover}
              placement="top"
              content={
                <TooltipCard>
                  <Box flex={{direction: 'column'}}>
                    <Box border="bottom" padding={{horizontal: 12, vertical: 8}}>
                      <Subheading>
                        {formatDate(new Date(date + index * 60 * 60 * 1000), {
                          month: 'short',
                          day: 'numeric',
                          hour: 'numeric',
                          minute: 'numeric',
                        })}
                      </Subheading>
                    </Box>
                    <Box
                      flex={{direction: 'row', alignItems: 'center', gap: 4}}
                      padding={{horizontal: 12, vertical: 8}}
                    >
                      <Mono>{numberFormatterWithMaxFractionDigits(2).format(displayValue)}</Mono>
                      <Body color={Colors.textLight()}>{displayUnit}</Body>
                    </Box>
                    {value > 0 && onClick ? (
                      <Box padding={{horizontal: 12, vertical: 8}} border="top">
                        <Body color={Colors.textLight()}>Click to view details</Body>
                      </Box>
                    ) : null}
                  </Box>
                </TooltipCard>
              }
            >
              <div
                className={styles.tileContainer}
                style={
                  {
                    '--tile-hover-color': hoverColor,
                    '--tile-color': color,
                  } as React.CSSProperties
                }
              >
                <div className={styles.placeholderTile} />
                {opacity ? (
                  <button
                    className={styles.tileButton}
                    style={{opacity}}
                    onClick={() => {
                      if (onClick) {
                        onClick({
                          current: {
                            before: date / 1000 + (index - 1) * 60 * 60,
                            after: date / 1000 + index * 60 * 60,
                          },
                          metric,
                        });
                      }
                    }}
                  />
                ) : null}
              </div>
            </Popover>
          );
        })}
      </div>
    </div>
  );
};

export const ActivityChartRow = memo(InnerActivityChartRow) as typeof InnerActivityChartRow;
