import {
  Box,
  Colors,
  Container,
  Icon,
  IconWrapper,
  Inner,
  Row,
  Skeleton,
  SubtitleSmall,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useMemo, useRef, useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {AssetActionMenu} from './AssetActionMenu';
import {AssetHealthStatusString, STATUS_INFO} from './AssetHealthSummary';
import {AssetRecentUpdatesTrend} from './AssetRecentUpdatesTrend';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {useAssetDefinition} from './useAssetDefinition';
import {AssetHealthFragment} from '../asset-data/types/AssetHealthDataProvider.types';
import {numberFormatter} from '../ui/formatters';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

const shimmer = {shimmer: true};
const shimmerRows = [shimmer, shimmer, shimmer, shimmer, shimmer];

export const AssetCatalogV2VirtualizedTable = React.memo(
  ({
    groupedByStatus,
    loading,
  }: {
    groupedByStatus: Record<AssetHealthStatusString, AssetHealthFragment[]>;
    loading: boolean;
  }) => {
    const containerRef = useRef<HTMLDivElement>(null);

    const [openStatuses, setOpenStatuses] = useState<Set<AssetHealthStatusString>>(
      new Set(['Unknown', 'Healthy', 'Warning', 'Degraded']),
    );

    const unGroupedRowItems = useMemo(() => {
      return Object.keys(groupedByStatus).flatMap((status_: string) => {
        const status = status_ as AssetHealthStatusString;
        if (!groupedByStatus[status].length) {
          return [];
        }
        if (openStatuses.has(status)) {
          return [{header: true, status}, ...groupedByStatus[status]];
        }
        return [{header: true, status}];
      });
    }, [groupedByStatus, openStatuses]);

    const rowItems = loading ? shimmerRows : unGroupedRowItems;

    const rowVirtualizer = useVirtualizer({
      count: rowItems.length,
      getScrollElement: () => containerRef.current,
      estimateSize: () => 44,
      overscan: 5,
    });

    const totalHeight = rowVirtualizer.getTotalSize();
    const items = rowVirtualizer.getVirtualItems();

    return (
      <Container ref={containerRef} style={{overflow: 'scroll'}}>
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            const item = rowItems[index]!;

            const wrapper = (content: React.ReactNode) => (
              <RowWrapper key={key}>
                <Row $height={size} $start={start}>
                  <div data-index={index} ref={rowVirtualizer.measureElement}>
                    <Box border="bottom" padding={{horizontal: 24, vertical: 12}}>
                      {content}
                    </Box>
                  </div>
                </Row>
              </RowWrapper>
            );

            if ('shimmer' in item) {
              return wrapper(<Skeleton key={key} $height={21} $width="45%" />);
            }
            if ('header' in item) {
              return (
                <Row key={key} $height={size} $start={start}>
                  <div data-index={index} ref={rowVirtualizer.measureElement}>
                    <StatusHeader
                      status={item.status}
                      open={openStatuses.has(item.status)}
                      count={groupedByStatus[item.status].length}
                      onToggle={() =>
                        setOpenStatuses((prev) => {
                          const newSet = new Set(prev);
                          if (newSet.has(item.status)) {
                            newSet.delete(item.status);
                          } else {
                            newSet.add(item.status);
                          }
                          return newSet;
                        })
                      }
                    />
                  </div>
                </Row>
              );
            }
            return wrapper(<AssetRow asset={item} />);
          })}
        </Inner>
      </Container>
    );
  },
);

const StatusHeader = React.memo(
  ({
    status,
    open,
    count,
    onToggle,
  }: {
    status: AssetHealthStatusString;
    open: boolean;
    count: number;
    onToggle: () => void;
  }) => {
    const {iconName, iconColor, text} = STATUS_INFO[status];
    return (
      <StatusHeaderContainer
        flex={{direction: 'row', alignItems: 'center', gap: 4}}
        onClick={onToggle}
      >
        <Icon name={iconName} color={iconColor} />
        <SubtitleSmall>
          {text} ({numberFormatter.format(count)})
        </SubtitleSmall>
        <Icon
          name="arrow_drop_down"
          style={{transform: open ? 'rotate(0deg)' : 'rotate(-90deg)'}}
          color={Colors.textLight()}
        />
      </StatusHeaderContainer>
    );
  },
);

const StatusHeaderContainer = styled(Box)`
  background-color: ${Colors.backgroundLight()};
  &:hover {
    background-color: ${Colors.backgroundLightHover()};
  }
  border-radius: 4px;
  padding: 6px 24px;
`;

const AssetRow = React.memo(({asset}: {asset: AssetHealthFragment}) => {
  const linkUrl = assetDetailsPathForKey({path: asset.assetKey.path});

  const {definition: _definition, refresh, cachedDefinition} = useAssetDefinition(asset.assetKey);
  const definition = cachedDefinition || _definition;

  const repoAddress = definition?.repository
    ? buildRepoAddress(definition.repository.name, definition.repository.location.name)
    : null;

  return (
    <Link to={linkUrl}>
      <Box flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}>
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <AssetIconWrapper>
            <Icon name="asset" />
          </AssetIconWrapper>
          {asset.assetKey.path.join(' / ')}
        </Box>
        {/* Prevent clicks on the trend from propoagating to the row and triggering the link */}
        <Box
          flex={{direction: 'row', alignItems: 'center', gap: 4}}
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
          }}
          style={{marginTop: -6, marginBottom: -6}}
        >
          <AssetRecentUpdatesTrend asset={asset} />
          <AssetActionMenu
            unstyledButton
            path={asset.assetKey.path}
            definition={definition}
            repoAddress={repoAddress}
            onRefresh={refresh}
          />
        </Box>
      </Box>
    </Link>
  );
});

const AssetIconWrapper = styled.div``;

const RowWrapper = styled.div`
  a {
    color: ${Colors.textLight()};
    cursor: pointer;
    transition: color 0.3s ease-in-out;
  }
  background: ${Colors.backgroundDefault()};
  &:hover {
    background: ${Colors.backgroundDefaultHover()};
    a,
    ${AssetIconWrapper} ${IconWrapper} {
      color: ${Colors.textDefault()};
      text-decoration: none;
    }
    ${AssetIconWrapper} ${IconWrapper} {
      background: ${Colors.textDefault()};
      text-decoration: none;
    }
  }
  transition: background 0.3s ease-in-out;
`;
