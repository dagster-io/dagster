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
import useResizeObserver from '@react-hook/resize-observer';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {displayNameForAssetKey, tokenForAssetKey} from '../asset-graph/Utils';
import {
  labelForAssetCheck,
  renderItemAssetCheck,
  renderItemAssetKey,
  sortItemAssetCheck,
  sortItemAssetKey,
} from '../assets/AssetListUtils';
import {
  assetDetailsPathForAssetCheck,
  assetDetailsPathForKey,
} from '../assets/assetDetailsPathForKey';
import {globalAssetGraphPathForAssetsAndDescendants} from '../assets/globalAssetGraphPathToString';
import {AssetKey} from '../assets/types';
import {TagActionsPopover} from '../ui/TagActions';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';
import {numberFormatter} from '../ui/formatters';

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
  extraTags?: React.ReactNode[];
  maxRows?: number;
}

/** This hook returns a containerRef and a moreLabelRef. It expects you to populate
 * containerRef with children, with the last child being a "More" button. When your
 * container renders, children will be hidden until the container is not overflowing
 * its maxHeight.
 *
 * This hook waits for an animation frame but forces layout so you can't see it "trying"
 * different numbers of tags. To avoid seeing tags wrap while waiting for an animation
 * frame, place an `overflow: hidden` on the container.
 */
export function useAdjustChildVisibilityToFill(moreLabelFn: (count: number) => string | null) {
  const containerRef = React.createRef<HTMLDivElement>();
  const moreLabelRef = React.createRef<HTMLDivElement>();
  const evaluatingRef = React.useRef(false);

  const evaluate = React.useCallback(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const children = Array.from(container.children) as HTMLElement[];
    if (children.length < 2) {
      return; // single item or no items, no need for fanciness
    }

    const tagsEls = children.slice(0, -1);
    const moreEl = children.pop()!;

    const apply = () => {
      const moreLabel = moreLabelFn(count);
      if (moreLabelRef.current && moreLabelRef.current.textContent !== moreLabel) {
        moreLabelRef.current.textContent = moreLabel;
      }
      moreEl.style.display = moreLabel !== null ? 'initial' : 'none';
      tagsEls.forEach((c, idx) => (c.style.display = idx < count ? 'initial' : 'none'));
    };

    evaluatingRef.current = true;

    let count = 0;
    apply();

    while (true) {
      if (container.scrollHeight > container.offsetHeight && count > 0) {
        count--;
        apply();
        break;
      } else if (count < tagsEls.length) {
        count++;
        apply();
      } else {
        break;
      }
    }

    evaluatingRef.current = false;
  }, [moreLabelFn, moreLabelRef, containerRef]);

  useResizeObserver(containerRef, () => {
    if (!evaluatingRef.current) {
      evaluate();
    }
  });

  React.useLayoutEffect(() => {
    window.requestAnimationFrame(evaluate);
  }, [evaluate]);

  return {containerRef, moreLabelRef};
}

export const AssetKeyTagCollection = React.memo((props: AssetKeyTagCollectionProps) => {
  const {assetKeys, useTags, extraTags, maxRows, dialogTitle = 'Assets in run'} = props;

  const count = assetKeys?.length ?? 0;
  const rendered = maxRows ? 10 : count === 1 ? 1 : 0;

  const {sortedAssetKeys, slicedSortedAssetKeys} = React.useMemo(() => {
    const sortedAssetKeys = assetKeys?.slice().sort(sortItemAssetKey) ?? [];
    return {
      sortedAssetKeys,
      slicedSortedAssetKeys: sortedAssetKeys?.slice(0, rendered) ?? [],
    };
  }, [assetKeys, rendered]);

  const {setShowMore, dialog} = useShowMoreDialog(dialogTitle, sortedAssetKeys, renderItemAssetKey);

  const moreLabelFn = React.useCallback(
    (displayed: number) =>
      displayed === 0
        ? `${numberFormatter.format(count)} assets`
        : count - displayed > 0
          ? `${numberFormatter.format(count - displayed)} more`
          : null,
    [count],
  );

  const {containerRef, moreLabelRef} = useAdjustChildVisibilityToFill(moreLabelFn);

  if (!count) {
    return null;
  }

  return (
    <Box
      ref={maxRows ? containerRef : null}
      flex={{gap: 4, alignItems: 'end', wrap: 'wrap'}}
      style={{
        minWidth: 0,
        maxWidth: '100%',
        maxHeight: maxRows ? maxRows * 30 : undefined,
        overflow: 'hidden',
      }}
    >
      {extraTags}
      {slicedSortedAssetKeys.map((assetKey) => (
        // Outer span ensures the popover target is in the right place if the
        // parent is a flexbox.
        <TagActionsPopover
          key={tokenForAssetKey(assetKey)}
          childrenMiddleTruncate
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
              <MiddleTruncate text={displayNameForAssetKey(assetKey)} />
            </Tag>
          ) : (
            <Link to={assetDetailsPathForKey(assetKey)}>
              <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                <Icon color={Colors.accentGray()} name="asset" size={16} />
                <MiddleTruncate text={displayNameForAssetKey(assetKey)} />
              </Box>
            </Link>
          )}
        </TagActionsPopover>
      ))}
      {rendered !== 1 && (
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
                to: globalAssetGraphPathForAssetsAndDescendants(sortedAssetKeys),
              },
            ]}
          >
            {useTags ? (
              <Tag intent="none" icon="asset">
                <span ref={moreLabelRef}>{moreLabelFn(0)}</span>
              </Tag>
            ) : (
              <ButtonLink onClick={() => setShowMore(true)} underline="hover">
                <Box
                  flex={{direction: 'row', gap: 8, alignItems: 'center', display: 'inline-flex'}}
                >
                  <Icon color={Colors.accentGray()} name="asset" size={16} />
                  <span ref={moreLabelRef}>{moreLabelFn(0)}</span>
                </Box>
              </ButtonLink>
            )}
          </TagActionsPopover>
          {dialog}
        </span>
      )}
    </Box>
  );
});

type Check = {name: string; assetKey: AssetKey};

interface AssetCheckTagCollectionProps {
  assetChecks: Check[] | null;
  dialogTitle?: string;
  useTags?: boolean;
  maxRows?: number;
}

export const AssetCheckTagCollection = React.memo((props: AssetCheckTagCollectionProps) => {
  const {assetChecks, maxRows, useTags, dialogTitle = 'Asset checks in run'} = props;

  const count = assetChecks?.length ?? 0;
  const rendered = maxRows ? 10 : count === 1 ? 1 : 0;

  const {sortedAssetChecks, slicedSortedAssetChecks} = React.useMemo(() => {
    const sortedAssetChecks = assetChecks?.slice().sort(sortItemAssetCheck) ?? [];
    return {
      sortedAssetChecks,
      slicedSortedAssetChecks: sortedAssetChecks?.slice(0, rendered) ?? [],
    };
  }, [assetChecks, rendered]);

  const {setShowMore, dialog} = useShowMoreDialog(
    dialogTitle,
    sortedAssetChecks,
    renderItemAssetCheck,
  );

  const moreLabelFn = React.useCallback(
    (displayed: number) =>
      displayed === 0
        ? `${numberFormatter.format(count)} checks`
        : count - displayed > 0
          ? `${numberFormatter.format(count - displayed)} more`
          : null,
    [count],
  );

  const {containerRef, moreLabelRef} = useAdjustChildVisibilityToFill(moreLabelFn);

  if (!count) {
    return null;
  }

  return (
    <Box
      ref={maxRows ? containerRef : null}
      flex={{gap: 4, alignItems: 'end', wrap: 'wrap'}}
      style={{
        minWidth: 0,
        maxWidth: '100%',
        maxHeight: maxRows ? maxRows * 30 : undefined,
        overflow: 'hidden',
      }}
    >
      {slicedSortedAssetChecks.map((check) => (
        <TagActionsPopover
          key={`${check.name}-${tokenForAssetKey(check.assetKey)}`}
          data={{key: '', value: ''}}
          actions={[{label: 'View asset check', to: assetDetailsPathForAssetCheck(check)}]}
          childrenMiddleTruncate
        >
          {useTags ? (
            <Tag intent="none" interactive icon="asset_check">
              <MiddleTruncate text={labelForAssetCheck(check)} />
            </Tag>
          ) : (
            <Link to={assetDetailsPathForAssetCheck(check)}>
              <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                <Icon color={Colors.accentGray()} name="asset_check" size={16} />
                <MiddleTruncate text={labelForAssetCheck(check)} />
              </Box>
            </Link>
          )}
        </TagActionsPopover>
      ))}
      {rendered !== 1 && (
        <span style={useTags ? {} : {marginBottom: -4}}>
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
                <span ref={moreLabelRef}>{moreLabelFn(0)}</span>
              </Tag>
            ) : (
              <ButtonLink onClick={() => setShowMore(true)} underline="hover">
                <Box
                  flex={{direction: 'row', gap: 8, alignItems: 'center', display: 'inline-flex'}}
                >
                  <Icon color={Colors.accentGray()} name="asset_check" size={16} />
                  <span ref={moreLabelRef}>{moreLabelFn(0)}</span>
                </Box>
              </ButtonLink>
            )}
          </TagActionsPopover>
          {dialog}
        </span>
      )}
    </Box>
  );
});
