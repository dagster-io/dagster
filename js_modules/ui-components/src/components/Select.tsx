/* eslint-disable no-restricted-imports */
import {PopoverProps} from '@blueprintjs/core';
import {
  Select as BlueprintSelect,
  ItemListRendererProps,
  SelectProps,
  isCreateNewItem,
} from '@blueprintjs/select';
/* eslint-enable no-restricted-imports */
import {useVirtualizer} from '@tanstack/react-virtual';
import deepmerge from 'deepmerge';
import * as React from 'react';

import {Box} from './Box';
import {MENU_ITEM_HEIGHT} from './Suggest';
import {Container, Inner, Row} from './VirtualizedTable';
import styles from './css/Select.module.css';

// arbitrary, just looks nice
const MAX_MENU_HEIGHT = 240;
const MENU_WIDTH = 250;

interface Props<T> extends React.PropsWithChildren<SelectProps<T>> {
  menuWidth?: number;
}

export const Select = <T,>(props: Props<T>) => {
  const {menuWidth = MENU_WIDTH, noResults, itemListRenderer, ...rest} = props;

  const popoverProps: Partial<PopoverProps> = {
    ...props.popoverProps,
    minimal: true,
    modifiers: deepmerge(
      {offset: {enabled: true, options: {offset: [0, 4]}}},
      props.popoverProps?.modifiers || {},
    ),
    popoverClassName: `dagster-popover ${props.popoverProps?.className || ''}`,
  };

  return (
    <BlueprintSelect<T>
      {...rest}
      popoverProps={popoverProps}
      itemListRenderer={
        itemListRenderer ??
        ((listProps) => {
          const {filteredItems} = listProps;
          if (filteredItems.length === 0 && noResults) {
            return (
              <Box
                className={styles.noResults}
                padding={{vertical: 4, horizontal: 8}}
                style={{width: menuWidth}}
              >
                {noResults}
              </Box>
            );
          }

          return <SelectList {...listProps} menuWidth={menuWidth} />;
        })
      }
    />
  );
};

interface SelectListProps<T> extends ItemListRendererProps<T> {
  menuWidth?: number;
}

const SelectList = <T,>(props: SelectListProps<T>) => {
  const {filteredItems, activeItem, menuWidth = MENU_WIDTH} = props;

  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const rowVirtualizer = useVirtualizer({
    count: filteredItems.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (_) => MENU_ITEM_HEIGHT,
    overscan: 10,
  });

  const items = rowVirtualizer.getVirtualItems();
  const totalHeight = rowVirtualizer.getTotalSize();
  const activeIndex =
    activeItem && !isCreateNewItem(activeItem) ? filteredItems.indexOf(activeItem) : -1;

  React.useEffect(() => {
    if (activeIndex !== -1) {
      rowVirtualizer.scrollToIndex(activeIndex);
    }
  }, [rowVirtualizer, activeIndex]);

  return (
    <div className={styles.selectListWrapper}>
      <Container
        ref={parentRef}
        className={styles.selectListContainer}
        style={{maxHeight: MAX_MENU_HEIGHT, width: menuWidth}}
      >
        <Inner totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            const item = filteredItems[index];
            if (!item) {
              return null;
            }

            return (
              <Row key={key} height={size} start={start}>
                {props.renderItem(item, index)}
              </Row>
            );
          })}
        </Inner>
      </Container>
    </div>
  );
};
