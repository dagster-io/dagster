import {
  Body,
  BodySmall,
  Box,
  Button,
  Colors,
  Icon,
  MiddleTruncate,
  Mono,
  Spinner,
} from '@dagster-io/ui-components';
import React, {useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import styles from './AssetCatalogHorizontalTopAssetsChart.module.css';
import {tokenToAssetKey} from '../../asset-graph/Utils';
import {numberFormatter} from '../../ui/formatters';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';

const PAGE_SIZE = 10;

const DistributionChartRow = ({maxValue, value}: {maxValue: number; value: number}) => {
  const percentage = Math.round((value / maxValue) * 100);

  return (
    <Box flex={{direction: 'row'}}>
      <div className={styles.distributionRow} style={{width: `${percentage}%`}} />
    </Box>
  );
};

export const AssetCatalogHorizontalTopAssetsChart = React.memo(
  ({
    datasets,
    unitType,
    loading,
  }: {
    datasets: {labels: string[]; data: number[]};
    unitType: string;
    loading: boolean;
  }) => {
    const [page, setPage] = useState(0);

    const values = useMemo(() => {
      return datasets.labels
        .map((label, i) => ({
          label,
          value: datasets.data[i]!,
        }))
        .filter(({value}) => value !== 0)
        .sort((a, b) => b.value - a.value);
    }, [datasets.data, datasets.labels]);

    // Compute the max value from all values for consistent X axis scaling
    const maxValue = useMemo(() => {
      return values.length > 0 ? Math.max(...values.map(({value}) => value)) : undefined;
    }, [values]);

    const totalPages = Math.ceil(values.length / PAGE_SIZE);

    const currentPageValues = useMemo(
      () => values.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE),
      [page, values],
    );

    return (
      <div className={styles.container}>
        {loading ? <Spinner purpose="body-text" /> : null}
        <div>
          <Box style={{color: Colors.textLighter()}} border="bottom" padding={{vertical: 8}}>
            <div className={styles.table}>
              <BodySmall>Asset</BodySmall>
              <BodySmall style={{textAlign: 'right'}}>{unitType}</BodySmall>
              <BodySmall>Distribution</BodySmall>
            </div>
          </Box>
          <Box className={styles.table} margin={{vertical: 20}}>
            {currentPageValues.map(({label, value}, i) => (
              <React.Fragment key={i}>
                <Body as="div" color={Colors.textLight()}>
                  <Link to={assetDetailsPathForKey(tokenToAssetKey(label))}>
                    <MiddleTruncate text={label} />
                  </Link>
                </Body>
                <Mono color={Colors.textDefault()} className={styles.tableValue}>
                  {numberFormatter.format(Math.round(value))}
                </Mono>
                <DistributionChartRow maxValue={maxValue!} value={Math.round(value)} />
              </React.Fragment>
            ))}
          </Box>
        </div>
        {totalPages > 1 && (
          <Box
            flex={{
              alignItems: 'flex-end',
              grow: 1,
              direction: 'row',
            }}
          >
            <Box
              flex={{
                direction: 'row',
                grow: 1,
                alignItems: 'flex-end',
                justifyContent: 'stretch',
              }}
              border="top"
              padding={{top: 12, horizontal: 8}}
            >
              <Box
                flex={{
                  direction: 'row',
                  gap: 12,
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
                style={{width: '100%'}}
              >
                <BodySmall>
                  {page + 1} of {totalPages}
                </BodySmall>
                <Box flex={{direction: 'row', gap: 4}}>
                  <Button
                    outlined
                    onClick={() => setPage(page - 1)}
                    disabled={page === 0}
                    icon={<Icon name="arrow_back" />}
                  />
                  <Button
                    outlined
                    onClick={() => setPage(page + 1)}
                    disabled={page === totalPages - 1}
                    icon={<Icon name="arrow_forward" />}
                  />
                </Box>
              </Box>
            </Box>
          </Box>
        )}
      </div>
    );
  },
);
