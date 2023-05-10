import {useQuery} from '@apollo/client';
import {
  Box,
  TextInput,
  Spinner,
  Colors,
  ButtonLink,
  Icon,
  Button,
  Tag,
  useViewport,
} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components/macro';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useLiveDataForAssetKeys} from '../asset-graph/useLiveDataForAssetKeys';
import {ASSET_CATALOG_TABLE_QUERY, AssetGroupSuggest} from '../assets/AssetsCatalogTable';
import {
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables,
} from '../assets/types/AssetsCatalogTable.types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Container, HeaderCell, Inner, Row, RowCell} from '../ui/VirtualizedTable';
import {StatusCase, buildAssetNodeStatusContent} from '../asset-graph/AssetNode';
import {toGraphId} from '../asset-graph/Utils';
import {Link} from 'react-router-dom';
import {workspacePathFromAddress} from '../workspace/workspacePath';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepositoryLink, RepositoryName} from '../nav/RepositoryLink';
import {AssetGroupSelector} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';

type Props = {
  Header: React.FC<{refreshState: ReturnType<typeof useQueryRefreshAtInterval>}>;
  TabButton: React.FC<{selected: 'timeline' | 'assets'}>;
};
export const OverviewAssetsRoot = ({Header, TabButton}: Props) => {
  useTrackPageView();
  useDocumentTitle('Overview | Timeline');

  const [searchValue, setSearchValue] = React.useState('');

  const query = useQuery<AssetCatalogTableQuery, AssetCatalogTableQueryVariables>(
    ASSET_CATALOG_TABLE_QUERY,
    {
      notifyOnNetworkStatusChange: true,
    },
  );
  const refreshState = useQueryRefreshAtInterval(query, FIFTEEN_SECONDS);

  const {assets, groupedAssets} = React.useMemo(() => {
    if (query.data?.assetsOrError.__typename === 'AssetConnection') {
      const assets = query.data.assetsOrError.nodes;
      return {assets, groupedAssets: groupAssets(assets)};
    }
    return {assets: [], groupedAssets: []};
  }, [query.data?.assetsOrError]);

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
        <VirtualHeaderRow />
        <div style={{overflow: 'hidden'}}>
          <Container ref={parentRef}>
            <Inner $totalHeight={totalHeight}>
              {items.map(({index, key, size, start}) => {
                const group = groupedAssets[index];
                return <VirtualRow key={key} start={start} height={size} group={group} />;
              })}
            </Inner>
          </Container>
        </div>
      </Box>
    );
  }

  const [searchGroup, setSearchGroup] = useQueryPersistedState<AssetGroupSelector | null>({
    queryKey: 'g',
    decode: (qs) => (qs.group ? JSON.parse(qs.group) : null),
    encode: (group) => ({group: group ? JSON.stringify(group) : undefined}),
  });

  return (
    <>
      <div style={{position: 'sticky', top: 0, zIndex: 1}}>
        <Header refreshState={refreshState} />
        <Box
          padding={{horizontal: 24, vertical: 16}}
          flex={{alignItems: 'center', gap: 12, grow: 0}}
        >
          <TabButton selected="assets" />
          <AssetGroupSuggest assets={assets} value={searchGroup} onChange={setSearchGroup} />
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
      groupName: string;
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
    groups[key] = groups[key] || {
      groupName,
      repositoryName,
      assets: [],
    };
    groups[key].assets.push(asset);
  });
  return Object.values(groups);
}

const TEMPLATE_COLUMNS = '5fr 1fr 1fr 1fr 1fr';

function VirtualHeaderRow() {
  return (
    <Box
      border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
      style={{
        display: 'grid',
        gridTemplateColumns: TEMPLATE_COLUMNS,
        height: '32px',
        fontSize: '12px',
        color: Colors.Gray600,
      }}
    >
      <HeaderCell>Group name</HeaderCell>
      <HeaderCell>Missing</HeaderCell>
      <HeaderCell>Failed/Overdue</HeaderCell>
      <HeaderCell>In Progress</HeaderCell>
      <HeaderCell>Materialized</HeaderCell>
    </Box>
  );
}

type RowProps = {
  height: number;
  start: number;
  group: ReturnType<typeof groupAssets>[0];
};
function VirtualRow({height, start, group}: RowProps) {
  const assetKeys = React.useMemo(() => group.assets.map((asset) => ({path: asset.key.path})), [
    group.assets,
  ]);

  const {liveDataByNode} = useLiveDataForAssetKeys(assetKeys);

  const statuses = React.useMemo(() => {
    const statuses = {successful: 0, failed: 0, inprogress: 0, missing: 0, loading: 0};
    if (!Object.keys(liveDataByNode).length) {
      statuses.loading = 1;
      return statuses;
    }
    Object.keys(liveDataByNode).forEach((key) => {
      const assetLiveData = liveDataByNode[key];
      const asset = group.assets.find((asset) => toGraphId(asset.key) === key)!;
      if (!asset.definition) {
        console.warn('Expected a definition for asset with key', key);
      }
      const status = buildAssetNodeStatusContent({
        assetKey: {path: JSON.parse(key)},
        definition: asset.definition!,
        liveData: assetLiveData,
        expanded: true,
      });
      switch (status.case) {
        case StatusCase.LOADING:
          statuses.loading++;
          break;
        case StatusCase.SOURCE_OBSERVING:
          statuses.inprogress++;
          break;
        case StatusCase.SOURCE_OBSERVED:
          statuses.successful++;
          break;
        case StatusCase.SOURCE_NEVER_OBSERVED:
          statuses.missing++;
          break;
        case StatusCase.SOURCE_NO_STATE:
          statuses.missing++;
          break;
        case StatusCase.MATERIALIZING:
          statuses.successful++;
          break;
        case StatusCase.LATE_OR_FAILED:
          statuses.failed++;
          break;
        case StatusCase.NEVER_MATERIALIZED:
          statuses.missing++;
          break;
        case StatusCase.MATERIALIZED:
          statuses.successful++;
          break;
        case StatusCase.PARTITIONS_FAILED:
          statuses.failed++;
          break;
        case StatusCase.PARTITIONS_MISSING:
          statuses.missing++;
          break;
        case StatusCase.PARTITIONS_MATERIALIZED:
          statuses.successful++;
          break;
      }
    });
    return statuses;
  }, [liveDataByNode]);

  const repo = group.assets.find((asset) => asset.definition?.repository)?.definition?.repository;
  const repoAddress = buildRepoAddress(repo?.name || '', repo?.location.name || '');

  const {containerProps, viewport} = useViewport();

  return (
    <Row $height={height} $start={start}>
      <RowGrid border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}>
        <Cell>
          <Box flex={{direction: 'column', gap: 2}}>
            <Box flex={{direction: 'row', gap: 8}}>
              <Icon name="asset_group" />
              <Link
                style={{fontWeight: 700}}
                to={workspacePathFromAddress(repoAddress, `/asset-groups/${group.groupName}`)}
              >
                {group.groupName}
              </Link>
            </Box>
            <div {...containerProps}>
              <RepositoryLinkWrapper maxWidth={viewport.width}>
                <RepositoryLink repoAddress={repoAddress} showRefresh={false} />
              </RepositoryLinkWrapper>
            </div>
          </Box>
        </Cell>
        <Cell isLoading={!!statuses.loading}>
          {statuses.missing ? (
            <Tag intent="none">
              <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                <div
                  style={{
                    width: '12px',
                    height: '12px',
                    border: `2px solid ${Colors.Gray500}`,
                    borderRadius: '50%',
                  }}
                />
                {statuses.missing}
              </Box>
            </Tag>
          ) : null}
        </Cell>
        <Cell isLoading={!!statuses.loading}>
          {statuses.failed ? (
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
                {statuses.failed}
              </Box>
            </Tag>
          ) : null}
        </Cell>
        <Cell isLoading={!!statuses.loading}>
          {statuses.inprogress ? (
            <Tag intent="primary" icon="spinner">
              {statuses.inprogress}
            </Tag>
          ) : null}
        </Cell>
        <Cell isLoading={!!statuses.loading}>
          {statuses.successful ? (
            <Tag intent="success">
              <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                <div
                  style={{
                    backgroundColor: Colors.Green500,
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                  }}
                />
                {statuses.successful}
              </Box>
            </Tag>
          ) : null}
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
    padding-top: 26px 0px;
  }
`;

const Cell = ({children, isLoading}: {children: React.ReactNode; isLoading?: boolean}) => {
  return (
    <RowCell style={{color: Colors.Gray900}}>
      {isLoading ? (
        <Box flex={{justifyContent: 'center', alignItems: 'center'}} style={{height: '82px'}}>
          <Spinner purpose="body-text" />
        </Box>
      ) : (
        <Box flex={{direction: 'row', alignItems: 'center', grow: 1}}>{children}</Box>
      )}
    </RowCell>
  );
};

const RepositoryLinkWrapper = styled.div<{maxWidth?: number}>`
  font-size: 12px;
  a {
    max-width: ${({maxWidth}) => (maxWidth ? 'unset' : `${maxWidth}px`)};
  }
`;
