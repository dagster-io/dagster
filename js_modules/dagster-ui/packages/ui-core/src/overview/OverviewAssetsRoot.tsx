import {useQuery} from '@apollo/client';
import {
  Box,
  Caption,
  Colors,
  Icon,
  MenuItem,
  Select,
  Spinner,
  Tag,
  TextInput,
  useViewport,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useAssetsLiveData} from '../asset-data/AssetLiveDataProvider';
import {StatusCase, buildAssetNodeStatusContent} from '../asset-graph/AssetNodeStatusContent';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {groupAssetsByStatus} from '../asset-graph/util';
import {partitionCountString} from '../assets/AssetNodePartitionCounts';
import {ASSET_CATALOG_TABLE_QUERY} from '../assets/AssetsCatalogTable';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables,
} from '../assets/types/AssetsCatalogTable.types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RepositoryLink} from '../nav/RepositoryLink';
import {Container, HeaderCell, Inner, Row, RowCell} from '../ui/VirtualizedTable';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../workspace/workspacePath';

type Props = {
  Header: React.ComponentType<{refreshState: ReturnType<typeof useQueryRefreshAtInterval>}>;
  TabButton: React.ComponentType<{selected: 'timeline' | 'assets'}>;
};
export const OverviewAssetsRoot = ({Header, TabButton}: Props) => {
  useTrackPageView();
  useDocumentTitle('Overview | Assets');

  const query = useQuery<AssetCatalogTableQuery, AssetCatalogTableQueryVariables>(
    ASSET_CATALOG_TABLE_QUERY,
    {
      notifyOnNetworkStatusChange: true,
    },
  );
  const refreshState = useQueryRefreshAtInterval(query, FIFTEEN_SECONDS);

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

  const groupedAssets = React.useMemo(() => {
    if (searchValue === '') {
      return groupedAssetsUnfiltered;
    }
    return groupedAssetsUnfiltered.filter((group) => {
      return (
        (group.groupName || UNGROUPED_ASSETS).toLowerCase().includes(searchValue.toLowerCase()) ||
        group.repositoryName.toLowerCase().includes(searchValue.toLowerCase())
      );
    });
  }, [groupedAssetsUnfiltered, searchValue]);

  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: groupedAssets.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 82,
    overscan: 5,
  });

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

    return (
      <Box flex={{direction: 'column'}} style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <VirtualHeaderRow />
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const group = groupedAssets[index]!;
              return <VirtualRow key={key} start={start} height={size} group={group} />;
            })}
          </Inner>
        </Container>
      </Box>
    );
  }

  return (
    <>
      <div style={{position: 'sticky', top: 0, zIndex: 1}}>
        <Header refreshState={refreshState} />
        <Box
          padding={{horizontal: 24, vertical: 16}}
          flex={{alignItems: 'center', gap: 12, grow: 0}}
        >
          <TabButton selected="assets" />
          <TextInput
            value={searchValue}
            onChange={(e) => {
              setSearchValue(e.target.value);
            }}
            placeholder="Filter asset groups…"
          />
        </Box>
      </div>
      {content()}
    </>
  );
};

type Assets = Extract<
  AssetCatalogTableQuery['assetsOrError'],
  {__typename: 'AssetConnection'}
>['nodes'];

function groupAssets(assets: Assets) {
  const groups: Record<
    string,
    {
      groupName: string | null;
      repositoryName: string;
      assets: Assets;
    }
  > = {};

  assets.forEach((asset) => {
    if (!asset.definition) {
      return;
    }
    const groupName = asset.definition.groupName;
    const repositoryName = asset.definition.repository.name;
    const key = `${groupName}||${repositoryName}`;
    const target = groups[key] || {
      groupName,
      repositoryName,
      assets: [] as Assets,
    };
    target.assets.push(asset);
    groups[key] = target;
  });
  return Object.values(groups);
}

const TEMPLATE_COLUMNS = '5fr 1fr 1fr 1fr 1fr';

function VirtualHeaderRow() {
  return (
    <Box
      border="top-and-bottom"
      style={{
        display: 'grid',
        gridTemplateColumns: TEMPLATE_COLUMNS,
        height: '32px',
        fontSize: '12px',
        color: Colors.textLight(),
        position: 'sticky',
        top: 0,
        zIndex: 1,
        background: Colors.backgroundDefault(),
      }}
    >
      <HeaderCell>Group name</HeaderCell>
      <HeaderCell>Missing</HeaderCell>
      <HeaderCell>Failed/Overdue</HeaderCell>
      <HeaderCell>In progress</HeaderCell>
      <HeaderCell>Materialized</HeaderCell>
    </Box>
  );
}

const UNGROUPED_ASSETS = 'Ungrouped Assets';
type RowProps = {
  height: number;
  start: number;
  group: ReturnType<typeof groupAssets>[0];
};
function VirtualRow({height, start, group}: RowProps) {
  const assetKeys = React.useMemo(
    () => group.assets.map((asset) => ({path: asset.key.path})),
    [group.assets],
  );

  const {liveDataByNode} = useAssetsLiveData(assetKeys);

  const statuses = React.useMemo(() => {
    return groupAssetsByStatus(group.assets, liveDataByNode);
  }, [liveDataByNode, group.assets]);

  const repo = group.assets.find((asset) => asset.definition?.repository)?.definition?.repository;
  const repoAddress = buildRepoAddress(repo?.name || '', repo?.location.name || '');

  const {containerProps, viewport} = useViewport();

  const isBatchStillLoading = assetKeys.length !== Object.keys(liveDataByNode).length;
  const zeroOrBlank = isBatchStillLoading ? '' : '0';

  return (
    <Row $height={height} $start={start}>
      <RowGrid border="bottom">
        <Cell>
          <Box flex={{direction: 'row', justifyContent: 'space-between', grow: 1}}>
            <Box flex={{direction: 'column', gap: 2, grow: 1}}>
              <Box flex={{direction: 'row', gap: 8}}>
                <Icon name="asset_group" />
                {group.groupName ? (
                  <Link
                    style={{fontWeight: 700}}
                    to={workspacePathFromAddress(repoAddress, `/asset-groups/${group.groupName}`)}
                  >
                    {group.groupName}
                  </Link>
                ) : (
                  UNGROUPED_ASSETS
                )}
              </Box>
              <div {...containerProps}>
                <RepositoryLinkWrapper maxWidth={viewport.width}>
                  <RepositoryLink repoAddress={repoAddress} showRefresh={false} />
                </RepositoryLinkWrapper>
              </div>
            </Box>
            <Box flex={{direction: 'column', justifyContent: 'center'}}>
              {isBatchStillLoading ? <Spinner purpose="body-text" /> : null}
            </Box>
          </Box>
        </Cell>
        <Cell>
          {statuses.missing.length ? (
            <SelectOnHover
              assets={statuses.missing}
              getCount={({status}) => {
                if (status.case === StatusCase.PARTITIONS_MISSING) {
                  return status.numMissing || 0;
                }
                return 0;
              }}
              adjective="missing"
            >
              <Tag intent="none">
                <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                  <div
                    style={{
                      width: '12px',
                      height: '12px',
                      border: `2px solid ${Colors.borderDefault()}`,
                      borderRadius: '50%',
                    }}
                  />
                  {statuses.missing.length}
                </Box>
              </Tag>
            </SelectOnHover>
          ) : (
            zeroOrBlank
          )}
        </Cell>
        <Cell>
          {statuses.failed.length ? (
            <SelectOnHover
              assets={statuses.failed}
              getCount={({status}) => {
                if (status.case === StatusCase.PARTITIONS_FAILED) {
                  return status.numFailed || 0;
                }
                return 0;
              }}
              adjective="failed"
            >
              <Tag intent="danger">
                <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                  <div
                    style={{
                      width: 0,
                      height: 0,
                      borderLeft: '6px solid transparent',
                      borderRight: '6px solid transparent',
                      borderBottom: '10px solid red',
                      display: 'inline-block',
                    }}
                  />
                  {statuses.failed.length}
                </Box>
              </Tag>
            </SelectOnHover>
          ) : (
            zeroOrBlank
          )}
        </Cell>
        <Cell>
          {statuses.inprogress.length ? (
            <SelectOnHover
              assets={statuses.inprogress}
              getCount={({status}) => {
                if (status.case === StatusCase.MATERIALIZING) {
                  return status.numMaterializing || 0;
                }
                return 0;
              }}
              adjective="materializing"
            >
              <Tag intent="primary" icon="spinner">
                {statuses.inprogress.length}
              </Tag>
            </SelectOnHover>
          ) : (
            zeroOrBlank
          )}
        </Cell>
        <Cell>
          {statuses.successful.length ? (
            <SelectOnHover
              assets={statuses.successful}
              getCount={({status}) => {
                if (status.case === StatusCase.PARTITIONS_MATERIALIZED) {
                  return status.numMaterialized || 0;
                }
                return 0;
              }}
              adjective="materialized"
            >
              <Tag intent="success">
                <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                  <div
                    style={{
                      backgroundColor: Colors.accentGreen(),
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                    }}
                  />
                  {statuses.successful.length}
                </Box>
              </Tag>
            </SelectOnHover>
          ) : (
            zeroOrBlank
          )}
        </Cell>
      </RowGrid>
    </Row>
  );
}

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
  > * {
    vertical-align: middle;
  }
`;

const Cell = ({children}: {children: React.ReactNode}) => {
  return (
    <RowCell style={{color: Colors.textDefault()}}>
      <Box flex={{direction: 'row', alignItems: 'center', grow: 1}}>{children}</Box>
    </RowCell>
  );
};

const RepositoryLinkWrapper = styled.div<{maxWidth?: number}>`
  font-size: 12px;
  pointer-events: none;
  a {
    color: ${Colors.textLight()};
    pointer-events: none;
    max-width: ${({maxWidth}) => (maxWidth ? 'unset' : `${maxWidth}px`)};
  }
`;

type AssetWithStatusType = {
  asset: Assets[0];
  status: ReturnType<typeof buildAssetNodeStatusContent>;
};
function SelectOnHover({
  assets,
  children,
  getCount,
  adjective,
}: {
  assets: AssetWithStatusType[];
  children: React.ReactNode;
  getCount: (asset: AssetWithStatusType) => number;
  adjective: string;
}) {
  return (
    <SelectWrapper>
      <Select
        items={assets}
        itemPredicate={(query, item) =>
          displayNameForAssetKey(item.asset.key)
            .toLocaleLowerCase()
            .includes(query.toLocaleLowerCase())
        }
        itemRenderer={(item) => {
          const count = getCount(item);
          return (
            <LinkWithNoUnderline to={assetDetailsPathForKey(item.asset.key)} target="_blank">
              <MenuItem
                key={displayNameForAssetKey(item.asset.key)}
                text={
                  <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                    <div style={{paddingLeft: '4px'}}>
                      <Icon name="asset" />
                    </div>
                    <div
                      style={{overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis'}}
                    >
                      {displayNameForAssetKey(item.asset.key)}
                    </div>
                    {count && count > 0 ? (
                      <Caption style={{color: Colors.textLight()}}>
                        {partitionCountString(count)} {adjective}
                      </Caption>
                    ) : null}
                  </Box>
                }
              />
            </LinkWithNoUnderline>
          );
        }}
        onItemSelect={() => {}}
      >
        {children}
      </Select>
    </SelectWrapper>
  );
}

const SelectWrapper = styled.div`
  cursor: pointer;
  &:hover {
    font-weight: 600;
  }
`;

const LinkWithNoUnderline = styled(Link)`
  &:hover {
    text-decoration: none;
  }
`;
