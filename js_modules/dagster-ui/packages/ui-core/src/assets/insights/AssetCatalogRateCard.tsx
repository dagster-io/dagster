import {BodyLarge, Box, Colors, Icon, Spinner} from '@dagster-io/ui-components';
import React from 'react';

import styles from './AssetCatalogRateCard.module.css';
import {numberFormatter} from '../../ui/formatters';

export interface AssetCatalogRateCardProps {
  title: string;
  value: number | null; // e.g., 0.981 for 98.1%
  prevValue: number | null; // e.g., 1 for 100%
  loading: boolean;
}

export function AssetCatalogRateCard({
  title,
  value,
  prevValue,
  loading,
}: AssetCatalogRateCardProps) {
  const pct = value ? Math.round(value * 1000) / 10 : 0;
  const prevPct = prevValue ? Math.round(prevValue * 1000) / 10 : 0;
  const delta = pct - prevPct;
  const isDown = delta < 0;
  const absDelta = Math.abs(delta);

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
        <div className={styles.rateCardValue}>{numberFormatter.format(pct) + '%'}</div>
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
              <div className={styles.rateCardPrev}>
                {numberFormatter.format(prevPct) + '% last period'}
              </div>
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
                  <>{numberFormatter.format(absDelta)}%</>
                </span>
              </Box>
            </>
          )
        )}
      </Box>
    </div>
  );
}
