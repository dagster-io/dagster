import {MenuItem, Suggest, useViewport} from '@dagster-io/ui-components';
import * as React from 'react';

import styles from './css/SearchFilter.module.css';
import {ShortcutHandler} from '../../app/ShortcutHandler';

type SearchFilterValue<T> = {
  label: string;
  value: T;
  // Optional fully-qualified name, matched alongside the label. Also used as
  // the item's identity, since labels are not necessarily unique.
  path?: string;
  // Optional qualifier rendered after the label when the label alone is
  // ambiguous within `values`.
  namespace?: string;
};

// The labels rendered by more than one entry. Only these get their full path
// shown, so the common case stays uncluttered.
export function ambiguousLabelsIn(values: {label: string}[]): Set<string> {
  const seen = new Set<string>();
  const ambiguous = new Set<string>();
  for (const {label} of values) {
    if (seen.has(label)) {
      ambiguous.add(label);
    }
    seen.add(label);
  }
  return ambiguous;
}

export const SearchFilter = <T,>({
  values,
  onSelectValue,
}: {
  values: SearchFilterValue<T>[];

  onSelectValue: (e: any, value: T) => void;
}) => {
  const {viewport, containerProps} = useViewport();
  const ref = React.useRef<HTMLDivElement | null>(null);

  const ambiguousLabels = React.useMemo(() => ambiguousLabelsIn(values), [values]);

  return (
    <ShortcutHandler
      key="insights"
      onShortcut={() => {
        if (ref.current) {
          ref.current.querySelector('input')?.focus();
        }
      }}
      shortcutLabel="⌥J"
      // Exclude metakey to not interfere with shortcut for opening/closing devtools
      shortcutFilter={(e) => !e.metaKey && e.altKey && e.code === 'KeyJ'}
    >
      <div
        className={styles.suggestWrapper}
        {...containerProps}
        ref={(div) => {
          if (div) {
            ref.current = div;
            containerProps.ref(div);
          }
        }}
      >
        <Suggest<(typeof values)[0]>
          key="asset-graph-explorer-search-bar"
          inputProps={{placeholder: 'Jump to…', style: {width: `min(100%, ${viewport.width}px)`}}}
          items={values}
          inputValueRenderer={(item) => item.label}
          itemPredicate={(query, item) => {
            const needle = query.trim().toLocaleLowerCase();
            if (!needle) {
              return true;
            }
            // Match the fully-qualified name too, so both `orders` and
            // `raw/orders` find the asset keyed ['raw', 'orders'].
            return (
              item.label.toLocaleLowerCase().includes(needle) ||
              !!item.path?.toLocaleLowerCase().includes(needle)
            );
          }}
          menuWidth={viewport.width}
          popoverProps={{usePortal: false, matchTargetWidth: true}}
          itemRenderer={(item, itemProps) => (
            <MenuItem
              active={itemProps.modifiers.active}
              onClick={(e) => itemProps.handleClick(e)}
              // Labels are not unique — two assets in different namespaces can
              // share a leaf name — so key on the path when we have one.
              key={item.path ?? item.label}
              // The qualifier goes inside the label rather than MenuItem's
              // `right` slot: that slot never shrinks, so a long qualifier
              // squeezes the label away entirely. Here the pair truncates as
              // one string, keeping the label itself readable.
              text={
                item.namespace && ambiguousLabels.has(item.label) ? (
                  <>
                    {item.label} <span className={styles.pathLabel}>{item.namespace}</span>
                  </>
                ) : (
                  item.label
                )
              }
            />
          )}
          noResults={<MenuItem disabled={true} text="No results" />}
          onItemSelect={(item, e) => onSelectValue(e, item.value)}
          selectedItem={null}
        />
      </div>
    </ShortcutHandler>
  );
};
