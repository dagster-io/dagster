import {Colors, MenuItem, Suggest, useViewport} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {ShortcutHandler} from '../../app/ShortcutHandler';

export const SearchFilter = <T,>({
  values,
  onSelectValue,
}: {
  values: {label: string; value: T}[];
  onSelectValue: (e: React.MouseEvent<any>, value: T) => void;
}) => {
  const {viewport, containerProps} = useViewport();
  const ref = React.useRef<HTMLDivElement | null>(null);
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
      <SuggestWrapper
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
          itemPredicate={(query, item) =>
            item.label.toLocaleLowerCase().includes(query.toLocaleLowerCase())
          }
          menuWidth={viewport.width}
          popoverProps={{usePortal: false, matchTargetWidth: true}}
          itemRenderer={(item, itemProps) => (
            <MenuItem
              active={itemProps.modifiers.active}
              onClick={(e) => itemProps.handleClick(e)}
              key={item.label}
              text={item.label}
            />
          )}
          noResults={<MenuItem disabled={true} text="No results" />}
          onItemSelect={(item, e) => onSelectValue(e as any, item.value)}
          selectedItem={null}
        />
      </SuggestWrapper>
    </ShortcutHandler>
  );
};

const SuggestWrapper = styled.div`
  .bp5-input-group.dagster-suggest-input {
    width: 100%;

    ::placeholder {
      color: ${Colors.textLighter()};
    }
  }
`;
