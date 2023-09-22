import {ButtonLink} from '@dagster-io/ui-components';
import * as React from 'react';

import {VirtualizedItemListForDialog} from '../../ui/VirtualizedItemListForDialog';
import {AssetLink} from '../AssetLink';
import {AssetKey} from '../types';

import {AssetKeysDialog, AssetKeysDialogEmptyState, AssetKeysDialogHeader} from './AssetKeysDialog';
import {useFilterAssetKeys} from './assetFilters';

interface Props {
  assetKeys: AssetKey[];
}

export const WaitingOnAssetKeysLink = ({assetKeys}: Props) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [queryString, setQueryString] = React.useState('');
  const count = assetKeys.length;
  const filteredAssetKeys = useFilterAssetKeys(assetKeys, queryString);

  return (
    <>
      <ButtonLink onClick={() => setIsOpen(true)}>
        {count === 1 ? 'Waiting on 1 asset' : `Waiting on ${count} assets`}
      </ButtonLink>
      <AssetKeysDialog
        isOpen={isOpen}
        setIsOpen={setIsOpen}
        header={
          <AssetKeysDialogHeader
            title={count === 1 ? '1 asset' : `${count} assets`}
            queryString={queryString}
            setQueryString={setQueryString}
            showSearch={count > 0}
            placeholder="Filter by asset key…"
          />
        }
        content={
          queryString && !filteredAssetKeys.length ? (
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
              renderItem={(item: AssetKey) => <AssetLink path={item.path} icon="asset" />}
            />
          )
        }
      />
    </>
  );
};
