import {gql, useLazyQuery} from '@apollo/client';
import {Box, Caption, Colors, Icon, IconWrapper, Tag} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {AppContext} from '../app/AppContext';
import {
  AssetLatestRunWithNotices,
  AssetRunLink,
  ASSET_NODE_LIVE_FRAGMENT,
  ComputeStatusNotice,
} from '../asset-graph/AssetNode';
import {buildLiveDataForNode} from '../asset-graph/Utils';
import {ASSET_LATEST_INFO_FRAGMENT} from '../asset-graph/useLiveDataForAssetKeys';
import {AssetActionMenu} from '../assets/AssetActionMenu';
import {AssetLink} from '../assets/AssetLink';
import {ASSET_TABLE_FRAGMENT} from '../assets/AssetTable';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {Container, HeaderCell, Inner, Row, RowCell} from '../ui/VirtualizedTable';

import {LoadingOrNone, useDelayedRowQuery} from './VirtualizedWorkspaceTable';
import {repoAddressAsString} from './repoAddressAsString';
import {RepoAddress} from './types';
import {SingleAssetQuery, SingleAssetQueryVariables} from './types/SingleAssetQuery';
import {workspacePathFromAddress} from './workspacePath';

type Asset = {id: string; groupName: string | null; assetKey: {path: string[]}};

interface Props {
  repoAddress: RepoAddress;
  assets: Asset[];
}

type RowType =
  | {type: 'group'; name: string; assetCount: number}
  | {type: 'asset'; id: string; path: string[]};

const UNGROUPED_NAME = 'UNGROUPED';
const ASSET_GROUPS_EXPANSION_STATE_STORAGE_KEY = 'assets-virtualized-expansion-state';

export const VirtualizedAssetTable: React.FC<Props> = ({repoAddress, assets}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const repoKey = repoAddressAsString(repoAddress);
  const {expandedKeys, onToggle} = useAssetGroupExpansionState(
    `${repoKey}-${ASSET_GROUPS_EXPANSION_STATE_STORAGE_KEY}`,
  );

  const grouped: {[key: string]: Asset[]} = React.useMemo(() => {
    const groups = {};
    for (const asset of assets) {
      const groupName = asset.groupName || UNGROUPED_NAME;
      const assetsForGroup = groups[groupName] || [];
      groups[groupName] = [...assetsForGroup, asset];
    }
    return groups;
  }, [assets]);

  const flattened: RowType[] = React.useMemo(() => {
    const flat: RowType[] = [];
    Object.keys(grouped).forEach((groupName) => {
      const assetsForGroup = grouped[groupName];
      flat.push({type: 'group', name: groupName, assetCount: assetsForGroup.length});
      if (expandedKeys.includes(groupName)) {
        assetsForGroup.forEach(({id, assetKey}) => {
          flat.push({type: 'asset', id, path: assetKey.path});
        });
      }
    });
    return flat;
  }, [grouped, expandedKeys]);

  const rowVirtualizer = useVirtualizer({
    count: flattened.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (ii: number) => {
      const row = flattened[ii];
      return row?.type === 'group' ? 48 : 64;
    },
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <>
      <Box
        border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
        style={{
          display: 'grid',
          gridTemplateColumns: '40% 30% 20% 10%',
          height: '32px',
          fontSize: '12px',
          color: Colors.Gray600,
        }}
      >
        <HeaderCell>Asset name</HeaderCell>
        <HeaderCell>Materialized</HeaderCell>
        <HeaderCell>Latest run</HeaderCell>
        <HeaderCell>Actions</HeaderCell>
      </Box>
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const row: RowType = flattened[index];
              const type = row!.type;
              return type === 'group' ? (
                <GroupNameRow
                  repoAddress={repoAddress}
                  groupName={row.name}
                  assetCount={row.assetCount}
                  expanded={expandedKeys.includes(row.name)}
                  key={key}
                  height={size}
                  start={start}
                  onToggle={onToggle}
                />
              ) : (
                <AssetRow
                  key={key}
                  path={row.path}
                  repoAddress={repoAddress}
                  height={size}
                  start={start}
                />
              );
            })}
          </Inner>
        </Container>
      </div>
    </>
  );
};

interface JobRowProps {
  path: string[];
  repoAddress: RepoAddress;
  height: number;
  start: number;
}

const AssetRow = (props: JobRowProps) => {
  const {path, repoAddress, start, height} = props;

  const [queryAsset, queryResult] = useLazyQuery<SingleAssetQuery, SingleAssetQueryVariables>(
    SINGLE_ASSET_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {input: {path}},
    },
  );

  useDelayedRowQuery(queryAsset);
  const {data} = queryResult;

  const asset = React.useMemo(() => {
    if (data?.assetOrError.__typename === 'Asset') {
      return data.assetOrError;
    }
    return null;
  }, [data]);

  const liveData = React.useMemo(() => {
    if (asset?.definition && data?.assetsLatestInfo) {
      const latestInfoForAsset = data.assetsLatestInfo[0];
      if (latestInfoForAsset) {
        return buildLiveDataForNode(asset.definition, latestInfoForAsset);
      }
    }
    return null;
  }, [data, asset]);

  const linkUrl = assetDetailsPathForKey({path});

  return (
    <Row $height={height} $start={start}>
      <RowGrid border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}>
        <RowCell>
          <AssetLink path={path} url={linkUrl} isGroup={false} icon="asset" />
          <div
            style={{
              maxWidth: '100%',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            <Caption
              style={{
                color: Colors.Gray500,
                whiteSpace: 'nowrap',
              }}
            >
              {asset?.definition?.description}
            </Caption>
          </div>
        </RowCell>
        <RowCell>
          {liveData?.lastMaterialization ? (
            <Box flex={{gap: 8, alignItems: 'center'}}>
              <>
                <AssetRunLink
                  runId={liveData.lastMaterialization.runId}
                  event={{
                    stepKey: liveData.stepKey,
                    timestamp: liveData.lastMaterialization.timestamp,
                  }}
                >
                  <TimestampDisplay
                    timestamp={Number(liveData.lastMaterialization.timestamp) / 1000}
                    timeFormat={{showSeconds: false, showTimezone: false}}
                  />
                </AssetRunLink>
              </>
              <ComputeStatusNotice computeStatus={liveData?.computeStatus} />
            </Box>
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          {liveData ? (
            <AssetLatestRunWithNotices liveData={liveData} />
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          {asset ? (
            <div>
              <AssetActionMenu repoAddress={repoAddress} asset={asset} />
            </div>
          ) : null}
        </RowCell>
      </RowGrid>
    </Row>
  );
};

export const GroupNameRow: React.FC<{
  repoAddress: RepoAddress;
  groupName: string;
  assetCount: number;
  expanded: boolean;
  height: number;
  start: number;
  onToggle: (groupName: string) => void;
}> = ({repoAddress, groupName, assetCount, expanded, height, start, onToggle}) => {
  return (
    <Row $height={height} $start={start}>
      <Box
        background={Colors.Gray50}
        flex={{direction: 'row', alignItems: 'center', gap: 8, justifyContent: 'space-between'}}
        padding={{horizontal: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        style={{height: '100%'}}
      >
        <Box flex={{alignItems: 'center', gap: 8}}>
          <Icon name="asset_group" />
          {groupName === UNGROUPED_NAME ? (
            <div>Ungrouped assets</div>
          ) : (
            <>
              <strong>{groupName}</strong>
              {groupName !== UNGROUPED_NAME ? (
                <Box margin={{left: 12}}>
                  <Link to={workspacePathFromAddress(repoAddress, `/asset-groups/${groupName}`)}>
                    <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                      <span>View lineage</span>
                      <Icon name="open_in_new" size={16} color={Colors.Link} />
                    </Box>
                  </Link>
                </Box>
              ) : null}
            </>
          )}
        </Box>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
          <Tag intent="primary">{assetCount === 1 ? '1 asset' : `${assetCount} assets`}</Tag>
          <ExpandButton onClick={() => onToggle(groupName)} $open={expanded}>
            <Icon name="arrow_drop_down" size={20} />
          </ExpandButton>
        </Box>
      </Box>
    </Row>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: 40% 30% 20% 10%;
  height: 100%;
`;

const ExpandButton = styled.button<{$open: boolean}>`
  background: none;
  border: 0;
  cursor: pointer;
  padding: 8px;
  margin: -8px;

  :focus,
  :active {
    outline: none;
  }

  ${IconWrapper}[aria-label="arrow_drop_down"] {
    transition: transform 100ms linear;
    ${({$open}) => ($open ? null : `transform: rotate(-90deg);`)}
  }
`;

const SINGLE_ASSET_QUERY = gql`
  query SingleAssetQuery($input: AssetKeyInput!) {
    assetOrError(assetKey: $input) {
      ... on Asset {
        id
        assetMaterializations(limit: 1) {
          runId
          timestamp
        }
        ...AssetTableFragment
        definition {
          id
          ...AssetNodeLiveFragment
        }
      }
    }
    assetsLatestInfo(assetKeys: [$input]) {
      ...AssetLatestInfoFragment
    }
  }

  ${ASSET_TABLE_FRAGMENT}
  ${ASSET_NODE_LIVE_FRAGMENT}
  ${ASSET_LATEST_INFO_FRAGMENT}
`;

const validateExpandedKeys = (parsed: unknown) => (Array.isArray(parsed) ? parsed : []);

/**
 * Use localStorage to persist the expanded/collapsed visual state of asset groups.
 */
export const useAssetGroupExpansionState = (storageKey: string) => {
  const {basePath} = React.useContext(AppContext);
  const [expandedKeys, setExpandedKeys] = useStateWithStorage<string[]>(
    `${basePath}:dagit.${storageKey}`,
    validateExpandedKeys,
  );

  const onToggle = React.useCallback(
    (groupName: string) => {
      setExpandedKeys((current) => {
        const nextExpandedKeys = new Set(current || []);
        if (nextExpandedKeys.has(groupName)) {
          nextExpandedKeys.delete(groupName);
        } else {
          nextExpandedKeys.add(groupName);
        }
        return Array.from(nextExpandedKeys);
      });
    },
    [setExpandedKeys],
  );

  return React.useMemo(
    () => ({
      expandedKeys,
      onToggle,
    }),
    [expandedKeys, onToggle],
  );
};
