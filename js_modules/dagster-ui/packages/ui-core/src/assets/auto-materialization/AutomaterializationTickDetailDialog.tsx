import {gql, useQuery} from '@apollo/client';
import {Box, Subtitle2, Caption, Icon, Spinner, Colors} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {Timestamp} from '../../app/time/Timestamp';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {AssetKeyInput, InstigationTickStatus} from '../../graphql/types';
import {TickDetailSummary} from '../../instigation/TickDetailsDialog';
import {HeaderCell, Inner, Row, RowCell} from '../../ui/VirtualizedTable';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {AssetLink} from '../AssetLink';
import {
  AssetKeysDialog,
  AssetKeysDialogHeader,
  AssetKeysDialogEmptyState,
} from '../AutoMaterializePolicyPage/AssetKeysDialog';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';

import {AssetDaemonTickFragment} from './types/AssetDaemonTicksQuery.types';
import {
  AssetGroupAndLocationQuery,
  AssetGroupAndLocationQueryVariables,
} from './types/AutomaterializationTickDetailDialog.types';
const TEMPLATE_COLUMNS = '30% 17% 53%';

export const AutomaterializationTickDetailDialog = React.memo(
  ({
    tick,
    isOpen,
    close,
  }: {
    tick: AssetDaemonTickFragment | null;
    isOpen: boolean;
    close: () => void;
  }) => {
    const [queryString, setQueryString] = React.useState('');

    const filteredAssetKeys = React.useMemo(
      () =>
        tick
          ? tick.requestedAssetKeys.filter((assetKey) =>
              assetKey.path.join('/').includes(queryString),
            )
          : [],
      [tick, queryString],
    );

    const count = tick?.requestedAssetKeys.length || 0;

    const parentRef = React.useRef<HTMLDivElement | null>(null);
    const rowVirtualizer = useVirtualizer({
      count: filteredAssetKeys.length,
      getScrollElement: () => parentRef.current,
      estimateSize: () => 34,
      overscan: 10,
    });
    const totalHeight = rowVirtualizer.getTotalSize();
    const items = rowVirtualizer.getVirtualItems();

    const assetKeyToPartitionsMap = React.useMemo(() => {
      const map: Record<string, string[]> = {};
      tick?.requestedMaterializationsForAssets.forEach(({assetKey, partitionKeys}) => {
        map[tokenForAssetKey(assetKey)] = partitionKeys;
      });
      return map;
    }, [tick?.requestedMaterializationsForAssets]);

    const content = React.useMemo(() => {
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
        <div style={{overflow: 'scroll'}} ref={parentRef}>
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
            <HeaderCell>Asset</HeaderCell>
            <HeaderCell>Group</HeaderCell>
            <HeaderCell>Result</HeaderCell>
          </Box>
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
    }, [assetKeyToPartitionsMap, filteredAssetKeys, items, queryString, tick, totalHeight]);

    return (
      <AssetKeysDialog
        isOpen={isOpen}
        setIsOpen={close}
        height={400}
        header={
          <AssetKeysDialogHeader
            title={
              tick ? (
                <div>
                  <Timestamp timestamp={{unix: tick.timestamp}} timeFormat={{showTimezone: true}} />
                </div>
              ) : (
                ''
              )
            }
            showSearch={count > 0}
            placeholder="Filter by asset key…"
            queryString={queryString}
            setQueryString={setQueryString}
          />
        }
        content={
          <div
            style={{
              display: 'grid',
              gridTemplateRows: 'auto auto minmax(0, 1fr)',
              height: '100%',
            }}
          >
            <Box padding={{vertical: 12, horizontal: 24}} border="bottom">
              {tick ? <TickDetailSummary tick={tick} /> : null}
            </Box>
            {tick?.status === InstigationTickStatus.STARTED ? null : (
              <>
                <Box
                  padding={{vertical: 12, horizontal: 24}}
                  border={filteredAssetKeys.length > 0 ? undefined : 'bottom'}
                >
                  <Subtitle2>Materializations requested</Subtitle2>
                </Box>
                {content}
              </>
            )}
          </div>
        }
      />
    );
  },
);

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
  const {data} = useQuery<AssetGroupAndLocationQuery, AssetGroupAndLocationQueryVariables>(
    ASSET_GROUP_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {
        assetKey: {path: assetKey.path},
      },
    },
  );
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
              view: 'auto-materialize-history',
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
