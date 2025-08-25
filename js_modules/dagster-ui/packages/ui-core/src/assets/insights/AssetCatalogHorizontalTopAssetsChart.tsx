import {
  Box,
  Colors,
  Container,
  Icon,
  Inner,
  ListItem,
  MiddleTruncate,
  Mono,
  Row,
  UnstyledButton,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import clsx from 'clsx';
import React, {useMemo, useRef, useState} from 'react';
import {Link} from 'react-router-dom';

import styles from './AssetCatalogHorizontalTopAssetsChart.module.css';
import {COMMON_COLLATOR} from '../../app/commonCollator';
import {tokenToAssetKey} from '../../asset-graph/Utils';
import {formatMetric} from '../../insights/formatMetric';
import {ReportingUnitType} from '../../insights/types';
import {numberFormatter} from '../../ui/formatters';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';

type SortBy = 'name' | 'current' | 'previous' | 'change';
type SortDir = 'asc' | 'desc';

const getInitialSortBy = (currentData: MaybeData, previousData: MaybeData) => {
  if (currentData && previousData) {
    return 'change';
  }
  if (currentData) {
    return 'current';
  }
  if (previousData) {
    return 'previous';
  }
  return 'name';
};

const calculateChange = (current: number, previous: number) => {
  if (previous === 0) {
    return current === 0 ? 0 : 1;
  }
  return (current - previous) / previous;
};

const getChangeColor = (change: number) => {
  if (change === 0) {
    return Colors.textLight();
  }
  return change > 0 ? Colors.textGreen() : Colors.textRed();
};

type MaybeData = null | {labels: string[]; data: number[]};

interface Props {
  currentData: MaybeData;
  previousData: MaybeData;
  unitType: ReportingUnitType;
}

export const AssetCatalogHorizontalTopAssetsChart = React.memo(
  ({currentData, previousData, unitType}: Props) => {
    const [sortBy, setSortBy] = useState<{by: SortBy; dir: SortDir}>(() => ({
      by: getInitialSortBy(currentData, previousData),
      dir: 'desc',
    }));

    const containerRef = useRef<HTMLDivElement>(null);

    const valueMap = useMemo(() => {
      const currentMap = currentData
        ? Object.fromEntries(
            currentData.labels.map((label, ii) => [label, currentData.data[ii] ?? 0]),
          )
        : null;
      const previousMap = previousData
        ? Object.fromEntries(
            previousData.labels.map((label, ii) => [label, previousData.data[ii] ?? 0]),
          )
        : null;
      return {
        current: currentMap,
        previous: previousMap,
      };
    }, [currentData, previousData]);

    const count = useMemo(() => {
      const set = new Set([
        ...(valueMap?.current ? Object.keys(valueMap.current) : []),
        ...(valueMap?.previous ? Object.keys(valueMap.previous) : []),
      ]);
      return set.size;
    }, [valueMap]);

    const sorted = useMemo(() => {
      const currentKeys = valueMap.current ? Object.keys(valueMap.current) : [];
      const previousKeys = valueMap.previous ? Object.keys(valueMap.previous) : [];
      const allKeys = Array.from(new Set([...currentKeys, ...previousKeys]));
      return allKeys.sort((a, b) => {
        if (sortBy.by === 'name') {
          return sortBy.dir === 'desc'
            ? COMMON_COLLATOR.compare(b, a)
            : COMMON_COLLATOR.compare(a, b);
        }

        const currentA = valueMap.current?.[a] ?? 0;
        const currentB = valueMap.current?.[b] ?? 0;
        const previousA = valueMap.previous?.[a] ?? 0;
        const previousB = valueMap.previous?.[b] ?? 0;
        switch (sortBy.by) {
          case 'current':
            return sortBy.dir === 'desc' ? currentB - currentA : currentA - currentB;
          case 'previous':
            return sortBy.dir === 'desc' ? previousB - previousA : previousA - previousB;
          case 'change': {
            const changeA = calculateChange(currentA, previousA);
            const changeB = calculateChange(currentB, previousB);
            return sortBy.dir === 'desc' ? changeB - changeA : changeA - changeB;
          }
        }
      });
    }, [valueMap, sortBy]);

    const onSort = (by: SortBy) => {
      setSortBy((current) => {
        if (current.by === by) {
          return {by, dir: current.dir === 'asc' ? 'desc' : 'asc'};
        }
        return {by, dir: by === 'name' ? 'asc' : 'desc'};
      });
      containerRef.current?.scrollTo({top: 0});
    };

    const rowVirtualizer = useVirtualizer({
      count,
      getScrollElement: () => containerRef.current,
      estimateSize: () => 42,
      overscan: 20,
    });

    const items = rowVirtualizer.getVirtualItems();
    const totalHeight = rowVirtualizer.getTotalSize();
    const icon = sortBy.dir === 'asc' ? 'expand_less' : 'expand_more';

    return (
      <div className={styles.container}>
        <Box style={{color: Colors.textLighter()}} border="bottom" padding={{top: 8}}>
          <div
            className={clsx(
              styles.headerGrid,
              currentData ? styles.hasCurrentData : null,
              previousData ? styles.hasPreviousData : null,
              currentData && previousData ? styles.change : null,
            )}
          >
            <UnstyledButton
              onClick={() => onSort('name')}
              className={clsx(styles.sortButton, sortBy.by === 'name' && styles.active)}
            >
              <span>Asset</span>
              <Icon name={sortBy.by === 'name' ? icon : 'expand'} />
            </UnstyledButton>
            {currentData ? (
              <UnstyledButton
                onClick={() => onSort('current')}
                className={clsx(styles.sortButton, sortBy.by === 'current' && styles.active)}
              >
                <span>This period</span>
                <Icon name={sortBy.by === 'current' ? icon : 'expand'} />
              </UnstyledButton>
            ) : null}
            {previousData ? (
              <UnstyledButton
                onClick={() => onSort('previous')}
                className={clsx(styles.sortButton, sortBy.by === 'previous' && styles.active)}
              >
                <span>Prev period</span>
                <Icon name={sortBy.by === 'previous' ? icon : 'expand'} />
              </UnstyledButton>
            ) : null}
            {currentData && previousData ? (
              <UnstyledButton
                onClick={() => onSort('change')}
                className={clsx(styles.sortButton, sortBy.by === 'change' && styles.active)}
              >
                <span>Change</span>
                <Icon name={sortBy.by === 'change' ? icon : 'expand'} />
              </UnstyledButton>
            ) : null}
          </div>
        </Box>
        <div className={styles.listContainer}>
          <Container ref={containerRef}>
            <Inner $totalHeight={totalHeight}>
              {items.map(({index, key, size, start}) => {
                const itemLabel = sorted[index];
                if (!itemLabel) {
                  return null;
                }

                const current = valueMap.current?.[itemLabel] ?? 0;
                const previous = valueMap.previous?.[itemLabel] ?? 0;

                const assetKey = tokenToAssetKey(itemLabel.split(' / ').join('/'));
                const change = calculateChange(current, previous);

                const currentFormatted =
                  unitType === ReportingUnitType.TIME_MS
                    ? formatMetric(current, unitType)
                    : numberFormatter.format(current);
                const previousFormatted =
                  unitType === ReportingUnitType.TIME_MS
                    ? formatMetric(previous, unitType)
                    : numberFormatter.format(previous);

                return (
                  <Row key={key} $start={start} $height={size}>
                    <ListItem
                      key={itemLabel}
                      ref={rowVirtualizer.measureElement}
                      index={index}
                      left={<MiddleTruncate text={itemLabel} />}
                      right={
                        <div
                          className={clsx(
                            styles.rightGrid,
                            currentData ? styles.hasCurrentData : null,
                            previousData ? styles.hasPreviousData : null,
                            currentData && previousData ? styles.change : null,
                          )}
                        >
                          {currentData ? (
                            <Mono color={Colors.textDefault()} className={styles.tableValue}>
                              {currentFormatted}
                            </Mono>
                          ) : null}
                          {previousData ? (
                            <Mono color={Colors.textDefault()} className={styles.tableValue}>
                              {previousFormatted}
                            </Mono>
                          ) : null}
                          {currentData && previousData ? (
                            <Mono className={styles.tableValue} color={getChangeColor(change)}>
                              {change === 0 ? (
                                <>0.0% </>
                              ) : (
                                `${change > 0 ? '+' : ''}${(change * 100).toFixed(1)}%`
                              )}
                            </Mono>
                          ) : null}
                        </div>
                      }
                      href={assetDetailsPathForKey(assetKey)}
                      renderLink={({href, ...rest}) => <Link to={href ?? '#'} {...rest} />}
                    />
                  </Row>
                );
              })}
            </Inner>
          </Container>
        </div>
      </div>
    );
  },
);
