import {gql, useLazyQuery} from '@apollo/client';
import {Box, Caption, Checkbox, Colors, Icon} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {ASSET_NODE_LIVE_FRAGMENT, buildAssetNodeStatusContent} from '../asset-graph/AssetNode';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {buildLiveDataForNode} from '../asset-graph/Utils';
import {ASSET_LATEST_INFO_FRAGMENT} from '../asset-graph/useLiveDataForAssetKeys';
import {AssetActionMenu} from '../assets/AssetActionMenu';
import {AssetLink} from '../assets/AssetLink';
import {PartitionCountLabels} from '../assets/AssetNodePartitionCounts';
import {ASSET_TABLE_FRAGMENT} from '../assets/AssetTableFragment';
import {StaleReasonsLabel} from '../assets/Stale';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetTableFragment} from '../assets/types/AssetTableFragment.types';
import {AssetViewType} from '../assets/useAssetView';
import {AssetComputeKindTag} from '../graph/OpTags';
import {RepositoryLink} from '../nav/RepositoryLink';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {HeaderCell, Row, RowCell} from '../ui/VirtualizedTable';

import {LoadingOrNone, useDelayedRowQuery} from './VirtualizedWorkspaceTable';
import {RepoAddress} from './types';
import {SingleAssetQuery, SingleAssetQueryVariables} from './types/VirtualizedAssetRow.types';
import {workspacePathFromAddress} from './workspacePath';

const TEMPLATE_COLUMNS = '1.3fr 1.3fr 80px';
const TEMPLATE_COLUMNS_FOR_CATALOG = '76px 1.3fr 1.3fr 1.3fr 80px';

interface AssetRowProps {
  checked: boolean;
  type: 'folder' | 'asset' | 'asset_non_sda';
  view?: AssetViewType;
  onToggleChecked: (values: {checked: boolean; shiftKey: boolean}) => void;
  showCheckboxColumn: boolean;
  showRepoColumn: boolean;
  path: string[];
  repoAddress: RepoAddress | null;
  height: number;
  start: number;
  onWipe: (assets: AssetTableFragment[]) => void;
}

export const VirtualizedAssetRow = (props: AssetRowProps) => {
  const {
    path,
    type,
    repoAddress,
    start,
    height,
    checked,
    onToggleChecked,
    onWipe,
    showCheckboxColumn = false,
    showRepoColumn,
    view = 'flat',
  } = props;

  const [queryAsset, queryResult] = useLazyQuery<SingleAssetQuery, SingleAssetQueryVariables>(
    SINGLE_ASSET_QUERY,
    {
      variables: {input: {path}},
    },
  );

  useDelayedRowQuery(queryAsset);
  const {data} = queryResult;

  const onChange = (e: React.FormEvent<HTMLInputElement>) => {
    if (onToggleChecked && e.target instanceof HTMLInputElement) {
      const {checked} = e.target;
      const shiftKey =
        e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
      onToggleChecked({checked, shiftKey});
    }
  };

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
      <RowGrid
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        $showRepoColumn={showRepoColumn}
      >
        {showCheckboxColumn ? (
          <RowCell>
            <Checkbox checked={checked} onChange={onChange} />
          </RowCell>
        ) : null}
        <RowCell>
          <Box flex={{alignItems: 'center'}}>
            <div style={{flex: 1, minWidth: 0}}>
              <AssetLink
                path={type === 'folder' || view === 'directory' ? path.slice(-1) : path}
                url={linkUrl}
                isGroup={type === 'folder'}
                icon={type}
                textStyle="middle-truncate"
              />
            </div>
            {asset?.definition && (
              <AssetComputeKindTag
                reduceColor
                reduceText
                definition={asset.definition}
                style={{position: 'relative'}}
              />
            )}
          </Box>
          <div
            style={{
              maxWidth: '100%',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            <Caption style={{color: Colors.Gray500, whiteSpace: 'nowrap'}}>
              {asset?.definition?.description}
            </Caption>
          </div>
        </RowCell>
        {showRepoColumn ? (
          <RowCell>
            {repoAddress ? (
              <Box
                flex={{direction: 'column', gap: 4}}
                style={{maxWidth: '100%', overflow: 'hidden'}}
              >
                <RepositoryLink repoAddress={repoAddress} showIcon showRefresh={false} />
                {asset?.definition && asset?.definition.groupName ? (
                  <Link
                    to={workspacePathFromAddress(
                      repoAddress,
                      `/asset-groups/${asset.definition.groupName}`,
                    )}
                  >
                    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                      <Icon color={Colors.Gray400} name="asset_group" />
                      {asset.definition.groupName}
                    </Box>
                  </Link>
                ) : null}
              </Box>
            ) : (
              <span>{'\u2013'}</span>
            )}
          </RowCell>
        ) : null}
        <RowCell>
          {asset?.definition?.partitionDefinition ? (
            <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 4}}>
              <PartitionCountLabels partitionStats={liveData?.partitionStats} />
              <Caption>{`${liveData?.partitionStats?.numPartitions.toLocaleString()} ${
                liveData?.partitionStats?.numPartitions === 1 ? 'partition' : 'partitions'
              }`}</Caption>
            </Box>
          ) : (
            <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 4}}>
              {asset?.definition ? (
                <Box
                  style={{whiteSpace: 'nowrap'}}
                  flex={{direction: 'row', alignItems: 'center', gap: 8}}
                >
                  {
                    buildAssetNodeStatusContent({
                      definition: asset.definition,
                      expanded: true,
                      liveData,
                    }).content
                  }
                </Box>
              ) : liveData?.lastMaterialization ? (
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
              ) : (
                <LoadingOrNone queryResult={queryResult} noneString={'\u2013'} />
              )}
              {liveData && (
                <StaleReasonsLabel assetKey={{path}} liveData={liveData} include="all" />
              )}
            </Box>
          )}
        </RowCell>
        <RowCell>
          {asset ? (
            <AssetActionMenu repoAddress={repoAddress} asset={asset} onWipe={onWipe} />
          ) : null}
        </RowCell>
      </RowGrid>
    </Row>
  );
};

export const VirtualizedAssetCatalogHeader: React.FC<{
  headerCheckbox: React.ReactNode;
  view: AssetViewType;
}> = ({headerCheckbox, view}) => {
  return (
    <Box
      border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
      style={{
        display: 'grid',
        gridTemplateColumns: TEMPLATE_COLUMNS_FOR_CATALOG,
        height: '32px',
        fontSize: '12px',
        color: Colors.Gray600,
      }}
    >
      <HeaderCell>{headerCheckbox}</HeaderCell>
      <HeaderCell>{view === 'flat' ? 'Asset name' : 'Asset key prefix'}</HeaderCell>
      <HeaderCell>Repository / Asset group</HeaderCell>
      <HeaderCell>Status</HeaderCell>
      <HeaderCell></HeaderCell>
    </Box>
  );
};

export const VirtualizedAssetHeader: React.FC<{
  nameLabel: React.ReactNode;
}> = ({nameLabel}) => {
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
      <HeaderCell>{nameLabel}</HeaderCell>
      <HeaderCell>Materialized</HeaderCell>
      <HeaderCell>Latest run</HeaderCell>
      <HeaderCell></HeaderCell>
    </Box>
  );
};

const RowGrid = styled(Box)<{$showRepoColumn: boolean}>`
  display: grid;
  grid-template-columns: ${({$showRepoColumn}) =>
    $showRepoColumn ? TEMPLATE_COLUMNS_FOR_CATALOG : TEMPLATE_COLUMNS};
  height: 100%;
`;

export const SINGLE_ASSET_QUERY = gql`
  query SingleAssetQuery($input: AssetKeyInput!) {
    assetOrError(assetKey: $input) {
      ... on Asset {
        id
        assetMaterializations(limit: 1) {
          runId
          timestamp
        }
        definition {
          id
          computeKind
          ...AssetNodeLiveFragment
        }
        ...AssetTableFragment
      }
    }
    assetsLatestInfo(assetKeys: [$input]) {
      ...AssetLatestInfoFragment
    }
  }

  ${ASSET_NODE_LIVE_FRAGMENT}
  ${ASSET_TABLE_FRAGMENT}
  ${ASSET_LATEST_INFO_FRAGMENT}
`;
