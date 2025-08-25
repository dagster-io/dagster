import {BodyLarge, Box, Colors, Icon, Spinner} from '@dagster-io/ui-components';
import React from 'react';

import styles from './AssetCatalogRateCard.module.css';
import {formatDuration, unitToShortLabel} from '../../ui/formatDuration';
import {numberFormatterWithMaxFractionDigits, percentFormatter} from '../../ui/formatters';

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

  const currValueAndUnit = formatDuration(value, {unit})[0];
  const prevValueAndUnit = formatDuration(prevValue, {unit})[0];

  return {
    currValueString: `${numberFormatterWithMaxFractionDigits(2).format(currValueAndUnit.value)} ${unitToShortLabel[currValueAndUnit.unit]}`,
    prevValueString: `${numberFormatterWithMaxFractionDigits(2).format(prevValueAndUnit.value)} ${unitToShortLabel[prevValueAndUnit.unit]}`,
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
      <BodyLarge style={{marginBottom: 12}}>{title}</BodyLarge>
      <AssetCatalogRateStats value={value} prevValue={prevValue} unit={unit} />
    </div>
  );
}

export const AssetCatalogRateStats = ({
  value,
  prevValue,
  unit,
}: {
  value: number | null;
  prevValue: number | null;
  unit: 'percent' | 'seconds';
}) => {
  const {currValueString, prevValueString, absDeltaString, hasNegativeDelta} = formatValues(
    value,
    prevValue,
    unit,
  );

  const noDataAvailableCard = (
    <div className={styles.rateCardNoDataContainer}>No data available</div>
  );
  return (
    <>
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
            <span className={styles.rateCardDelta}>
              <>New this period</>
            </span>
          </Box>
        ) : (
          prevValue !== null &&
          value !== null && (
            <>
              <div className={styles.rateCardPrev}>{prevValueString + ' prev period'}</div>
              <Box
                className={styles.rateCardDeltaRow}
                flex={{direction: 'row', alignItems: 'center', gap: 4}}
              >
                <Icon
                  name={hasNegativeDelta ? 'trending_down' : 'trending_up'}
                  color={Colors.textLighter()}
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
    </>
  );
};
