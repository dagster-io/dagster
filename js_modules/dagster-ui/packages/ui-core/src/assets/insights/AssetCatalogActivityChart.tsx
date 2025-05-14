import {
  Body,
  BodyLarge,
  BodySmall,
  Box,
  Mono,
  Popover,
  Spinner,
  Subheading,
} from '@dagster-io/ui-components';
import React, {useState} from 'react';
import styles from './AssetCatalogInsights.module.css';
import {TooltipCard} from '../../insights/InsightsChartShared';
import {numberFormatter} from '../../ui/formatters';
import {useFormatDateTime} from '../../ui/useFormatDateTime';
import { ActivityChartDialogData, AssetCatalogActivityChartDialog } from 'shared/assets/insights/AssetCatalogActivityChartDialog.oss';
import { AssetTableFragment } from '../types/AssetTableFragment.types';

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

type ActivityChartDialogDayData = {
  after: number; 
  before: number;
}

export const ActivityChart = React.memo(
  ({metrics, unit, loading, selectorData}: {metrics: ActivityChartData; unit: string; loading: boolean; selectorData: {metric: string; assets: AssetTableFragment[], selection: string}}) => {
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [dialogConfig, setDialogConfig] = useState({
      before: 0,
      after: 0,
      metric: selectorData.metric,
      assets: selectorData.assets,
      selection: selectorData.selection,
    });

    const openWithTimeRange = ({before, after}: ActivityChartDialogDayData) => {
      setDialogConfig({
        before,
        after,
        metric: selectorData.metric,
        assets: selectorData.assets,
        selection: selectorData.selection,
      });
      setIsDialogOpen(true);
    };

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
        <AssetCatalogActivityChartDialog dialogConfig={dialogConfig} isOpen={isDialogOpen} onClose={() => {setIsDialogOpen(false)}}/>
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
              onClick={openWithTimeRange}
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
  }: {
    date: number;
    hourlyValues: Array<number | null>;
    max: number | null;
    color: string;
    hoverColor: string;
    unit: string;
    onClick: (data: ActivityChartDialogDayData) => void;
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
            return (
              <Popover
                key={index}
                targetTagName="div"
                interactionKind="hover"
                popoverClassName={styles.Popover}
                content={
                  <TooltipCard>
                    <Box
                      flex={{direction: 'column', gap: 4}}
                      padding={{vertical: 8, horizontal: 12}}
                    >
                      <Box border="bottom" padding={{bottom: 4}} margin={{bottom: 4}}>
                        <Subheading>
                          {formatDate(new Date(date + index * 60 * 60 * 1000), {
                            month: 'short',
                            day: 'numeric',
                            hour: 'numeric',
                            minute: 'numeric',
                          })}
                        </Subheading>
                      </Box>
                      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                        <Mono>{numberFormatter.format(value)}</Mono>
                        <Body>{unit}</Body>
                      </Box>
                      <BodySmall>Click for asset breakdown</BodySmall>
                    </Box>
                  </TooltipCard>
                }
              >
                <div className={styles.TileContainer}>
                  <div className={styles.Tile} />
                  {opacity ? (
                    <div
                      className={styles.Tile}
                      style={
                        {
                          '--tile-color': color,
                          '--tile-hover-color': hoverColor,
                          opacity,
                        } as React.CSSProperties
                      }
                      onClick={() => {onClick({
                        before: (date/1000) + (index + 1) * 60 * 60,
                        after: (date/1000) + index * 60 * 60,
                      })}}
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
