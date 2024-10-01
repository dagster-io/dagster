import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogFooter,
  Icon,
  MiddleTruncate,
  Tag,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {displayNameForAssetKey} from '../asset-graph/Utils';
import {
  assetDetailsPathForAssetCheck,
  assetDetailsPathForKey,
} from '../assets/assetDetailsPathForKey';
import {globalAssetGraphPathForAssetsAndDescendants} from '../assets/globalAssetGraphPathToString';
import {AssetKey} from '../assets/types';
import {TagActionsPopover} from '../ui/TagActions';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';
import {numberFormatter} from '../ui/formatters';

const renderItemAssetKey = (assetKey: AssetKey) => (
  <Link to={assetDetailsPathForKey(assetKey)} style={{display: 'block', width: '100%'}}>
    <MiddleTruncate text={displayNameForAssetKey(assetKey)} />
  </Link>
);

const renderItemAssetCheck = (assetCheck: Check) => (
  <Link to={assetDetailsPathForAssetCheck(assetCheck)} style={{display: 'block', width: '100%'}}>
    <MiddleTruncate text={labelForAssetCheck(assetCheck)} />
  </Link>
);

const labelForAssetCheck = (check: Check) => {
  return `${check.name} on ${displayNameForAssetKey(check.assetKey)}`;
};

function useShowMoreDialog<T>(
  dialogTitle: string,
  items: T[] | null,
  renderItem: (item: T) => React.ReactNode,
) {
  const [showMore, setShowMore] = React.useState(false);

  const dialog =
    !!items && items.length > 1 ? (
      <Dialog
        title={dialogTitle}
        onClose={() => setShowMore(false)}
        style={{minWidth: '400px', width: '50vw', maxWidth: '800px', maxHeight: '70vh'}}
        isOpen={showMore}
      >
        <div style={{height: '500px', overflow: 'hidden'}}>
          <VirtualizedItemListForDialog items={items} renderItem={renderItem} />
        </div>
        <DialogFooter topBorder>
          <Button intent="primary" autoFocus onClick={() => setShowMore(false)}>
            Done
          </Button>
        </DialogFooter>
      </Dialog>
    ) : undefined;

  return {dialog, showMore, setShowMore};
}

interface AssetKeyTagCollectionProps {
  assetKeys: AssetKey[] | null;
  dialogTitle?: string;
  useTags?: boolean;
}

export const AssetKeyTagCollection = React.memo((props: AssetKeyTagCollectionProps) => {
  const {assetKeys, useTags, dialogTitle = 'Assets in run'} = props;
  const {setShowMore, dialog} = useShowMoreDialog(dialogTitle, assetKeys, renderItemAssetKey);

  if (!assetKeys || !assetKeys.length) {
    return null;
  }

  if (assetKeys.length === 1) {
    // Outer span ensures the popover target is in the right place if the
    // parent is a flexbox.
    const assetKey = assetKeys[0]!;
    return (
      <TagActionsPopover
        data={{key: '', value: ''}}
        actions={[
          {
            label: 'View asset',
            to: assetDetailsPathForKey(assetKey),
          },
          {
            label: 'View lineage',
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
          <Link to={assetDetailsPathForKey(assetKey)}>
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <Icon color={Colors.accentGray()} name="asset" size={16} />
              {displayNameForAssetKey(assetKey)}
            </Box>
          </Link>
        )}
      </TagActionsPopover>
    );
  }

  return (
    <span style={useTags ? {} : {marginBottom: -4}}>
      <TagActionsPopover
        data={{key: '', value: ''}}
        actions={[
          {
            label: 'View list',
            onClick: () => setShowMore(true),
          },
          {
            label: 'View lineage',
            to: globalAssetGraphPathForAssetsAndDescendants(assetKeys),
          },
        ]}
      >
        {useTags ? (
          <Tag intent="none" icon="asset">
            {numberFormatter.format(assetKeys.length)} assets
          </Tag>
        ) : (
          <ButtonLink onClick={() => setShowMore(true)} underline="hover">
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center', display: 'inline-flex'}}>
              <Icon color={Colors.accentGray()} name="asset" size={16} />
              {`${numberFormatter.format(assetKeys.length)} assets`}
            </Box>
          </ButtonLink>
        )}
      </TagActionsPopover>
      {dialog}
    </span>
  );
});

type Check = {name: string; assetKey: AssetKey};

interface AssetCheckTagCollectionProps {
  assetChecks: Check[] | null;
  dialogTitle?: string;
  useTags?: boolean;
}

export const AssetCheckTagCollection = React.memo((props: AssetCheckTagCollectionProps) => {
  const {assetChecks, useTags, dialogTitle = 'Asset checks in run'} = props;
  const {setShowMore, dialog} = useShowMoreDialog(dialogTitle, assetChecks, renderItemAssetCheck);

  if (!assetChecks || !assetChecks.length) {
    return null;
  }

  if (assetChecks.length === 1) {
    // Outer span ensures the popover target is in the right place if the
    // parent is a flexbox.
    const check = assetChecks[0]!;
    return (
      <TagActionsPopover
        data={{key: '', value: ''}}
        actions={[{label: 'View asset check', to: assetDetailsPathForAssetCheck(check)}]}
      >
        {useTags ? (
          <Tag intent="none" interactive icon="asset_check">
            {labelForAssetCheck(check)}
          </Tag>
        ) : (
          <Link to={assetDetailsPathForAssetCheck(check)}>
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <Icon color={Colors.accentGray()} name="asset_check" size={16} />
              {labelForAssetCheck(check)}
            </Box>
          </Link>
        )}
      </TagActionsPopover>
    );
  }

  return (
    <>
      <TagActionsPopover
        data={{key: '', value: ''}}
        actions={[
          {
            label: 'View list',
            onClick: () => setShowMore(true),
          },
        ]}
      >
        {useTags ? (
          <Tag intent="none" icon="asset_check">
            {numberFormatter.format(assetChecks.length)} asset checks
          </Tag>
        ) : (
          <ButtonLink onClick={() => setShowMore(true)} underline="hover">
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center', display: 'inline-flex'}}>
              <Icon color={Colors.accentGray()} name="asset_check" size={16} />
              {`${numberFormatter.format(assetChecks.length)} asset checks`}
            </Box>
          </ButtonLink>
        )}
      </TagActionsPopover>
      {dialog}
    </>
  );
});
