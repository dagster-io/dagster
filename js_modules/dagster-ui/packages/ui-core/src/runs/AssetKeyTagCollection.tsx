import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogFooter,
  Icon,
  Tag,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {displayNameForAssetKey, tokenForAssetKey} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetKey} from '../assets/types';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';

const MAX_ASSET_TAGS = 3;

export const AssetKeyTagCollection: React.FC<{
  assetKeys: AssetKey[] | null;
  modalTitle?: string;
  useTags?: boolean;
}> = React.memo(({assetKeys, useTags, modalTitle = 'Assets in Run'}) => {
  const [showMore, setShowMore] = React.useState(false);

  if (!assetKeys || !assetKeys.length) {
    return null;
  }

  const assetCount = assetKeys.length;
  const displayed = assetCount <= MAX_ASSET_TAGS ? assetKeys : [];
  const hidden = assetCount - displayed.length;

  const showMoreDialog =
    hidden > 0 ? (
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

  if (useTags) {
    return (
      <>
        {displayed.map((assetKey, ii) => (
          <Link to={assetDetailsPathForKey(assetKey)} key={`${tokenForAssetKey(assetKey)}-${ii}`}>
            <Tag intent="none" interactive icon="asset">
              {displayNameForAssetKey(assetKey)}
            </Tag>
          </Link>
        ))}
        {hidden > 0 && (
          <ButtonLink onClick={() => setShowMore(true)}>
            <Tag intent="none" icon="asset">
              {hidden} assets
            </Tag>
          </ButtonLink>
        )}
        {showMoreDialog}
      </>
    );
  }

  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <Icon color={Colors.Gray400} name="asset" size={16} />
      <Box style={{flex: 1}} flex={{wrap: 'wrap', display: 'inline-flex'}}>
        {displayed.map((assetKey, idx) => (
          <Link
            to={assetDetailsPathForKey(assetKey)}
            key={tokenForAssetKey(assetKey)}
            style={{marginRight: 4}}
          >
            {`${displayNameForAssetKey(assetKey)}${idx < displayed.length - 1 ? ',' : ''}`}
          </Link>
        ))}

        {hidden > 0 && displayed.length > 0 ? (
          <ButtonLink onClick={() => setShowMore(true)}>{` + ${hidden} more`}</ButtonLink>
        ) : hidden > 0 ? (
          <ButtonLink onClick={() => setShowMore(true)}>{`${hidden} assets`}</ButtonLink>
        ) : undefined}
      </Box>
      {showMoreDialog}
    </Box>
  );
});
