import {
  Box,
  Caption,
  Colors,
  HeaderCell,
  Icon,
  Inner,
  Row,
  RowCell,
  Spinner,
  Subtitle2,
  TextInput,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useMemo, useRef, useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {gql, useQuery} from '../apollo-client';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetLink} from '../assets/AssetLink';
import {AssetKeysDialogEmptyState} from '../assets/AutoMaterializePolicyPage/AssetKeysDialog';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetDaemonTickFragment} from '../assets/auto-materialization/types/AssetDaemonTicksQuery.types';
import {
  AssetGroupAndLocationQuery,
  AssetGroupAndLocationQueryVariables,
} from '../assets/auto-materialization/types/AutomaterializationTickDetailDialog.types';
import {AssetKeyInput} from '../graphql/types';
import {HeaderRow} from '../ui/VirtualizedTable';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../workspace/workspacePath';

const TEMPLATE_COLUMNS = '30% 17% 53%';

export const TickMaterializationsTable = ({
  tick,
}: {
  tick: Pick<
    AssetDaemonTickFragment,
    'requestedAssetKeys' | 'requestedMaterializationsForAssets' | 'autoMaterializeAssetEvaluationId'
  > | null;
}) => {
  const [queryString, setQueryString] = useState('');

  const filteredAssetKeys = useMemo(
    () =>
      tick
        ? tick.requestedAssetKeys.filter((assetKey) =>
            assetKey.path.join('/').includes(queryString),
          )
        : [],
    [tick, queryString],
  );

  const parentRef = useRef<HTMLDivElement | null>(null);
  const rowVirtualizer = useVirtualizer({
    count: filteredAssetKeys.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 34,
    overscan: 10,
  });
  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  const assetKeyToPartitionsMap = useMemo(() => {
    const map: Record<string, string[]> = {};
    tick?.requestedMaterializationsForAssets.forEach(({assetKey, partitionKeys}) => {
      map[tokenForAssetKey(assetKey)] = partitionKeys;
    });
    return map;
  }, [tick?.requestedMaterializationsForAssets]);

  const content = () => {
    if (queryString && !filteredAssetKeys.length) {
      return (
        <AssetKeysDialogEmptyState
          title="No matching asset keys"
          description={
            <>
              No matching asset keys for <strong>{queryString}</strong>
            </>
          }
        />
      );
    }
    if (!tick?.requestedAssetKeys.length) {
      return (
        <Box padding={{vertical: 12, horizontal: 24}}>
          <Caption color={Colors.textLight()}>None</Caption>
        </Box>
      );
    }
    return (
      <div style={{overflow: 'scroll', flex: 1}} ref={parentRef}>
        <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
          <HeaderCell>Asset</HeaderCell>
          <HeaderCell>Group</HeaderCell>
          <HeaderCell>Result</HeaderCell>
        </HeaderRow>
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            const assetKey = filteredAssetKeys[index]!;
            return (
              <AssetDetailRow
                key={key}
                $height={size}
                $start={start}
                assetKey={assetKey}
                partitionKeys={assetKeyToPartitionsMap[tokenForAssetKey(assetKey)]}
                evaluationId={tick.autoMaterializeAssetEvaluationId!}
              />
            );
          })}
        </Inner>
      </div>
    );
  };

  return (
    <Box style={{height: '500px'}} flex={{direction: 'column'}}>
      <Box
        padding={{vertical: 12, horizontal: 24}}
        flex={{justifyContent: 'space-between', alignItems: 'center'}}
        border="bottom"
      >
        <Subtitle2>Requested materializations</Subtitle2>
        <TextInput
          icon="search"
          value={queryString}
          onChange={(e) => setQueryString(e.target.value)}
          placeholder="Filter by asset key…"
          style={{width: '252px'}}
        />
      </Box>
      {content()}
    </Box>
  );
};

const AssetDetailRow = ({
  $start,
  $height,
  assetKey,
  partitionKeys,
  evaluationId,
}: {
  $start: number;
  $height: number;
  assetKey: AssetKeyInput;
  partitionKeys?: string[];
  evaluationId: number;
}) => {
  const numMaterializations = partitionKeys?.length || 1;
  const queryResult = useQuery<AssetGroupAndLocationQuery, AssetGroupAndLocationQueryVariables>(
    ASSET_GROUP_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {
        assetKey: {path: assetKey.path},
      },
    },
  );
  const {data} = queryResult;

  const asset = data?.assetOrError.__typename === 'Asset' ? data.assetOrError : null;
  const definition = asset?.definition;
  const repoAddress = definition
    ? buildRepoAddress(definition.repository.name, definition.repository.location.name)
    : null;
  return (
    <Row $start={$start} $height={$height}>
      <RowGrid border="bottom">
        <RowCell>
          <AssetLink path={assetKey.path} icon="asset" textStyle="middle-truncate" />
        </RowCell>
        <RowCell>
          {data ? (
            definition && definition.groupName && repoAddress ? (
              <Link
                to={workspacePathFromAddress(repoAddress, `/asset-groups/${definition.groupName}`)}
              >
                <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                  <Icon color={Colors.textLight()} name="asset_group" />
                  {definition.groupName}
                </Box>
              </Link>
            ) : (
              <Caption color={Colors.textLight()}>Asset not found</Caption>
            )
          ) : (
            <Spinner purpose="body-text" />
          )}
        </RowCell>
        <RowCell>
          <Link
            to={assetDetailsPathForKey(assetKey, {
              view: 'automation',
              evaluation: `${evaluationId}`,
            })}
          >
            {numMaterializations} materialization{numMaterializations === 1 ? '' : 's'} requested
          </Link>
        </RowCell>
      </RowGrid>
    </Row>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
  > * {
    justify-content: center;
  }
`;

const ASSET_GROUP_QUERY = gql`
  query AssetGroupAndLocationQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        definition {
          id
          groupName
          repository {
            id
            name
            location {
              id
              name
            }
          }
        }
      }
    }
  }
`;
