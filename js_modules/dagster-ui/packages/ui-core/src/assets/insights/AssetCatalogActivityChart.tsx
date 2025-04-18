import {BodyLarge, BodySmall, Box, Popover} from '@dagster-io/ui-components';
import React from 'react';

import styles from './AssetCatalogInsights.module.css';
import {numberFormatter} from '../../ui/formatters';

export type ActivityChartDayData = {
  date: string;
  hourlyValues: Array<number | null>;
};

export type ActivityChartData = {
  max: number | null;
  dataByDay: ActivityChartDayData[];
  header: string;
  color: string;
};

export const ActivityChart = React.memo(({metrics}: {metrics: ActivityChartData}) => {
  const {header, color, dataByDay, max} = metrics;
  return (
    <div className={styles.ActivityChartContainer}>
      <Box flex={{direction: 'row', alignItems: 'center'}} padding={{bottom: 12}}>
        <BodyLarge>{header}</BodyLarge>
      </Box>
      <div className={styles.ActivityChart}>
        {dataByDay.map((dayData) => (
          <ActivityChartRow
            key={dayData.date}
            date={dayData.date}
            hourlyValues={dayData.hourlyValues}
            max={max}
            color={color}
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
});

const ActivityChartRow = React.memo(
  ({
    date,
    hourlyValues,
    max,
    color,
  }: {
    date: string;
    hourlyValues: Array<number | null>;
    max: number | null;
    color: string;
  }) => {
    return (
      <div className={styles.ActivityChartRow}>
        <BodySmall>{date}</BodySmall>
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
            if (value === 0) {
              return (
                <div key={index} className={styles.TileContainer}>
                  <div className={styles.Tile} />
                </div>
              );
            }
            return (
              <Popover
                key={index}
                targetTagName="div"
                interactionKind="hover"
                content={
                  <div className={styles.Tooltip}>
                    <BodySmall>{numberFormatter.format(value)}</BodySmall>
                  </div>
                }
              >
                <div className={styles.TileContainer}>
                  <div className={styles.Tile} />
                  <div
                    className={styles.Tile}
                    style={{
                      backgroundColor: color,
                      opacity: value / (max || 1),
                    }}
                  />
                </div>
              </Popover>
            );
          })}
        </div>
      </div>
    );
  },
);
