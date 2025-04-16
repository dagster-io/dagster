import {
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
  Tab,
  Tabs,
  ifPlural,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import updateLocale from 'dayjs/plugin/updateLocale';
import React, {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {Link, useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';
import {CreateCatalogViewButton} from 'shared/assets/CreateCatalogViewButton.oss';
import styled from 'styled-components';

import {AssetCatalogAssetGraph} from './AssetCatalogAssetGraph';
import {AssetHealthStatusString, STATUS_INFO, statusToIconAndColor} from './AssetHealthSummary';
import {AssetRecentUpdatesTrend} from './AssetRecentUpdatesTrend';
import {useAllAssets} from './AssetsCatalogTable';
import {AssetsEmptyState} from './AssetsEmptyState';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {asAssetKeyInput} from './asInput';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {currentPageAtom} from '../app/analytics';
import {useAssetsHealthData} from '../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../asset-data/types/AssetHealthDataProvider.types';
import {useAssetSelectionInput} from '../asset-selection/input/useAssetSelectionInput';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {SyntaxError} from '../selection/CustomErrorListener';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';
import {numberFormatter} from '../ui/formatters';
const emptyArray: any[] = [];

dayjs.extend(relativeTime);
dayjs.extend(updateLocale);

export const AssetsCatalogTableV2Impl = React.memo(
  ({isFullScreen, toggleFullScreen}: {isFullScreen: boolean; toggleFullScreen: () => void}) => {
    const {assets, loading: assetsLoading, error} = useAllAssets();
    useBlockTraceUntilTrue('useAllAssets', !!assets?.length && !assetsLoading);

    const [errorState, setErrorState] = useState<SyntaxError[]>([]);
    const {filterInput, filtered, loading, setAssetSelection, assetSelection} =
      useAssetSelectionInput<AssetTableFragment>({
        assets: assets ?? emptyArray,
        assetsLoading: !assets && assetsLoading,
        onErrorStateChange: useCallback(
          (errors: SyntaxError[]) => {
            if (errors !== errorState) {
              setErrorState(errors);
            }
          },
          [errorState],
        ),
      });

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

    const [selectedTab, setSelectedTab] = useQueryPersistedState<string | undefined>({
      queryKey: 'selectedTab',
      decode: (qs) =>
        qs.selectedTab && typeof qs.selectedTab === 'string' ? qs.selectedTab : undefined,
      encode: (b) => ({selectedTab: b || undefined}),
    });

    const setCurrentPage = useSetRecoilState(currentPageAtom);
    const {path} = useRouteMatch();
    useEffect(() => {
      setCurrentPage(({specificPath}) => ({
        specificPath,
        path: `${path}?view=AssetCatalogTableV2&selected_tab=${selectedTab}`,
      }));
    }, [path, setCurrentPage, selectedTab]);

    const content = useMemo(() => {
      switch (selectedTab) {
        case 'lineage':
          return (
            <AssetCatalogAssetGraph
              selection={assetSelection}
              onChangeSelection={setAssetSelection}
              isFullScreen={isFullScreen}
              toggleFullScreen={toggleFullScreen}
            />
          );
        case 'insights':
          return <div>Insights</div>;
        default:
          return <Table assets={filtered} groupedByStatus={groupedByStatus} loading={loading} />;
      }
    }, [
      selectedTab,
      filtered,
      groupedByStatus,
      loading,
      assetSelection,
      setAssetSelection,
      isFullScreen,
      toggleFullScreen,
    ]);

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

    const extraStyles =
      selectedTab === 'lineage'
        ? {
            gridTemplateColumns: 'minmax(500px, 1fr)',
            display: 'grid',
            gridTemplateRows: 'repeat(2, auto) minmax(0, 1fr)',
          }
        : {};
    return (
      <Box flex={{direction: 'column'}} style={{height: '100%', minHeight: 600, ...extraStyles}}>
        <Box
          flex={{direction: 'row', alignItems: 'center', gap: 8}}
          padding={{vertical: 12, horizontal: 24}}
          border="bottom"
        >
          <Box flex={{grow: 1, shrink: 1}}>{filterInput}</Box>
          <CreateCatalogViewButton />
        </Box>
        {selectedTab === 'catalog' ? (
          <IndeterminateLoadingBar $loading={loading || healthDataLoading} />
        ) : null}
        <Box border="bottom">
          {isFullScreen ? null : (
            <Tabs
              onChange={setSelectedTab}
              selectedTabId={selectedTab}
              style={{marginLeft: 24, marginRight: 24}}
            >
              <Tab id="catalog" title="Catalog" />
              <Tab id="lineage" title="Lineage" />
              <Tab id="insights" title="Insights" />
            </Tabs>
          )}
        </Box>
        {content}
      </Box>
    );
  },
);

const Table = React.memo(
  ({
    assets,
    groupedByStatus,
    loading,
  }: {
    assets: AssetTableFragment[] | undefined;
    groupedByStatus: Record<AssetHealthStatusString, AssetHealthFragment[]>;
    loading: boolean;
  }) => {
    const scope = useMemo(
      () => ({
        all: (assets ?? [])
          .filter((a): a is AssetWithDefinition => !!a.definition)
          .map((a) => ({...a.definition, assetKey: a.key})),
      }),
      [assets],
    );

    return (
      <div
        style={{
          display: 'grid',
          gridTemplateRows: 'minmax(0, 1fr)',
          height: '100%',
        }}
      >
        <div
        // style={{
        //   display: 'grid',
        //   gridTemplateColumns: 'minmax(0, 1fr) 374px',
        //   height: '100%',
        // }}
        >
          <div
            style={{
              display: 'grid',
              gridTemplateRows: 'auto minmax(500px, 1fr)',
              height: '100%',
              gridTemplateColumns: 'minmax(500px, 1fr)',
            }}
          >
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
                    {numberFormatter.format(assets?.length ?? 0)} asset
                    {ifPlural(assets?.length ?? 0, '', 's')}
                  </>
                )}
              </Subtitle1>
              {loading ? (
                <Skeleton $width={300} $height={21} />
              ) : (
                <LaunchAssetExecutionButton primary={false} scope={scope} />
              )}
            </Box>
            <VirtualizedTable groupedByStatus={groupedByStatus} loading={loading} />
          </div>
          {/* <Box border="left" padding={{vertical: 24, horizontal: 12}}>
            Sidebar
          </Box> */}
        </div>
      </div>
    );
  },
);

const shimmer = {shimmer: true};
const shimmerRows = [shimmer, shimmer, shimmer, shimmer, shimmer];

const VirtualizedTable = React.memo(
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
      estimateSize: () => 32,
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

  return (
    <RowWrapper to={linkUrl}>
      <Box flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}>
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <AssetIconWrapper>
            <Icon name="asset" />
          </AssetIconWrapper>
          {asset.assetKey.path.join(' / ')}
        </Box>
        {/* Prevent clicks on the trend from propoagating to the row and triggering the link */}
        <div
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
          }}
          className="test"
        >
          <AssetRecentUpdatesTrend asset={asset} />
        </div>
      </Box>
    </RowWrapper>
  );
});

type AssetWithDefinition = AssetTableFragment & {
  definition: NonNullable<AssetTableFragment['definition']>;
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
