import * as React from 'react';

import {Box, ButtonLink, Caption, Tag} from '@dagster-io/ui-components';

import {sortAssetKeys} from '../../asset-graph/Utils';
import {AssetLink} from '../AssetLink';
import {AssetKey} from '../types';
import {AssetKeysDialog, AssetKeysDialogEmptyState, AssetKeysDialogHeader} from './AssetKeysDialog';
import {VirtualizedAssetPartitionListForDialog} from './VirtualizedAssetPartitionListForDialog';
import {AssetDetailType, detailTypeToLabel} from './assetDetailUtils';
import {useFilterPartitionNames} from './assetFilters';

interface Props {
  updatedAssetKeys: Record<string, AssetKey[]>;
  willUpdateAssetKeys: Record<string, AssetKey[]>;
}

export const ParentUpdatedPartitionLink = ({updatedAssetKeys, willUpdateAssetKeys}: Props) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [queryString, setQueryString] = React.useState('');

  const partitionNames = React.useMemo(() => {
    return Array.from(
      new Set([...Object.keys(updatedAssetKeys), ...Object.keys(willUpdateAssetKeys)]),
    );
  }, [updatedAssetKeys, willUpdateAssetKeys]);

  const count = partitionNames.length;
  const filteredPartitionNames = useFilterPartitionNames(partitionNames, queryString);

  const visiblePartitions = React.useMemo(() => {
    return Object.fromEntries(
      filteredPartitionNames.map((partitionName) => {
        return [
          partitionName,
          [
            ...(updatedAssetKeys[partitionName] || []).sort(sortAssetKeys).map((assetKey) => ({
              assetKey,
              detailType: AssetDetailType.Updated,
            })),
            ...(willUpdateAssetKeys[partitionName] || []).sort(sortAssetKeys).map((assetKey) => ({
              assetKey,
              detailType: AssetDetailType.WillUpdate,
            })),
          ],
        ];
      }),
    );
  }, [updatedAssetKeys, willUpdateAssetKeys, filteredPartitionNames]);

  return (
    <>
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
        <Tag>{count === 1 ? `1 partition` : `${count} partitions`}</Tag>
        <ButtonLink onClick={() => setIsOpen(true)}>
          <Caption>View details</Caption>
        </ButtonLink>
      </Box>
      <AssetKeysDialog
        isOpen={isOpen}
        setIsOpen={setIsOpen}
        header={
          <AssetKeysDialogHeader
            title={count === 1 ? '1 partition' : `${count} partitions`}
            placeholder="Filter by partition…"
            queryString={queryString}
            setQueryString={setQueryString}
            showSearch={count > 0}
          />
        }
        content={
          queryString && !filteredPartitionNames.length ? (
            <AssetKeysDialogEmptyState
              title="No matching partitions"
              description={
                <>
                  No matching partitions for <strong>{queryString}</strong>
                </>
              }
            />
          ) : (
            <VirtualizedAssetPartitionListForDialog
              assetKeysByPartition={visiblePartitions}
              renderPartitionDetail={({assetCount}) =>
                assetCount === 1 ? `(1 parent updated)` : `(${assetCount} parents updated)`
              }
              renderItem={(item) => (
                <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                  <AssetLink path={item.assetKey.path} icon="asset" />
                  <span>({detailTypeToLabel(item.detailType)})</span>
                </Box>
              )}
            />
          )
        }
      />
    </>
  );
};
