import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogFooter,
  Icon,
  MiddleTruncate,
  SpinnerWithText,
  Tag,
} from '@dagster-io/ui-components';
import useResizeObserver from '@react-hook/resize-observer';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {displayNameForAssetKey, tokenForAssetKey} from '../asset-graph/Utils';
import {
  Check,
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
import {globalAssetGraphPathForAssets} from '../assets/globalAssetGraphPathToString';
import {AssetKey} from '../assets/types';
import {TagActionsPopover} from '../ui/TagActions';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';
import {numberFormatter} from '../ui/formatters';

/**
 * Describes a selection whose inline tags are a bounded preview, with the full list fetched lazily
 * (e.g. the runs feed, where a run can target tens of thousands of assets/checks). When provided,
 * the total count drives the labels and the full list is loaded on demand for the "View list"
 * dialog and lineage link.
 */
export interface TagCollectionLazyLoad<T> {
  /** Total number of items; the inline preview list may be truncated. */
  totalCount: number;
  /** The full list, once lazily loaded (null until then). */
  allItems: T[] | null;
  /** Whether the full list is currently being fetched. */
  loading: boolean;
  /** Request the full list. Called when the overflow popover opens and when an action is clicked. */
  onRequest: () => void;
}

function useShowMoreDialog<T>(
  dialogTitle: string,
  items: T[] | null,
  renderItem: (item: T) => React.ReactNode,
  loading?: boolean,
) {
  const [showMore, setShowMore] = React.useState(false);

  // Always render the dialog and toggle it with `isOpen` rather than mounting/unmounting it on
  // `showMore` — mount/unmount breaks the open/close fade animation.
  const dialog = (
    <Dialog
      title={dialogTitle}
      onClose={() => setShowMore(false)}
      style={{minWidth: '400px', width: '50vw', maxWidth: '800px', maxHeight: '70vh'}}
      isOpen={showMore}
    >
      <div style={{height: '500px', overflow: 'hidden'}}>
        {items && items.length ? (
          <VirtualizedItemListForDialog items={items} renderItem={renderItem} />
        ) : (
          <Box flex={{alignItems: 'center', justifyContent: 'center'}} style={{height: '100%'}}>
            {loading ? <SpinnerWithText label="Loading…" /> : null}
          </Box>
        )}
      </div>
      <DialogFooter topBorder>
        <Button intent="primary" autoFocus onClick={() => setShowMore(false)}>
          Done
        </Button>
      </DialogFooter>
    </Dialog>
  );

  return {dialog, showMore, setShowMore};
}

interface AssetKeyTagCollectionProps {
  /**
   * The asset keys to render as inline tags. When `lazy` is provided this is only a bounded
   * preview — `lazy.totalCount` is the true count and `lazy.allItems` the full list (loaded on
   * demand). Without `lazy` it is the complete list.
   */
  assetKeys: AssetKey[] | null;
  dialogTitle?: string;
  useTags?: boolean;
  extraTags?: React.ReactNode[];
  maxRows?: number;
  lazy?: TagCollectionLazyLoad<AssetKey>;
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
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
  const {assetKeys, useTags, extraTags, maxRows, dialogTitle = 'Assets in run', lazy} = props;

  const count = lazy ? lazy.totalCount : (assetKeys?.length ?? 0);
  const rendered = maxRows ? 10 : count === 1 ? 1 : 0;

  // When the preview already holds the entire selection there is nothing more to fetch, so the
  // preview itself is the full list and actions needing it are ready immediately.
  const previewComplete = !lazy || (assetKeys?.length ?? 0) >= lazy.totalCount;

  const {slicedSortedAssetKeys, fullAssetKeys} = React.useMemo(() => {
    const sortedPreview = assetKeys?.slice().sort(sortItemAssetKey) ?? [];
    const sortedAll = lazy?.allItems ? lazy.allItems.slice().sort(sortItemAssetKey) : null;
    return {
      slicedSortedAssetKeys: sortedPreview.slice(0, rendered),
      // The complete, sorted list: the preview when it already holds everything, otherwise the
      // lazily-loaded full list (null until it arrives).
      fullAssetKeys: previewComplete ? sortedPreview : sortedAll,
    };
  }, [assetKeys, rendered, lazy, previewComplete]);

  const {setShowMore, dialog} = useShowMoreDialog(
    dialogTitle,
    fullAssetKeys,
    renderItemAssetKey,
    lazy?.loading,
  );

  // Kick off the lazy fetch (a no-op when the preview is already complete) when the overflow menu
  // opens or "View list" is clicked.
  const requestFull = React.useCallback(() => {
    if (!previewComplete) {
      lazy?.onRequest();
    }
  }, [previewComplete, lazy]);

  const showMore = React.useCallback(() => {
    requestFull();
    setShowMore(true);
  }, [requestFull, setShowMore]);

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
            onOpening={requestFull}
            actions={[
              {
                label: 'View list',
                onClick: showMore,
              },
              // Lineage needs the complete set; disable it until the full list is available so we
              // never navigate with only the preview.
              fullAssetKeys
                ? {
                    label: 'View lineage',
                    to: globalAssetGraphPathForAssets(fullAssetKeys),
                  }
                : {
                    label: 'View lineage',
                    to: '',
                    disabled: true,
                  },
            ]}
          >
            {useTags ? (
              <Tag intent="none" icon="asset">
                <span ref={moreLabelRef}>{moreLabelFn(0)}</span>
              </Tag>
            ) : (
              <ButtonLink onClick={showMore} underline="hover">
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

interface AssetCheckTagCollectionProps {
  /**
   * The asset checks to render as inline tags. When `lazy` is provided this is only a bounded
   * preview — `lazy.totalCount` is the true count and `lazy.allItems` the full list (loaded on
   * demand). Without `lazy` it is the complete list.
   */
  assetChecks: Check[] | null;
  dialogTitle?: string;
  maxRows?: number;
  lazy?: TagCollectionLazyLoad<Check>;
}

export const AssetCheckTagCollection = React.memo((props: AssetCheckTagCollectionProps) => {
  const {assetChecks, maxRows, dialogTitle = 'Asset checks in run', lazy} = props;

  const count = lazy ? lazy.totalCount : (assetChecks?.length ?? 0);
  const rendered = maxRows ? 10 : count === 1 ? 1 : 0;

  // When the preview already holds every check there is nothing more to fetch.
  const previewComplete = !lazy || (assetChecks?.length ?? 0) >= lazy.totalCount;

  const {slicedSortedAssetChecks, fullAssetChecks} = React.useMemo(() => {
    const sortedPreview = assetChecks?.slice().sort(sortItemAssetCheck) ?? [];
    const sortedAll = lazy?.allItems ? lazy.allItems.slice().sort(sortItemAssetCheck) : null;
    return {
      slicedSortedAssetChecks: sortedPreview.slice(0, rendered),
      fullAssetChecks: previewComplete ? sortedPreview : sortedAll,
    };
  }, [assetChecks, rendered, lazy, previewComplete]);

  const {setShowMore, dialog} = useShowMoreDialog(
    dialogTitle,
    fullAssetChecks,
    renderItemAssetCheck,
    lazy?.loading,
  );

  const requestFull = React.useCallback(() => {
    if (!previewComplete) {
      lazy?.onRequest();
    }
  }, [previewComplete, lazy]);

  const showMore = React.useCallback(() => {
    requestFull();
    setShowMore(true);
  }, [requestFull, setShowMore]);

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
          <Tag intent="none" interactive icon="asset_check">
            <MiddleTruncate text={labelForAssetCheck(check)} />
          </Tag>
        </TagActionsPopover>
      ))}
      {rendered !== 1 && (
        <span>
          <TagActionsPopover
            data={{key: '', value: ''}}
            onOpening={requestFull}
            actions={[
              {
                label: 'View list',
                onClick: showMore,
              },
            ]}
          >
            <Tag intent="none" icon="asset_check">
              <span ref={moreLabelRef}>{moreLabelFn(0)}</span>
            </Tag>
          </TagActionsPopover>
          {dialog}
        </span>
      )}
    </Box>
  );
});
