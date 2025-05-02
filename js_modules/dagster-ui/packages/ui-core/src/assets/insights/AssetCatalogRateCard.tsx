import {BodyLarge, Box, Colors, Icon, Spinner} from '@dagster-io/ui-components';
import React from 'react';

import styles from './AssetCatalogRateCard.module.css';
import {numberFormatter} from '../../ui/formatters';

export interface AssetCatalogRateCardProps {
  title: string;
  value: number | null; // e.g., 0.981 for 98.1%
  prevValue: number | null; // e.g., 1 for 100%
}

export function AssetCatalogRateCard({title, value, prevValue}: AssetCatalogRateCardProps) {
  const pct = value ? Math.round(value * 1000) / 10 : 0;
  const prevPct = prevValue ? Math.round(prevValue * 1000) / 10 : 0;
  const delta = pct - prevPct;
  const isDown = delta < 0;
  const absDelta = Math.abs(delta);

  const loadingCurrentPeriod = !value;
  const loadingPrevPeriod = !prevValue;

  return (
    <div className={styles.rateCardContainer}>
      <BodyLarge>{title}</BodyLarge>
      <div className={styles.rateCardValue}>
        {loadingCurrentPeriod ? (
          <span>
            <Spinner purpose="body-text" />
          </span>
        ) : (
          numberFormatter.format(pct) + '%'
        )}
      </div>
      <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
        <div className={styles.rateCardPrev}>
          {loadingPrevPeriod ? (
            <Spinner purpose="body-text" />
          ) : (
            numberFormatter.format(prevPct) + '% last period'
          )}
        </div>
        <Box
          className={styles.rateCardDeltaRow}
          flex={{direction: 'row', alignItems: 'center', gap: 4}}
        >
          {loadingCurrentPeriod || loadingPrevPeriod ? null : (
            <Icon
              name={isDown ? 'trending_down' : 'trending_up'}
              color={Colors.textLight()}
              size={16}
            />
          )}
          <span className={styles.rateCardDelta}>
            {loadingCurrentPeriod || loadingPrevPeriod ? (
              <Spinner purpose="body-text" />
            ) : (
              <>{numberFormatter.format(absDelta)}%</>
            )}
          </span>
        </Box>
      </Box>
    </div>
  );
}
