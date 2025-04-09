import {
  Body,
  Box,
  Colors,
  Container,
  Icon,
  IconWrapper,
  Inner,
  Row,
  Skeleton,
  Subtitle1,
  SubtitleSmall,
  ifPlural,
  useDelayedState,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import updateLocale from 'dayjs/plugin/updateLocale';
import React, {useEffect, useMemo, useRef, useState} from 'react';
import {Link, useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';
import {AssetGlobalLineageLink} from 'shared/assets/AssetPageHeader.oss';
import {ViewBreadcrumb} from 'shared/assets/ViewBreadcrumb.oss';
import styled from 'styled-components';

import {
  AssetHealthStatusString,
  AssetHealthSummary,
  STATUS_INFO,
  statusToIconAndColor,
} from './AssetHealthSummary';
import {useAllAssets} from './AssetsCatalogTable';
import {AssetsEmptyState} from './AssetsEmptyState';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {asAssetKeyInput} from './asInput';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {currentPageAtom} from '../app/analytics';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {useRecentAssetEvents} from './useRecentAssetEvents';
import {useAssetsHealthData} from '../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../asset-data/types/AssetHealthDataProvider.types';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {useAssetSelectionInput} from '../asset-selection/input/useAssetSelectionInput';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {SyntaxError} from '../selection/CustomErrorListener';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';
import {numberFormatter} from '../ui/formatters';

dayjs.extend(relativeTime);
dayjs.extend(updateLocale);

const emptyArray: any[] = [];
export const AssetsCatalogTableV2 = () => {
  const setCurrentPage = useSetRecoilState(currentPageAtom);
  const {path} = useRouteMatch();
  useEffect(() => {
    setCurrentPage(({specificPath}) => ({specificPath, path: `${path}?view=AssetCatalogTableV2`}));
  }, [path, setCurrentPage]);

  return (
    <>
      <Box
        padding={{top: 12, horizontal: 24}}
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        border="top"
      >
        <ViewBreadcrumb full />
        <AssetGlobalLineageLink />
      </Box>
      <AssetsCatalogTableV2Impl />
    </>
  );
};

const AssetsCatalogTableV2Impl = () => {
  const {assets, loading: assetsLoading, error} = useAllAssets();
  useBlockTraceUntilTrue('useAllAssets', !!assets?.length && !assetsLoading);

  const [errorState, setErrorState] = useState<SyntaxError[]>([]);
  const {filterInput, filtered, loading} = useAssetSelectionInput({
    assets: assets ?? emptyArray,
    assetsLoading: !assets && assetsLoading,
    onErrorStateChange: (errors) => {
      if (errors !== errorState) {
        setErrorState(errors);
      }
    },
  });

  const scope = useMemo(
    () => ({
      all: (filtered ?? [])
        .filter((a): a is AssetWithDefinition => !!a.definition)
        .map((a) => ({...a.definition, assetKey: a.key})),
    }),
    [filtered],
  );

  const {liveDataByNode} = useAssetsHealthData(
    useMemo(() => filtered.map((asset) => asAssetKeyInput(asset.key)), [filtered]),
  );

  const healthDataLoading = useMemo(() => {
    return Object.values(liveDataByNode).length !== filtered.length;
  }, [liveDataByNode, filtered]);

  const groupedByStatus = useMemo(() => {
    const byStatus: Record<AssetHealthStatusString, (typeof liveDataByNode)[string][]> = {
      Degraded: [],
      Warning: [],
      Healthy: [],
      Unknown: [],
    };
    Object.values(liveDataByNode).forEach((asset) => {
      const status = statusToIconAndColor[asset.assetHealth?.assetHealth ?? 'undefined'].text;
      byStatus[status].push(asset);
    });
    return byStatus;
  }, [liveDataByNode]);

  if (error) {
    return <PythonErrorInfo error={error} />;
  }

  if (!assets?.length && !loading) {
    return (
      <Box padding={{vertical: 64}}>
        <AssetsEmptyState />
      </Box>
    );
  }

  return (
    <>
      <Box padding={{vertical: 12, horizontal: 24}}>{filterInput}</Box>
      <IndeterminateLoadingBar $loading={loading || healthDataLoading} />
      <Box
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        padding={{horizontal: 24, vertical: 12}}
        border="bottom"
      >
        <Subtitle1>
          {loading ? (
            <Skeleton $width={200} $height={21} />
          ) : (
            <>
              {numberFormatter.format(filtered.length)} asset{ifPlural(filtered.length, '', 's')}
            </>
          )}
        </Subtitle1>
        {loading ? (
          <Skeleton $width={300} $height={21} />
        ) : (
          <LaunchAssetExecutionButton primary={false} scope={scope} />
        )}
      </Box>
      <Table groupedByStatus={groupedByStatus} loading={loading} />
    </>
  );
};

const shimmer = {shimmer: true};
const shimmerRows = [shimmer, shimmer, shimmer, shimmer, shimmer];

const Table = ({
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
    estimateSize: () => 32,
    overscan: 5,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <Container ref={containerRef}>
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const item = rowItems[index]!;

          const wrapper = (content: React.ReactNode) => (
            <Row key={key} $height={size} $start={start}>
              <div data-index={index} ref={rowVirtualizer.measureElement}>
                <Box border="bottom" padding={{horizontal: 24, vertical: 12}}>
                  {content}
                </Box>
              </div>
            </Row>
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
};

const StatusHeader = ({
  status,
  open,
  onToggle,
}: {
  status: AssetHealthStatusString;
  open: boolean;
  onToggle: () => void;
}) => {
  const {iconName, iconColor, textColor, text} = STATUS_INFO[status];
  return (
    <StatusHeaderContainer
      flex={{direction: 'row', alignItems: 'center', gap: 4}}
      onClick={onToggle}
    >
      <Icon name={iconName} color={iconColor} />
      <SubtitleSmall color={textColor}>{text}</SubtitleSmall>
      <Icon
        name="arrow_drop_down"
        style={{transform: open ? 'rotate(0deg)' : 'rotate(-90deg)'}}
        color={Colors.textLight()}
      />
    </StatusHeaderContainer>
  );
};

const StatusHeaderContainer = styled(Box)`
  background-color: ${Colors.backgroundLight()};
  &:hover {
    background-color: ${Colors.backgroundLightHover()};
  }
  border-radius: 4px;
  padding: 6px 24px;
`;

const AssetRow = ({asset}: {asset: AssetHealthFragment}) => {
  const linkUrl = assetDetailsPathForKey({path: asset.assetKey.path});

  return (
    <RowWrapper to={linkUrl}>
      <Box flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}>
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <AssetIconWrapper>
            <Icon name="asset" />
          </AssetIconWrapper>
          {asset.assetKey.path.join(' / ')}
        </Box>
        <AssetRecentUpdatesTrend asset={asset} />
      </Box>
    </RowWrapper>
  );
};

const AssetRecentUpdatesTrend = ({asset}: {asset: AssetHealthFragment}) => {
  const {assetsByAssetKey} = useAllAssets();
  const assetDefinition = assetsByAssetKey[tokenForAssetKey(asset.assetKey)]?.definition;
  // Wait 100ms to avoid querying during fast scrolling of the table
  const shouldQuery = useDelayedState(100);
  const {materializations, observations, loading} = useRecentAssetEvents(
    shouldQuery ? asset.assetKey : undefined,
    {limit: 5},
    {assetHasDefinedPartitions: !!assetDefinition?.partitionDefinition},
  );

  const states = useMemo(() => {
    return new Array(5)
      .fill(null)
      .map((_, index) => {
        const materialization = materializations[index] ?? observations[index];
        if (!materialization) {
          return <Pill key={index} $index={index} $color={Colors.backgroundDisabled()} />;
        }
        if (materialization.__typename === 'FailedToMaterializeEvent') {
          return <Pill key={index} $index={index} $color={Colors.accentRed()} />;
        }
        return <Pill key={index} $index={index} $color={Colors.accentGreen()} />;
      })
      .reverse();
  }, [materializations, observations]);

  const lastEvent = materializations[0] ?? observations[0];

  const timeAgo = useMemo(() => {
    if (!lastEvent) {
      return ' - ';
    }
    return dayjs(Number(lastEvent.timestamp)).fromNow();
  }, [lastEvent]);

  return (
    <Box flex={{direction: 'row', gap: 6, alignItems: 'center'}}>
      {loading && !lastEvent ? (
        <Skeleton $width={100} $height={21} />
      ) : (
        <>
          <Body color={Colors.textLight()}>{timeAgo}</Body>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>{states}</Box>
          <div style={{height: 13, width: 1, background: Colors.keylineDefault()}} />
        </>
      )}
      <AssetHealthSummary assetKey={asset.assetKey} iconOnly />
    </Box>
  );
};

type AssetWithDefinition = AssetTableFragment & {
  definition: NonNullable<AssetTableFragment['definition']>;
};

const Pill = styled.div<{$index: number; $color: string}>`
  border-radius: 2px;
  height: 12px;
  width: 4px;
  background: ${({$color}) => $color};
  opacity: ${({$index}) => OPACITIES[$index] ?? 1};
`;

const OPACITIES: Record<number, number> = {
  4: 1,
  3: 0.8,
  2: 0.66,
  1: 0.4,
  0: 0.2,
};

const AssetIconWrapper = styled.div``;

const RowWrapper = styled(Link)`
  color: ${Colors.textLight()};
  cursor: pointer;
  :hover {
    &,
    ${AssetIconWrapper} ${IconWrapper} {
      color: ${Colors.textDefault()};
      text-decoration: none;
    }
    ${AssetIconWrapper} ${IconWrapper} {
      background: ${Colors.textDefault()};
      text-decoration: none;
    }
  }
`;
