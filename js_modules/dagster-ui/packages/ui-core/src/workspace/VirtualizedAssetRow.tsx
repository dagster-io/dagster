import {Box, Caption, Checkbox, Colors, Icon, Skeleton} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {RepoAddress} from './types';
import {
  SingleNonSdaAssetQuery,
  SingleNonSdaAssetQueryVariables,
} from './types/VirtualizedAssetRow.types';
import {workspacePathFromAddress} from './workspacePath';
import {gql, useQuery} from '../apollo-client';
import {useAssetsLiveData} from '../asset-data/AssetLiveDataProvider';
import {buildAssetNodeStatusContent} from '../asset-graph/AssetNodeStatusContent';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {MISSING_LIVE_DATA, tokenForAssetKey} from '../asset-graph/Utils';
import {AssetActionMenu} from '../assets/AssetActionMenu';
import {AssetLink} from '../assets/AssetLink';
import {PartitionCountLabels, partitionCountString} from '../assets/AssetNodePartitionCounts';
import {StaleReasonsLabel} from '../assets/Stale';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetTableDefinitionFragment} from '../assets/types/AssetTableFragment.types';
import {AssetViewType} from '../assets/useAssetView';
import {AssetKind} from '../graph/KindTags';
import {AssetKeyInput} from '../graphql/types';
import {RepositoryLink} from '../nav/RepositoryLink';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {testId} from '../testing/testId';
import {StaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';
import {HeaderCell, HeaderRow, Row, RowCell} from '../ui/VirtualizedTable';

const TEMPLATE_COLUMNS = '1.3fr 1fr 80px';
const TEMPLATE_COLUMNS_FOR_CATALOG = '76px 1.3fr 1.3fr 1.3fr 80px';

interface AssetRowProps {
  path: string[];
  definition: AssetTableDefinitionFragment | null;

  checked: boolean;
  type: 'folder' | 'asset' | 'asset_non_sda';
  view?: AssetViewType;
  onToggleChecked: (values: {checked: boolean; shiftKey: boolean}) => void;
  showCheckboxColumn: boolean;
  showRepoColumn: boolean;
  repoAddress: RepoAddress | null;
  height: number;
  start: number;
  onRefresh: () => void;
  kindFilter?: StaticSetFilter<string>;
}

export const VirtualizedAssetRow = (props: AssetRowProps) => {
  const {
    path,
    definition,
    type,
    repoAddress,
    start,
    height,
    checked,
    onToggleChecked,
    onRefresh,
    showCheckboxColumn = false,
    showRepoColumn,
    view = 'flat',
    kindFilter,
  } = props;

  const liveData = useLiveDataOrLatestMaterializationDebounced(path, type);
  const linkUrl = assetDetailsPathForKey(
    {path},
    {
      view: type === 'folder' ? 'folder' : undefined,
    },
  );

  const onChange = (e: React.FormEvent<HTMLInputElement>) => {
    if (onToggleChecked && e.target instanceof HTMLInputElement) {
      const {checked} = e.target;
      const shiftKey =
        e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
      onToggleChecked({checked, shiftKey});
    }
  };
  const kinds = definition?.kinds;

  return (
    <Row $height={height} $start={start} data-testid={testId(`row-${tokenForAssetKey({path})}`)}>
      <RowGrid border="bottom" $showRepoColumn={showRepoColumn}>
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
            {kinds && (
              <>
                {kinds?.map((kind) => (
                  <AssetKind
                    key={kind}
                    reduceColor
                    reduceText
                    kind={kind}
                    style={{position: 'relative'}}
                    currentPageFilter={kindFilter}
                  />
                ))}
              </>
            )}
          </Box>
          <div
            style={{
              maxWidth: '100%',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            <Caption style={{color: Colors.textLight(), whiteSpace: 'nowrap'}}>
              {definition?.description}
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
                {definition && definition.groupName ? (
                  <Link
                    to={workspacePathFromAddress(
                      repoAddress,
                      `/asset-groups/${definition.groupName}`,
                    )}
                  >
                    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                      <Icon color={Colors.accentGray()} name="asset_group" />
                      {definition.groupName}
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
          {definition?.partitionDefinition && definition?.isMaterializable ? (
            <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 4}}>
              <PartitionCountLabels partitionStats={liveData?.partitionStats} />
              <Caption>{partitionCountString(liveData?.partitionStats?.numPartitions)}</Caption>
            </Box>
          ) : (
            <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 4}}>
              {definition ? (
                <Box
                  style={{whiteSpace: 'nowrap'}}
                  flex={{direction: 'row', alignItems: 'center', gap: 8}}
                >
                  {
                    buildAssetNodeStatusContent({
                      assetKey: {path},
                      definition,
                      expanded: true,
                      liveData,
                    }).content
                  }
                </Box>
              ) : liveData?.lastMaterialization ? (
                <AssetRunLink
                  assetKey={{path}}
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
                <div style={{color: Colors.textLight()}}>
                  {!liveData && type !== 'folder' ? 'Loading' : '\u2013'}
                </div>
              )}
              {liveData && <StaleReasonsLabel assetKey={{path}} liveData={liveData} />}
            </Box>
          )}
        </RowCell>
        <RowCell>
          {type !== 'folder' ? (
            <AssetActionMenu
              path={path}
              definition={definition}
              repoAddress={repoAddress}
              onRefresh={onRefresh}
            />
          ) : null}
        </RowCell>
      </RowGrid>
    </Row>
  );
};

export const VirtualizedAssetCatalogHeader = ({
  headerCheckbox,
  view,
}: {
  headerCheckbox: React.ReactNode;
  view: AssetViewType;
}) => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS_FOR_CATALOG} sticky>
      <HeaderCell>{headerCheckbox}</HeaderCell>
      <HeaderCell>{view === 'flat' ? 'Asset name' : 'Asset key prefix'}</HeaderCell>
      <HeaderCell>Code location / Asset group</HeaderCell>
      <HeaderCell>Status</HeaderCell>
      <HeaderCell></HeaderCell>
    </HeaderRow>
  );
};

export const ShimmerRow = (props: {$height: number; $start: number; $showRepoColumn: boolean}) => (
  <Row {...props}>
    <RowGrid border="bottom" $showRepoColumn={props.$showRepoColumn}>
      <RowCell>
        <Skeleton $height={21} $width="45%" />
      </RowCell>
      <RowCell>
        <Skeleton $height={21} $width="45%" />
      </RowCell>
      <RowCell>
        <Skeleton $height={21} $width="45%" />
      </RowCell>
      {props.$showRepoColumn ? (
        <>
          <RowCell>
            <Skeleton $height={21} $width="45%" />
          </RowCell>
          <RowCell>
            <Skeleton $height={21} $width="45%" />
          </RowCell>
        </>
      ) : null}
    </RowGrid>
  </Row>
);

export const VirtualizedAssetHeader = ({nameLabel}: {nameLabel: React.ReactNode}) => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>{nameLabel}</HeaderCell>
      <HeaderCell>Status</HeaderCell>
      <HeaderCell></HeaderCell>
    </HeaderRow>
  );
};

const RowGrid = styled(Box)<{$showRepoColumn: boolean}>`
  display: grid;
  grid-template-columns: ${({$showRepoColumn}) =>
    $showRepoColumn ? TEMPLATE_COLUMNS_FOR_CATALOG : TEMPLATE_COLUMNS};
  height: 100%;
`;

const LIVE_QUERY_DELAY = 250;

/**
 * This hook maps through to `AssetLiveDataProvider` for the `asset` case and a per-row
 * query for the latest materialization for the `asset_non_sda` case.
 *
 * It uses internal state and `skip` to implement a debounce that prevents a ton of queries
 * as the user scans past rows. (The best way to skip the AssetLiveDataProvider work is
 * to pass it an empty array of asset keys.)
 */
export function useLiveDataOrLatestMaterializationDebounced(
  path: string[],
  type: 'folder' | 'asset' | 'asset_non_sda',
) {
  const [debouncedKeys, setDebouncedKeys] = React.useState<AssetKeyInput[]>([]);
  const debouncedKey = (debouncedKeys[0] || '') as AssetKeyInput;

  const {liveDataByNode} = useAssetsLiveData(type === 'asset' ? debouncedKeys : []);

  const skip = type !== 'asset_non_sda' || !debouncedKey;
  const queryResult = useQuery<SingleNonSdaAssetQuery, SingleNonSdaAssetQueryVariables>(
    SINGLE_NON_SDA_ASSET_QUERY,
    {
      skip,
      variables: {input: debouncedKey},
    },
  );
  const {data: nonSDAData} = queryResult;

  React.useEffect(() => {
    if (type === 'folder') {
      return;
    }
    const timer = setTimeout(() => {
      setDebouncedKeys(path ? [{path}] : []);
    }, LIVE_QUERY_DELAY);
    return () => clearTimeout(timer);
  }, [type, path]);

  if (type === 'asset') {
    return liveDataByNode[tokenForAssetKey({path})]!;
  }

  if (type === 'asset_non_sda') {
    return {
      ...MISSING_LIVE_DATA,
      lastMaterialization:
        nonSDAData?.assetOrError.__typename === 'Asset' &&
        nonSDAData.assetOrError.assetMaterializations[0]
          ? nonSDAData.assetOrError.assetMaterializations[0]
          : null,
    };
  }

  return null;
}

export const SINGLE_NON_SDA_ASSET_QUERY = gql`
  query SingleNonSDAAssetQuery($input: AssetKeyInput!) {
    assetOrError(assetKey: $input) {
      ... on Asset {
        id
        assetMaterializations(limit: 1) {
          runId
          timestamp
        }
      }
    }
  }
`;
