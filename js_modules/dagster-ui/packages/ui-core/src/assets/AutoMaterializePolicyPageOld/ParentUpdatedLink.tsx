import {ButtonLink, Box} from '@dagster-io/ui-components';
import * as React from 'react';

import {sortAssetKeys} from '../../asset-graph/Utils';
import {VirtualizedItemListForDialog} from '../../ui/VirtualizedItemListForDialog';
import {AssetLink} from '../AssetLink';
import {AssetKey} from '../types';

import {AssetKeysDialog, AssetKeysDialogEmptyState, AssetKeysDialogHeader} from './AssetKeysDialog';
import {AssetDetailType, detailTypeToLabel} from './assetDetailUtils';
import {useFilterAssetKeys} from './assetFilters';

type AssetKeyDetail = {assetKey: AssetKey; detailType: AssetDetailType};

interface Props {
  updatedAssetKeys: AssetKey[];
  willUpdateAssetKeys: AssetKey[];
}

export const ParentUpdatedLink = ({updatedAssetKeys, willUpdateAssetKeys}: Props) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [queryString, setQueryString] = React.useState('');
  const count = updatedAssetKeys.length + willUpdateAssetKeys.length;

  const filteredUpdatedAssetKeys = useFilterAssetKeys(updatedAssetKeys, queryString);
  const filteredWillUpdateAssetKeys = useFilterAssetKeys(willUpdateAssetKeys, queryString);
  const filteredCount = filteredUpdatedAssetKeys.length + filteredWillUpdateAssetKeys.length;

  const filteredAssetKeys: AssetKeyDetail[] = React.useMemo(() => {
    return [
      ...[...filteredUpdatedAssetKeys].sort(sortAssetKeys).map((assetKey) => ({
        assetKey,
        detailType: AssetDetailType.Updated,
      })),
      ...[...filteredWillUpdateAssetKeys].sort(sortAssetKeys).map((assetKey) => ({
        assetKey,
        detailType: AssetDetailType.WillUpdate,
      })),
    ];
  }, [filteredUpdatedAssetKeys, filteredWillUpdateAssetKeys]);

  return (
    <>
      <ButtonLink onClick={() => setIsOpen(true)}>
        {count === 1 ? '1 parent updated' : `${count} parents updated`}
      </ButtonLink>
      <AssetKeysDialog
        isOpen={isOpen}
        setIsOpen={setIsOpen}
        header={
          <AssetKeysDialogHeader
            title={count === 1 ? '1 asset' : `${count} assets`}
            showSearch={count > 0}
            placeholder="Filter by asset key…"
            queryString={queryString}
            setQueryString={setQueryString}
          />
        }
        content={
          queryString && !filteredCount ? (
            <AssetKeysDialogEmptyState
              title="No matching asset keys"
              description={
                <>
                  No matching asset keys for <strong>{queryString}</strong>
                </>
              }
            />
          ) : (
            <VirtualizedItemListForDialog
              items={filteredAssetKeys}
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
