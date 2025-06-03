import {BodyLarge, Box, Colors, Icon, Spinner} from '@dagster-io/ui-components';
import React from 'react';

import styles from './AssetCatalogRateCard.module.css';
import {percentFormatter} from '../../ui/formatters';

export interface AssetCatalogRateCardProps {
  title: string;
  value: number | null; // e.g., 0.981 for 98.1%
  prevValue: number | null; // e.g., 1 for 100%
  loading: boolean;
  unit: 'percent' | 'seconds';
}

function pctChange(x: number, y: number): number {
  if (x === 0) {
    if (y === 0) {
      return 0.0; // No change
    }
    return Number.POSITIVE_INFINITY;
  }

  if (y >= x) {
    return y / x - 1;
  }
  return -(1 - y / x);
}

const secondsFormatter = new Intl.NumberFormat(navigator.language, {
  style: 'unit',
  unit: 'second',
});

function formatValues(
  valueOrNull: number | null,
  prevValueOrNull: number | null,
  unit: 'percent' | 'seconds',
): {
  currValueString: string;
  prevValueString: string;
  absDeltaString: string;
  hasNegativeDelta: boolean;
} {
  const value = valueOrNull ?? 0;
  const prevValue = prevValueOrNull ?? 0;

  const delta = pctChange(prevValue, value);
  const hasNegativeDelta = delta < 0;
  const absDelta = Math.abs(delta);

  if (unit === 'percent') {
    return {
      currValueString: percentFormatter.format(value),
      prevValueString: percentFormatter.format(prevValue),
      absDeltaString: percentFormatter.format(absDelta),
      hasNegativeDelta,
    };
  }

  return {
    currValueString: secondsFormatter.format(value),
    prevValueString: secondsFormatter.format(prevValue),
    absDeltaString: percentFormatter.format(absDelta),
    hasNegativeDelta,
  };
}

export function AssetCatalogRateCard({
  title,
  value,
  prevValue,
  loading,
  unit,
}: AssetCatalogRateCardProps) {
  const {currValueString, prevValueString, absDeltaString, hasNegativeDelta} = formatValues(
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
                  name={hasNegativeDelta ? 'trending_down' : 'trending_up'}
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
