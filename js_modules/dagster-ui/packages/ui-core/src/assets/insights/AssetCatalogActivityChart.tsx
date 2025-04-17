import {BodyLarge, BodySmall, Box, Popover} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import React from 'react';

import styles from './AssetCatalogInsights.module.css';
import {numberFormatter} from '../../ui/formatters';

const hours = Array.from({length: 24}, (_, i) => i);

export const ActivityChart = React.memo(({header, color}: {header: string; color: string}) => {
  return (
    <div className={styles.ActivityChartContainer}>
      <Box flex={{direction: 'row', alignItems: 'center'}} padding={{bottom: 12}}>
        <BodyLarge>{header}</BodyLarge>
      </Box>
      <div className={styles.ActivityChart}>
        <ActivityChartRow
          date="2024-04-16"
          data={hours.map((hour) => {
            if (hour > 16) {
              return null;
            }
            const value = Math.random() * 100;
            return value > 50 ? value : 0;
          })}
          max={100}
          color={color}
        />
        <ActivityChartRow
          date="2024-04-15"
          data={hours.map(() => Math.random() * 100)}
          max={100}
          color={color}
        />
        <ActivityChartRow
          date="2024-04-14"
          data={hours.map(() => Math.random() * 100)}
          max={100}
          color={color}
        />
        <ActivityChartRow
          date="2024-04-13"
          data={hours.map(() => Math.random() * 100)}
          max={100}
          color={color}
        />
        <ActivityChartRow
          date="2024-04-12"
          data={hours.map(() => Math.random() * 100)}
          max={100}
          color={color}
        />
        <ActivityChartRow
          date="2024-04-11"
          data={hours.map(() => Math.random() * 100)}
          max={100}
          color={color}
        />
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
    data,
    max,
    color,
  }: {
    date: string;
    data: Array<number | null>;
    max: number;
    color: string;
  }) => {
    return (
      <div className={styles.ActivityChartRow}>
        <BodySmall>{dayjs(date).format('MMM D')}</BodySmall>
        <div
          style={{
            display: 'grid',
            gap: 2,
            gridTemplateColumns: 'repeat(24, 1fr)',
            gridTemplateRows: '16px',
          }}
        >
          {data.map((value, index) => {
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
                      opacity: value / max,
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
