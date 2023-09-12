import {Box, Button, Colors, Dialog, DialogFooter, Icon, Tag} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {displayNameForAssetKey} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {globalAssetGraphPathForAssetsAndDescendants} from '../assets/globalAssetGraphPathToString';
import {AssetKey} from '../assets/types';
import {TagActionsPopover} from '../ui/TagActions';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';

export const AssetKeyTagCollection: React.FC<{
  assetKeys: AssetKey[] | null;
  modalTitle?: string;
  useTags?: boolean;
}> = React.memo(({assetKeys, useTags, modalTitle = 'Assets in Run'}) => {
  const [showMore, setShowMore] = React.useState(false);

  if (!assetKeys || !assetKeys.length) {
    return null;
  }

  const showMoreDialog =
    assetKeys.length > 1 ? (
      <Dialog
        title={modalTitle}
        onClose={() => setShowMore(false)}
        style={{minWidth: '400px', maxWidth: '80vw', maxHeight: '70vh'}}
        isOpen={showMore}
      >
        <div style={{height: '340px', overflow: 'hidden'}}>
          <VirtualizedItemListForDialog
            items={assetKeys}
            renderItem={(assetKey: AssetKey) => (
              <Link to={assetDetailsPathForKey(assetKey)}>{displayNameForAssetKey(assetKey)}</Link>
            )}
          />
        </div>
        <DialogFooter topBorder>
          <Button autoFocus onClick={() => setShowMore(false)}>
            Done
          </Button>
        </DialogFooter>
      </Dialog>
    ) : undefined;

  if (assetKeys.length === 1) {
    // Outer span ensures the popover target is in the right place if the
    // parent is a flexbox.
    const assetKey = assetKeys[0]!;
    return (
      <span style={{lineHeight: 0}}>
        <TagActionsPopover
          data={{key: '', value: ''}}
          actions={[
            {
              label: 'View asset',
              to: assetDetailsPathForKey(assetKey),
            },
            {
              label: 'View downstream lineage',
              to: assetDetailsPathForKey(assetKey, {
                view: 'lineage',
                lineageScope: 'downstream',
              }),
            },
          ]}
        >
          {useTags ? (
            <Tag intent="none" interactive icon="asset">
              {displayNameForAssetKey(assetKey)}
            </Tag>
          ) : (
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <Icon color={Colors.Gray400} name="asset" size={16} />
              {displayNameForAssetKey(assetKey)}
            </Box>
          )}
        </TagActionsPopover>
      </span>
    );
  }

  return (
    <span style={{lineHeight: 0}}>
      <TagActionsPopover
        data={{key: '', value: ''}}
        actions={[
          {
            label: 'View list',
            onClick: () => setShowMore(true),
          },
          {
            label: 'View downstream lineage',
            to: globalAssetGraphPathForAssetsAndDescendants(assetKeys),
          },
        ]}
      >
        {useTags ? (
          <Tag intent="none" icon="asset">
            {assetKeys.length} assets
          </Tag>
        ) : (
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center', display: 'inline-flex'}}>
            <Icon color={Colors.Gray400} name="asset" size={16} />
            <Box style={{flex: 1}} flex={{wrap: 'wrap', display: 'inline-flex'}}>
              {`${assetKeys.length} assets`}
            </Box>
          </Box>
        )}
      </TagActionsPopover>
      {showMoreDialog}
    </span>
  );
});
