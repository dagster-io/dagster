import {gql, RefetchQueriesFunction} from '@apollo/client';
import {
  Box,
  Button,
  Checkbox,
  Colors,
  Icon,
  MenuItem,
  Menu,
  Popover,
  Table,
  Mono,
  Tooltip,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePermissions} from '../app/Permissions';
import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {
  AssetLatestRunWithNotices,
  AssetRunLink,
  ComputeStatusNotice,
} from '../asset-graph/AssetNode';
import {LiveData, toGraphId} from '../asset-graph/Utils';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {RepositoryLink} from '../nav/RepositoryLink';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {AnchorButton} from '../ui/AnchorButton';
import {MenuLink} from '../ui/MenuLink';
import {markdownToPlaintext} from '../ui/markdownToPlaintext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {AssetLink} from './AssetLink';
import {AssetWipeDialog} from './AssetWipeDialog';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetTableFragment as Asset} from './types/AssetTableFragment';
import {AssetViewType} from './useAssetView';

type AssetKey = {path: string[]};

export const AssetTable = ({
  view,
  assets,
  actionBarComponents,
  refreshState,
  liveDataByNode,
  prefixPath,
  displayPathForAsset,
  maxDisplayCount,
  requery,
}: {
  view: AssetViewType;
  assets: Asset[];
  refreshState: QueryRefreshState;
  actionBarComponents: React.ReactNode;
  liveDataByNode: LiveData;
  prefixPath: string[];
  displayPathForAsset: (asset: Asset) => string[];
  maxDisplayCount?: number;
  requery?: RefetchQueriesFunction;
}) => {
  const [toWipe, setToWipe] = React.useState<AssetKey[] | undefined>();
  const {canWipeAssets} = usePermissions();

  const groupedByFirstComponent: {[pathComponent: string]: Asset[]} = {};

  assets.forEach((asset) => {
    const displayPathKey = JSON.stringify(displayPathForAsset(asset));
    groupedByFirstComponent[displayPathKey] = [
      ...(groupedByFirstComponent[displayPathKey] || []),
      asset,
    ];
  });

  const [{checkedIds: checkedPaths}, {onToggleFactory, onToggleAll}] = useSelectionReducer(
    Object.keys(groupedByFirstComponent),
  );

  const checkedAssets: Asset[] = [];
  const checkedPathsOnscreen: string[] = [];

  const pageDisplayPathKeys = Object.keys(groupedByFirstComponent).sort().slice(0, maxDisplayCount);
  pageDisplayPathKeys.forEach((pathKey) => {
    if (checkedPaths.has(pathKey)) {
      checkedPathsOnscreen.push(pathKey);
      checkedAssets.push(...(groupedByFirstComponent[pathKey] || []));
    }
  });

  return (
    <Box flex={{direction: 'column'}}>
      <Box flex={{alignItems: 'center', gap: 12}} padding={{vertical: 8, left: 24, right: 12}}>
        {actionBarComponents}
        <div style={{flex: 1}} />
        <QueryRefreshCountdown refreshState={refreshState} />

        <Box flex={{alignItems: 'center', gap: 8}}>
          {checkedAssets.some((c) => !c.definition) ? (
            <Tooltip content="One or more selected assets are not software-defined and cannot be launched directly.">
              <Button intent="primary" icon={<Icon name="materialization" />} disabled>
                {checkedAssets.length > 1 ? `Materialize (${checkedAssets.length})` : 'Materialize'}
              </Button>
            </Tooltip>
          ) : (
            <LaunchAssetExecutionButton assetKeys={checkedAssets.map((c) => c.key)} />
          )}
          <MoreActionsDropdown selected={checkedAssets} clearSelection={() => onToggleAll(false)} />
        </Box>
      </Box>
      <Table>
        <thead>
          <tr>
            <th style={{width: 42, paddingTop: 0, paddingBottom: 0}}>
              <Checkbox
                indeterminate={
                  checkedPathsOnscreen.length > 0 &&
                  checkedPathsOnscreen.length !== pageDisplayPathKeys.length
                }
                checked={checkedPathsOnscreen.length === pageDisplayPathKeys.length}
                onChange={(e) => {
                  if (e.target instanceof HTMLInputElement) {
                    onToggleAll(checkedPathsOnscreen.length !== pageDisplayPathKeys.length);
                  }
                }}
              />
            </th>
            <th>{view === 'directory' ? 'Asset Key Prefix' : 'Asset Key'}</th>
            <th style={{width: 340}}>Defined In</th>
            <th style={{width: 265}}>Materialized</th>
            <th style={{width: 115}}>Latest Run</th>
            <th style={{width: 80}}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {pageDisplayPathKeys.length ? (
            pageDisplayPathKeys.map((pathStr, idx) => {
              return (
                <AssetEntryRow
                  key={idx}
                  prefixPath={prefixPath}
                  path={JSON.parse(pathStr)}
                  assets={groupedByFirstComponent[pathStr] || []}
                  liveDataByNode={liveDataByNode}
                  isSelected={checkedPaths.has(pathStr)}
                  onToggleChecked={onToggleFactory(pathStr)}
                  onWipe={(assets: Asset[]) => setToWipe(assets.map((asset) => asset.key))}
                  canWipe={canWipeAssets.enabled}
                />
              );
            })
          ) : (
            <AssetEmptyRow />
          )}
        </tbody>
      </Table>
      <AssetWipeDialog
        assetKeys={toWipe || []}
        isOpen={!!toWipe}
        onClose={() => setToWipe(undefined)}
        onComplete={() => setToWipe(undefined)}
        requery={requery}
      />
    </Box>
  );
};

const AssetEmptyRow = () => {
  return (
    <tr>
      <td colSpan={6}>
        <Box flex={{justifyContent: 'center', alignItems: 'center'}}>
          <Box margin={{left: 8}}>No assets to display</Box>
        </Box>
      </td>
    </tr>
  );
};

const AssetEntryRow: React.FC<{
  prefixPath: string[];
  path: string[];
  isSelected: boolean;
  onToggleChecked: (values: {checked: boolean; shiftKey: boolean}) => void;
  assets: Asset[];
  liveDataByNode: LiveData;
  onWipe: (assets: Asset[]) => void;
  canWipe?: boolean;
}> = React.memo(
  ({prefixPath, path, assets, isSelected, onToggleChecked, onWipe, canWipe, liveDataByNode}) => {
    const fullPath = [...prefixPath, ...path];
    const linkUrl = assetDetailsPathForKey({path: fullPath});

    const isGroup = assets.length > 1 || fullPath.join('/') !== assets[0].key.path.join('/');
    const asset = !isGroup ? assets[0] : null;

    const onChange = (e: React.FormEvent<HTMLInputElement>) => {
      if (e.target instanceof HTMLInputElement) {
        const {checked} = e.target;
        const shiftKey =
          e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
        onToggleChecked({checked, shiftKey});
      }
    };

    const liveData = asset && liveDataByNode[toGraphId(asset.key)];
    const repoAddress = asset?.definition
      ? buildRepoAddress(
          asset.definition.repository.name,
          asset.definition.repository.location.name,
        )
      : null;

    return (
      <tr>
        <td style={{paddingRight: 8}}>
          <Checkbox checked={isSelected} onChange={onChange} />
        </td>
        <td>
          <AssetLink
            path={path}
            url={linkUrl}
            isGroup={isGroup}
            icon={isGroup ? 'folder' : asset?.definition ? 'asset' : 'asset_non_sda'}
          />
          <Description>
            {asset?.definition &&
              asset.definition.description &&
              markdownToPlaintext(asset.definition.description).split('\n')[0]}
          </Description>
        </td>
        <td>
          {repoAddress && (
            <Box flex={{direction: 'column', gap: 4}}>
              <RepositoryLink showIcon showRefresh={false} repoAddress={repoAddress} />
              {asset?.definition && asset?.definition.groupName ? (
                <Link
                  to={workspacePathFromAddress(
                    repoAddress,
                    `/asset-groups/${asset.definition.groupName}`,
                  )}
                >
                  <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                    <Icon color={Colors.Gray400} name="asset_group" /> {asset.definition.groupName}
                  </Box>
                </Link>
              ) : undefined}
            </Box>
          )}
        </td>
        <td>
          {liveData ? (
            <Box flex={{gap: 8, alignItems: 'center'}}>
              {liveData.lastMaterialization ? (
                <Mono style={{flex: 1}}>
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
                </Mono>
              ) : (
                <span>–</span>
              )}
              <ComputeStatusNotice computeStatus={liveData?.computeStatus} />
            </Box>
          ) : undefined}
        </td>
        <td>
          {liveData && (
            <Mono>
              <AssetLatestRunWithNotices liveData={liveData} />
            </Mono>
          )}
        </td>
        <td>
          {asset ? (
            <Box flex={{gap: 8, alignItems: 'center'}}>
              <AnchorButton to={assetDetailsPathForKey({path})}>View details</AnchorButton>
              <Popover
                position="bottom-right"
                content={
                  <Menu>
                    <MenuLink
                      text="Show in group"
                      to={
                        repoAddress && asset.definition?.groupName
                          ? workspacePathFromAddress(
                              repoAddress,
                              `/asset-groups/${asset.definition.groupName}`,
                            )
                          : ''
                      }
                      disabled={!asset?.definition}
                      icon="asset_group"
                    />
                    <MenuLink
                      text="View neighbors"
                      to={assetDetailsPathForKey(
                        {path},
                        {view: 'lineage', lineageScope: 'neighbors'},
                      )}
                      disabled={!asset?.definition}
                      icon="graph_neighbors"
                    />
                    <MenuLink
                      text="View upstream assets"
                      to={assetDetailsPathForKey(
                        {path},
                        {view: 'lineage', lineageScope: 'upstream'},
                      )}
                      disabled={!asset?.definition}
                      icon="graph_upstream"
                    />
                    <MenuLink
                      text="View downstream assets"
                      to={assetDetailsPathForKey(
                        {path},
                        {view: 'lineage', lineageScope: 'downstream'},
                      )}
                      disabled={!asset?.definition}
                      icon="graph_downstream"
                    />
                    <MenuItem
                      text="Wipe materializations"
                      icon="delete"
                      disabled={!canWipe}
                      intent="danger"
                      onClick={() => canWipe && onWipe(assets)}
                    />
                  </Menu>
                }
              >
                <Button icon={<Icon name="expand_more" />} />
              </Popover>
            </Box>
          ) : (
            <span />
          )}
        </td>
      </tr>
    );
  },
);

const MoreActionsDropdown: React.FC<{
  selected: Asset[];
  clearSelection: () => void;
  requery?: RefetchQueriesFunction;
}> = React.memo(({selected, clearSelection, requery}) => {
  const [showBulkWipeDialog, setShowBulkWipeDialog] = React.useState<boolean>(false);
  const {canWipeAssets} = usePermissions();

  if (!canWipeAssets.enabled) {
    return null;
  }

  const disabled = selected.length === 0;

  return (
    <>
      <Popover
        position="bottom-right"
        content={
          <Menu>
            <MenuItem
              text="Wipe materializations"
              onClick={() => setShowBulkWipeDialog(true)}
              icon={<Icon name="delete" color={disabled ? Colors.Gray600 : Colors.Red500} />}
              disabled={disabled}
              intent="danger"
            />
          </Menu>
        }
      >
        <Button icon={<Icon name="expand_more" />} />
      </Popover>
      <AssetWipeDialog
        assetKeys={selected.map((asset) => asset.key)}
        isOpen={showBulkWipeDialog}
        onClose={() => setShowBulkWipeDialog(false)}
        onComplete={() => {
          setShowBulkWipeDialog(false);
          clearSelection();
        }}
        requery={requery}
      />
    </>
  );
});

export const ASSET_TABLE_DEFINITION_FRAGMENT = gql`
  fragment AssetTableDefinitionFragment on AssetNode {
    id
    groupName
    partitionDefinition
    description
    repository {
      id
      name
      location {
        id
        name
      }
    }
  }
`;

export const ASSET_TABLE_FRAGMENT = gql`
  fragment AssetTableFragment on Asset {
    __typename
    id
    key {
      path
    }
    definition {
      id
      ...AssetTableDefinitionFragment
    }
  }
  ${ASSET_TABLE_DEFINITION_FRAGMENT}
`;

const Description = styled.div`
  color: ${Colors.Gray800};
  font-size: 14px;
`;
