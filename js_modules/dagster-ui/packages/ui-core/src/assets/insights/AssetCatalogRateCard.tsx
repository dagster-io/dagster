import {BodyLarge, Box, Colors, Icon, Spinner} from '@dagster-io/ui-components';
import React from 'react';

import styles from './AssetCatalogRateCard.module.css';
import {numberFormatter} from '../../ui/formatters';

export interface AssetCatalogRateCardProps {
  title: string;
  value: number | null; // e.g., 0.981 for 98.1%
  prevValue: number | null; // e.g., 1 for 100%
  loading: boolean;
  unit: 'percent' | 'seconds';
}

function pct_change(x: number, y: number): number {
  if (x === 0) {
    if (y === 0) {
      return 0.0; // No change
    }
    return Number.POSITIVE_INFINITY;
  }

  if (y > x) {
    return Math.round(1000 * (y / x - 1)) / 10;
  }
  return Math.round(-(1000 * (1 - y / x))) / 10;
}

function formatValues(
  valueOrNull: number | null,
  prevValueOrNull: number | null,
  unit: 'percent' | 'seconds',
): {
  currValueString: string;
  prevValueString: string;
  absDeltaString: string;
  isDown: boolean;
} {
  let value = valueOrNull ?? 0;
  let prevValue = prevValueOrNull ?? 0;

  if (unit === 'percent') {
    value = Math.round(value * 1000) / 10;
    prevValue = Math.round(prevValue * 1000) / 10;
  }

  const deltaPct = pct_change(prevValue, value);
  const isDown = deltaPct < 0;
  const absDeltaPct = Math.abs(deltaPct);
  const unitString = unit === 'percent' ? '%' : ' seconds';

  return {
    currValueString: numberFormatter.format(value) + unitString,
    prevValueString: numberFormatter.format(prevValue) + unitString,
    absDeltaString: numberFormatter.format(absDeltaPct) + '%', // delta is always in percent
    isDown,
  };
}

export function AssetCatalogRateCard({
  title,
  value,
  prevValue,
  loading,
  unit,
}: AssetCatalogRateCardProps) {
  const {currValueString, prevValueString, absDeltaString, isDown} = formatValues(
    value,
    prevValue,
    unit,
  );

  const noDataAvailableCard = (
    <div className={styles.rateCardNoDataContainer}>
      <div className={styles.rateCardNoDataPercentContainer}>%</div>
      No data available
    </div>
  );

  if (loading) {
    return (
      <div className={styles.rateCardContainer}>
        <BodyLarge>{title}</BodyLarge>
        <div className={styles.spinner}>
          <span>
            <Spinner purpose="body-text" />
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.rateCardContainer}>
      <BodyLarge>{title}</BodyLarge>
      {value !== null ? (
        <div className={styles.rateCardValue}>{currValueString}</div>
      ) : (
        noDataAvailableCard
      )}
      <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
        {value !== null && prevValue === null ? (
          <Box
            className={styles.rateCardDeltaRow}
            flex={{direction: 'row', alignItems: 'center', gap: 4}}
          >
            <Icon name="trending_up" color={Colors.textLight()} size={16} />
            <span className={styles.rateCardDelta}>
              <>New this period</>
            </span>
          </Box>
        ) : (
          prevValue !== null &&
          value !== null && (
            <>
              <div className={styles.rateCardPrev}>{prevValueString + ' last period'}</div>
              <Box
                className={styles.rateCardDeltaRow}
                flex={{direction: 'row', alignItems: 'center', gap: 4}}
              >
                <Icon
                  name={isDown ? 'trending_down' : 'trending_up'}
                  color={Colors.textLight()}
                  size={16}
                />
                <span className={styles.rateCardDelta}>
                  <>{absDeltaString}</>
                </span>
              </Box>
            </>
          )
        )}
      </Box>
    </div>
  );
}
