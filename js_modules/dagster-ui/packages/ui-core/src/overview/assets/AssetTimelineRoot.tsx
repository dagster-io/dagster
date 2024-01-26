import {useQuery} from '@apollo/client';
import {Box, Colors, Spinner, TextInput, useViewport} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components';

import {AssetsTimelineDataFetcher, CodeLocationNodes} from './AssetTimelineDataFetcher';
import {AssetTimelineRow} from './AssetTimelineRow';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {groupIdForNode, toGroupId, tokenForAssetKey} from '../../asset-graph/Utils';
import {ASSET_CATALOG_TABLE_QUERY} from '../../assets/AssetsCatalogTable';
import {AssetTableFragment} from '../../assets/types/AssetTableFragment.types';
import {
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables,
} from '../../assets/types/AssetsCatalogTable.types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {TimeDividers} from '../../runs/RunTimeline';
import {useHourWindow} from '../../runs/useHourWindow';
import {Container, HeaderCell, Inner} from '../../ui/VirtualizedTable';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {RepoAddress} from '../../workspace/types';
import {TimePageControls, hourWindowToOffset} from '../OverviewTimelineRoot';

const ONE_HOUR_MSEC = 60 * 60 * 1000;
const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

export type NodeNonAssetType =
  | {groupName: string; id: string; level: number; type: 'group'; repoAddress: RepoAddress}
  | {locationName: string; id: string; level: number; type: 'location'; repoAddress: RepoAddress};

export type NodeType =
  | NodeNonAssetType
  | {
      path: string;
      id: string;
      asset: AssetTableFragment;
      level: number;
      type: 'asset';
      repoAddress: RepoAddress;
    };

type Props = {
  Header: React.ComponentType<{refreshState: ReturnType<typeof useQueryRefreshAtInterval>}>;
  TabButton: React.ComponentType<{selected: 'timeline' | 'assets' | 'asset-timeline'}>;
};
export const AssetTimelineRoot = ({Header, TabButton}: Props) => {
  useTrackPageView();
  useDocumentTitle('Overview | Assets');

  const query = useQuery<AssetCatalogTableQuery, AssetCatalogTableQueryVariables>(
    ASSET_CATALOG_TABLE_QUERY,
    {
      notifyOnNetworkStatusChange: true,
    },
  );
  const refreshState = useQueryRefreshAtInterval(query, FIFTEEN_SECONDS);

  const [hourWindow, setHourWindow] = useHourWindow('12');
  const [now, setNow] = React.useState(() => Date.now());
  const [offsetMsec, setOffsetMsec] = React.useState(() => 0);

  const onPageEarlier = React.useCallback(() => {
    setOffsetMsec((current) => current - hourWindowToOffset(hourWindow));
  }, [hourWindow]);

  const onPageLater = React.useCallback(() => {
    setOffsetMsec((current) => current + hourWindowToOffset(hourWindow));
  }, [hourWindow]);

  const onPageNow = React.useCallback(() => {
    setOffsetMsec(0);
  }, []);

  React.useEffect(() => {
    setNow(Date.now());
    const timer = setInterval(() => {
      setNow(Date.now());
    }, POLL_INTERVAL);

    return () => {
      clearInterval(timer);
    };
  }, [hourWindow]);

  const range: [number, number] = React.useMemo(
    () => [
      now - Number(hourWindow) * ONE_HOUR + offsetMsec,
      now + LOOKAHEAD_HOURS * ONE_HOUR + offsetMsec,
    ],
    [hourWindow, now, offsetMsec],
  );

  const groupedAssetsUnfiltered = React.useMemo(() => {
    if (query.data?.assetsOrError.__typename === 'AssetConnection') {
      const assets = query.data.assetsOrError.nodes;
      return groupAssets(assets);
    }
    return [];
  }, [query.data?.assetsOrError]);

  const [searchValue, setSearchValue] = useQueryPersistedState<string>({
    queryKey: 'q',
    decode: (qs) => (qs.searchQuery ? JSON.parse(qs.searchQuery) : ''),
    encode: (searchQuery) => ({searchQuery: searchQuery ? JSON.stringify(searchQuery) : undefined}),
  });

  const lowerCaseSearchValue = searchValue.toLowerCase();

  const groupedAssetsFiltered = React.useMemo(() => {
    if (lowerCaseSearchValue === '') {
      return groupedAssetsUnfiltered;
    }
    const filteredGroups: typeof groupedAssetsUnfiltered = [];
    groupedAssetsUnfiltered.forEach((group) => {
      if (
        (group.groupName || UNGROUPED_ASSETS).toLowerCase().includes(lowerCaseSearchValue) ||
        group.repositoryName.toLowerCase().includes(lowerCaseSearchValue)
      ) {
        filteredGroups.push(group);
      } else {
        const filteredGroupAssets = group.assets.filter((asset) =>
          tokenForAssetKey(asset.key).toLowerCase().includes(lowerCaseSearchValue),
        );
        if (filteredGroupAssets.length) {
          filteredGroups.push({
            ...group,
            assets: filteredGroupAssets,
          });
        }
      }
    });
    return filteredGroups;
  }, [groupedAssetsUnfiltered, lowerCaseSearchValue]);

  const [openNodes, setOpenNodes] = useStateWithStorage<Set<string>>(
    'asset-timeline-open-nodes',
    (json) => {
      if (json instanceof Array) {
        return new Set(json);
      }
      return new Set();
    },
  );

  const [sidebarWidth, _setSidebarWidth] = useStateWithStorage(
    'assets-timeline-sidebar-width',
    (json) => {
      try {
        const int = parseInt(json);
        if (!isNaN(int)) {
          return int;
        }
      } catch (e) {}
      return 306;
    },
  );

  const {renderedNodes, codeLocationNodes} = React.useMemo(() => {
    const nodes: NodeType[] = [];

    // Map of Code Locations -> Groups -> Assets
    const codeLocationNodes: CodeLocationNodes = {};

    let groupsCount = 0;
    groupedAssetsFiltered.forEach((group) => {
      const {repositoryName, locationName, groupName: _groupName, assets} = group;
      const groupName = _groupName || 'default';

      const groupId = toGroupId(repositoryName, locationName, groupName);
      const codeLocation = buildRepoPathForHuman(repositoryName, locationName);
      codeLocationNodes[codeLocation] = codeLocationNodes[codeLocation] || {
        locationName: codeLocation,
        repoAddress: {
          name: repositoryName,
          location: locationName,
        },
        groups: {},
      };

      if (!codeLocationNodes[codeLocation]!.groups[groupId]!) {
        groupsCount += 1;
      }

      codeLocationNodes[codeLocation]!.groups[groupId] = codeLocationNodes[codeLocation]!.groups[
        groupId
      ] || {
        groupName,
        assets,
        groupId,
      };
    });

    const codeLocationsCount = Object.keys(codeLocationNodes).length;
    Object.entries(codeLocationNodes).forEach(([locationName, locationNode]) => {
      nodes.push({
        locationName,
        type: 'location',
        id: locationName,
        level: 1,
        repoAddress: locationNode.repoAddress,
      });
      if (openNodes.has(locationName) || codeLocationsCount === 1) {
        Object.entries(locationNode.groups).forEach(([id, groupNode]) => {
          nodes.push({
            groupName: groupNode.groupName,
            type: 'group',
            id,
            level: 2,
            repoAddress: locationNode.repoAddress,
          });
          if (openNodes.has(id) || groupsCount === 1) {
            groupNode.assets
              .sort((a, b) => COLLATOR.compare(tokenForAssetKey(a.key), tokenForAssetKey(b.key)))
              .forEach((asset) => {
                const key = tokenForAssetKey(asset.key);
                nodes.push({
                  type: 'asset' as const,
                  id: key,
                  asset,
                  path: locationName + ':' + groupNode.groupName + ':' + key,
                  level: 3,
                  repoAddress: locationNode.repoAddress,
                });
              });
          }
        });
      }
    });
    return {renderedNodes: nodes, codeLocationNodes};
  }, [openNodes, groupedAssetsFiltered]);

  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: renderedNodes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 34,
    overscan: 5,
  });

  const {viewport, containerProps} = useViewport();

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  function content() {
    const result = query.data?.assetsOrError;
    if (!query.data && query.loading) {
      return (
        <Box
          flex={{alignItems: 'center', justifyContent: 'center', direction: 'column', grow: 1}}
          style={{width: '100%'}}
        >
          <Spinner purpose="page" />
        </Box>
      );
    }
    if (result?.__typename === 'PythonError') {
      return (
        <Box
          flex={{alignItems: 'center', justifyContent: 'center', direction: 'column', grow: 1}}
          style={{width: '100%'}}
        >
          <PythonErrorInfo error={result} />
        </Box>
      );
    }

    const timelineWidth = viewport.width - sidebarWidth;

    // eslint-disable-next-line react-hooks/rules-of-hooks

    return (
      <>
        <Box flex={{direction: 'column'}} style={{overflow: 'hidden', position: 'relative'}}>
          <AssetsTimelineDataFetcher codeLocationNodes={codeLocationNodes} range={range}>
            <VirtualHeaderRow
              sidebarWidth={sidebarWidth}
              searchValue={searchValue}
              setSearchValue={setSearchValue}
              range={range}
              now={now}
              tableHeight={viewport.height}
            />
            <Container
              {...containerProps}
              ref={(node) => {
                if (node) {
                  parentRef.current = node;
                  containerProps.ref(node);
                }
              }}
            >
              <Inner $totalHeight={totalHeight}>
                {items.map(({index, size, start}) => {
                  const node = renderedNodes[index]!;
                  return (
                    <AssetTimelineRow
                      key={node.id}
                      range={range}
                      height={size}
                      top={start}
                      node={node}
                      sidebarWidth={sidebarWidth}
                      timelineWidth={timelineWidth}
                      openNodes={openNodes}
                      setOpenNodes={setOpenNodes}
                    />
                  );
                })}
              </Inner>
            </Container>
          </AssetsTimelineDataFetcher>
        </Box>
      </>
    );
  }

  return (
    <>
      <div style={{position: 'sticky', top: 0, zIndex: 1}}>
        <Header refreshState={refreshState} />
        <Box
          padding={{horizontal: 24, vertical: 16}}
          flex={{alignItems: 'center', gap: 12, grow: 0, justifyContent: 'space-between'}}
        >
          <TabButton selected="asset-timeline" />
          <TimePageControls
            onPageEarlier={onPageEarlier}
            onPageLater={onPageLater}
            onPageNow={onPageNow}
            hourWindow={hourWindow}
            setHourWindow={setHourWindow}
          />
        </Box>
      </div>
      {content()}
    </>
  );
};

const LOOKAHEAD_HOURS = 1;
const ONE_HOUR = 60 * 60 * 1000;
const POLL_INTERVAL = 60 * 1000;

type Assets = Extract<
  AssetCatalogTableQuery['assetsOrError'],
  {__typename: 'AssetConnection'}
>['nodes'];

function groupAssets(assets: Assets) {
  const groups: Record<
    string,
    {
      groupName: string | null;
      groupId: string;
      repositoryName: string;
      locationName: string;
      assets: Assets;
    }
  > = {};

  assets.forEach((asset) => {
    if (!asset.definition) {
      return;
    }
    const groupName = asset.definition.groupName;
    const repositoryName = asset.definition.repository.name;
    const locationName = asset.definition.repository.location.name;
    const key = groupIdForNode(asset);
    const target = groups[key] || {
      groupId: key,
      groupName,
      repositoryName,
      locationName,
      assets: [] as Assets,
    };
    target.assets.push(asset);
    groups[key] = target;
  });
  return Object.values(groups);
}

function VirtualHeaderRow({
  sidebarWidth,
  searchValue,
  setSearchValue,
  range,
  now,
  tableHeight,
}: {
  sidebarWidth: number;
  searchValue: string;
  setSearchValue: (value: string) => void;
  range: [number, number];
  now: number;
  tableHeight: number;
}) {
  return (
    <Box
      border="top"
      style={{
        display: 'grid',
        gridTemplateColumns: `${sidebarWidth}px 1fr`,
        fontSize: '12px',
        color: Colors.textLight(),
        position: 'sticky',
        top: 0,
        zIndex: 1,
        height: 64,
        background: Colors.backgroundDefault(),
      }}
    >
      <HeaderCell style={{width: sidebarWidth}}>
        <TextInputWrapper>
          <TextInput
            value={searchValue}
            icon="search"
            placeholder="Filter assets"
            onChange={(e: React.ChangeEvent<any>) => {
              setSearchValue(e.target.value);
            }}
          />
        </TextInputWrapper>
      </HeaderCell>
      <Box border="bottom">
        <HeaderCell>
          <div style={{position: 'absolute', top: 0, bottom: 0, left: 0, right: 0}}>
            <TimeDividers
              interval={ONE_HOUR_MSEC}
              range={range}
              height={0}
              left={sidebarWidth - 1}
              style={{zIndex: 9999, pointerEvents: 'none'}}
              now={now}
              top={0}
              tableHeight={tableHeight}
            />
          </div>
        </HeaderCell>
      </Box>
    </Box>
  );
}

const UNGROUPED_ASSETS = 'Ungrouped Assets';

const TextInputWrapper = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
  place-items: center;
  > * {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    width: 100%;
  }
  height: 48px;
`;
