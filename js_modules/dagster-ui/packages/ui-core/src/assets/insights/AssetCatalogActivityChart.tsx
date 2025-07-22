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
import clsx from 'clsx';
import React from 'react';

import styles from './AssetCatalogInsights.module.css';
import {AssetCatalogMetricNames} from './AssetCatalogMetricUtils';
import {TooltipCard} from '../../insights/InsightsChartShared';
import {formatDuration} from '../../ui/formatDuration';
import {numberFormatterWithMaxFractionDigits} from '../../ui/formatters';
import {useFormatDateTime} from '../../ui/useFormatDateTime';

type MetricsDialogData = {
  after: number;
  before: number;
  metric: AssetCatalogMetricNames;
  unit: string;
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

export const ActivityChart = React.memo(
  ({
    metrics,
    unit,
    loading,
    openMetricDialog,
    metric,
  }: {
    metrics: ActivityChartData;
    unit: string;
    loading: boolean;
    openMetricDialog: ({before, after, metric, unit}: MetricsDialogData) => void;
    metric: AssetCatalogMetricNames;
  }) => {
    const {header, color, dataByDay, max, hoverColor} = metrics;
    return (
      <div className={styles.ActivityChartContainer}>
        <Box
          flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
          padding={{bottom: 12}}
        >
          <BodyLarge>{header}</BodyLarge>
          {loading ? <Spinner purpose="body-text" /> : null}
        </Box>
        <div className={styles.ActivityChart}>
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
          <div className={styles.ActivityChartRow}>
            <div />
            <div className={styles.ActivityChartBottomLegend}>
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
  },
);

const ActivityChartRow = React.memo(
  ({
    date,
    hourlyValues,
    max,
    color,
    unit,
    hoverColor,
    onClick,
    metric,
  }: {
    date: number;
    hourlyValues: Array<number | null>;
    max: number | null;
    color: string;
    hoverColor: string;
    unit: string;
    onClick: (data: MetricsDialogData) => void;
    metric: AssetCatalogMetricNames;
  }) => {
    const formatDate = useFormatDateTime();
    return (
      <div className={styles.ActivityChartRow}>
        <BodySmall>{formatDate(new Date(date), {month: 'short', day: 'numeric'})}</BodySmall>
        <div
          style={{
            display: 'grid',
            gap: 2,
            gridTemplateColumns: 'repeat(24, 1fr)',
            gridTemplateRows: '16px',
          }}
        >
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
                popoverClassName={styles.Popover}
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
                      {value > 0 ? (
                        <Box padding={{horizontal: 12, vertical: 8}} border="top">
                          <Body color={Colors.textLight()}>Click to view details</Body>
                        </Box>
                      ) : null}
                    </Box>
                  </TooltipCard>
                }
              >
                <div
                  className={clsx(styles.TileContainer, opacity ? styles.clickable : null)}
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
                        onClick({
                          before: date / 1000 + index * 60 * 60,
                          after: date / 1000 + (index - 1) * 60 * 60,
                          metric,
                          unit,
                        });
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
  },
);
