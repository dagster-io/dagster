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
import {ASSET_CATALOG_TABLE_QUERY} from '../assets/AssetsCatalogTable';
import {
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables,
} from '../assets/types/AssetsCatalogTable.types';
import {RunStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Container, HeaderCell, Inner, Row, RowCell} from '../ui/VirtualizedTable';
import {StatusCase, buildAssetNodeStatusContent} from '../asset-graph/AssetNode';
import {toGraphId} from '../asset-graph/Utils';
import {Link} from 'react-router-dom';
import {workspacePathFromAddress} from '../workspace/workspacePath';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepositoryLink, RepositoryName} from '../nav/RepositoryLink';

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

  const groupedAssets = React.useMemo(() => {
    if (query.data?.assetsOrError.__typename === 'AssetConnection') {
      return groupAssets(query.data?.assetsOrError.nodes);
    }
    return [];
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
      <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
        <VirtualHeaderRow />
        <Container>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const group = groupedAssets[index];
              return <VirtualRow key={key} start={start} height={size} group={group} />;
            })}
          </Inner>
        </Container>
      </Box>
    );
  }

  return (
    <div style={{position: 'sticky', top: 0, zIndex: 1}}>
      <Header refreshState={refreshState} />
      <Box padding={{horizontal: 24, vertical: 16}} flex={{alignItems: 'center', gap: 12, grow: 0}}>
        <TabButton selected="assets" />
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Filter by asset group"
          style={{width: '200px'}}
        />
      </Box>
      {content()}
    </div>
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
    const groupName = asset.definition?.groupName || 'default';
    const repositoryName = asset.definition?.repository.name || 'unknown';
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
        assetKey: JSON.parse(key),
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

  const repo = group.assets.find((asset) => asset.definition?.repository)?.definition?.repository!;
  const repoAddress = buildRepoAddress(repo.name, repo.location.name);

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
        <div>{children}</div>
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
