import {
  Body,
  Box,
  Colors,
  Container,
  Icon,
  Inner,
  Row,
  Skeleton,
  Subtitle1,
  ifPlural,
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

import {AssetHealthSummary} from './AssetHealthSummary';
import {useAllAssets} from './AssetsCatalogTable';
import {AssetsEmptyState} from './AssetsEmptyState';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {currentPageAtom} from '../app/analytics';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {useRecentAssetEvents} from './useRecentAssetEvents';
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
  const {filterInput, filtered, loading, assetSelection, setAssetSelection} =
    useAssetSelectionInput({
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
      all: (assets ?? [])
        .filter((a): a is AssetWithDefinition => !!a.definition)
        .map((a) => ({...a.definition, assetKey: a.key})),
    }),
    [assets],
  );

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
      <IndeterminateLoadingBar $loading={loading} />
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
      <Table
        assets={filtered}
        assetSelection={assetSelection}
        setAssetSelection={setAssetSelection}
        loading={loading}
      />
    </>
  );
};

const shimmer = {shimmer: true};
const shimmerRows = [shimmer, shimmer, shimmer, shimmer, shimmer];

const Table = ({
  assets,
  loading,
}: {
  assets: AssetTableFragment[];
  assetSelection: string;
  setAssetSelection: (selection: string) => void;
  loading: boolean;
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  const rowItems = loading ? shimmerRows : assets;

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
          return wrapper(<AssetRow asset={item} />);
        })}
      </Inner>
    </Container>
  );
};

const AssetRow = ({asset}: {asset: AssetTableFragment}) => {
  const linkUrl = assetDetailsPathForKey({path: asset.key.path});

  return (
    <Box flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}>
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="asset" />
        <Link to={linkUrl}>{asset.key.path.join(' / ')}</Link>
      </Box>
      <AssetRecentUpdatesTrend asset={asset} />
    </Box>
  );
};

const AssetRecentUpdatesTrend = ({asset}: {asset: AssetTableFragment}) => {
  const {materializations, observations, loading} = useRecentAssetEvents(
    asset.key,
    {limit: 5},
    {assetHasDefinedPartitions: !!asset.definition?.partitionDefinition},
  );

  const states = useMemo(() => {
    return new Array(5).fill(null).map((_, index) => {
      const materialization = materializations[index] ?? observations[index];
      if (!materialization) {
        return <Pill key={index} $index={index} $color={Colors.backgroundDisabled()} />;
      }
      if (materialization.__typename === 'FailedToMaterializeEvent') {
        return <Pill key={index} $index={index} $color={Colors.accentRed()} />;
      }
      return <Pill key={index} $index={index} $color={Colors.accentGreen()} />;
    });
  }, [materializations, observations]);

  const lastEvent = materializations[0] ?? observations[0];

  const timeAgo = useMemo(() => {
    if (!lastEvent) {
      return ' - ';
    }
    return dayjs(Number(lastEvent.timestamp)).fromNow();
  }, [lastEvent]);

  if (loading) {
    return <Skeleton $width={100} $height={21} />;
  }

  return (
    <Box flex={{direction: 'row', gap: 6, alignItems: 'center'}}>
      <Body color={Colors.textLight()}>{timeAgo}</Body>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>{states}</Box>
      <div style={{height: 13, width: 1, background: Colors.keylineDefault()}} />
      <AssetHealthSummary assetKey={asset.key} iconOnly />
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
  0: 1,
  1: 0.8,
  2: 0.66,
  3: 0.4,
  4: 0.2,
};
