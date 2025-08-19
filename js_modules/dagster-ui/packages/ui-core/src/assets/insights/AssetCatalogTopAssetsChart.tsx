import {
  BodyLarge,
  Box,
  Button,
  Icon,
  Menu,
  MenuItem,
  Popover,
  Spinner,
} from '@dagster-io/ui-components';
import {memo, useMemo, useState} from 'react';

import styles from './AssetCatalogTopAssetsChart.module.css';
import {AssetCatalogTopAssetsList} from './AssetCatalogTopAssetsList';
import {ReportingUnitType} from '../../insights/types';

interface Props {
  header: string;
  datasets: {labels: string[]; data: number[]};
  unitLabel: string;
  loading: boolean;
  unitType: ReportingUnitType;
}

export const AssetCatalogTopAssetsChart = memo(
  ({header, datasets, unitType, unitLabel, loading}: Props) => {
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

    const {data, labels} = datasets;

    const values = useMemo(() => {
      return labels
        .map((label, i) => ({
          label,
          value: data[i] ?? 0,
        }))
        .filter(({value}) => value !== 0)
        .sort((a, b) => (sortDirection === 'asc' ? a.value - b.value : b.value - a.value));
    }, [data, labels, sortDirection]);

    return (
      <div className={styles.container}>
        <Box
          flex={{direction: 'row', gap: 12, justifyContent: 'space-between', alignItems: 'center'}}
          padding={{bottom: 12, horizontal: 12}}
        >
          <BodyLarge>{header}</BodyLarge>
          {loading ? (
            <Spinner purpose="body-text" />
          ) : (
            <Popover
              placement="bottom-end"
              content={
                <Menu>
                  <MenuItem
                    text="Low to high"
                    icon="sort_asc"
                    onClick={() => setSortDirection('asc')}
                    active={sortDirection === 'asc'}
                  />
                  <MenuItem
                    text="High to low"
                    icon="sort_desc"
                    onClick={() => setSortDirection('desc')}
                    active={sortDirection === 'desc'}
                  />
                </Menu>
              }
            >
              <Button
                icon={<Icon name={sortDirection === 'asc' ? 'sort_asc' : 'sort_desc'} />}
                rightIcon={<Icon name="expand_more" />}
              >
                {sortDirection === 'asc' ? 'Low to high' : 'High to low'}
              </Button>
            </Popover>
          )}
        </Box>
        {values.length ? (
          <AssetCatalogTopAssetsList
            values={values}
            unitType={unitType}
            unitLabel={unitLabel}
            key={sortDirection} // Reset to first page when sort changes
          />
        ) : loading ? null : (
          <div className={styles.emptyState}>
            No reported events for this metric in this time range.
          </div>
        )}
      </div>
    );
  },
);

AssetCatalogTopAssetsChart.displayName = 'AssetCatalogTopAssetsChart';
