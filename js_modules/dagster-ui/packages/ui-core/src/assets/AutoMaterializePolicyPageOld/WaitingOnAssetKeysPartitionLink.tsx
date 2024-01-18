import * as React from 'react';

import {Box, ButtonLink, Caption, Tag} from '@dagster-io/ui-components';

import {sortAssetKeys} from '../../asset-graph/Utils';
import {AssetLink} from '../AssetLink';
import {AssetKey} from '../types';
import {AssetKeysDialog, AssetKeysDialogEmptyState, AssetKeysDialogHeader} from './AssetKeysDialog';
import {VirtualizedAssetPartitionListForDialog} from './VirtualizedAssetPartitionListForDialog';
import {useFilterPartitionNames} from './assetFilters';

interface Props {
  assetKeysByPartition: Record<string, AssetKey[]>;
}

export const WaitingOnAssetKeysPartitionLink = ({assetKeysByPartition}: Props) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [queryString, setQueryString] = React.useState('');
  const partitionNames = Object.keys(assetKeysByPartition);
  const count = partitionNames.length;
  const filteredPartitionNames = useFilterPartitionNames(partitionNames, queryString);

  const visiblePartitions = React.useMemo(() => {
    return Object.fromEntries(
      filteredPartitionNames.map((partitionName) => [
        partitionName,
        [...assetKeysByPartition[partitionName]!].sort(sortAssetKeys),
      ]),
    );
  }, [assetKeysByPartition, filteredPartitionNames]);

  return (
    <>
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
        <Tag intent="warning">{count === 1 ? `1 partition` : `${count} partitions`}</Tag>
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
            queryString={queryString}
            setQueryString={setQueryString}
            showSearch={count > 0}
            placeholder="Filter by partition…"
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
                assetCount === 1 ? `(Waiting on 1 asset)` : `(Waiting on ${assetCount} assets)`
              }
              renderItem={(item: AssetKey) => <AssetLink path={item.path} icon="asset" />}
            />
          )
        }
      />
    </>
  );
};
