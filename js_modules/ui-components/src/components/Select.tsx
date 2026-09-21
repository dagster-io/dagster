import {useVirtualizer} from '@tanstack/react-virtual';
import clsx from 'clsx';
import deepmerge from 'deepmerge';
import {useCallback, useEffect, useRef, useState} from 'react';

import {Box} from './Box';
import {Popover} from './Popover';
import {MENU_ITEM_HEIGHT} from './Suggest';
import {TextInput} from './TextInput';
import {Container, Inner, Row} from './VirtualizedTable';
import styles from './css/Select.module.css';
import type {BaseListProps, ItemListRenderer, SelectPopoverProps} from './selectTypes';
import {useListItems} from './useListItems';

const MAX_MENU_HEIGHT = 240;
const MENU_WIDTH = 250;

interface SelectProps<T> extends BaseListProps<T> {
  itemListRenderer?: ItemListRenderer<T>;
  children?: React.ReactNode;
  filterable?: boolean;
  fill?: boolean;
  menuWidth?: number;
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>;
  popoverProps?: SelectPopoverProps;
}

export const Select = <T,>(props: SelectProps<T>) => {
  const {
    items,
    itemRenderer,
    onItemSelect,
    itemPredicate,
    itemListPredicate,
    itemListRenderer,
    activeItem: initialActiveItem,
    noResults,
    children,
    disabled = false,
    fill = false,
    filterable = true,
    menuWidth = MENU_WIDTH,
    query: controlledQuery,
    onQueryChange,
    resetOnQuery = true,
    resetOnSelect = false,
    resetOnClose = false,
    popoverProps = {},
    inputProps = {},
  } = props;

  const matchTargetWidth = popoverProps.matchTargetWidth ?? false;
  const effectiveMenuWidth: number | string = matchTargetWidth ? '100%' : menuWidth;
  const defaultPlacement = popoverProps.position ? undefined : ('bottom-start' as const);

  const [isOpen, setIsOpen] = useState(false);

  const list = useListItems<T>({
    items,
    itemPredicate,
    itemListPredicate,
    query: controlledQuery,
    onQueryChange,
    resetOnQuery,
    onItemSelect: (item, event) => {
      onItemSelect(item, event);
      setIsOpen(false);
      if (resetOnSelect) {
        list.resetQuery();
      }
    },
  });

  const handleKeyDown = (e: React.KeyboardEvent) => {
    list.handleKeyDown(e);
    if (e.key === 'Escape') {
      setIsOpen(false);
      if (resetOnClose) {
        list.resetQuery();
      }
    }
  };

  const handleInteraction = (nextOpen: boolean, e?: React.SyntheticEvent<HTMLElement>) => {
    if (disabled && nextOpen) {
      return;
    }
    setIsOpen(nextOpen);
    if (nextOpen) {
      list.setActiveItem(initialActiveItem ?? list.filteredItems[0] ?? null);
    }
    popoverProps.onInteraction?.(nextOpen, e);
  };

  const handlePopoverOpened = (node: HTMLElement) => {
    popoverProps.onOpened?.(node);
  };

  const handleTriggerKeyDown = (e: React.KeyboardEvent<HTMLElement>) => {
    if (!isOpen && e.key === 'ArrowDown') {
      e.preventDefault();
      setIsOpen(true);
      list.setActiveItem(initialActiveItem ?? list.filteredItems[0] ?? null);
      return;
    }
    if (isOpen) {
      handleKeyDown(e);
    }
  };

  const handlePopoverClosed = (node: HTMLElement) => {
    if (resetOnClose) {
      list.resetQuery();
    }
    popoverProps.onClosed?.(node);
  };

  const filterInputRef = useCallback((input: HTMLInputElement | null) => {
    if (input) {
      input.focus();
    }
  }, []);

  const {getItemProps} = list;
  const renderItem = useCallback(
    (item: T, index: number): React.JSX.Element | null => {
      return itemRenderer(item, getItemProps(item, index));
    },
    [itemRenderer, getItemProps],
  );

  const menuRef = useRef<HTMLElement | null>(null);

  const renderContent = () => {
    if (itemListRenderer) {
      return itemListRenderer({
        activeItem: list.activeItem,
        filteredItems: list.filteredItems,
        items,
        query: list.query,
        renderItem,
        itemsParentRef: menuRef,
        menuProps: {},
      });
    }
    if (list.filteredItems.length === 0 && noResults) {
      return (
        <Box className={styles.noResults} padding={{vertical: 4, horizontal: 8}}>
          {noResults}
        </Box>
      );
    }
    return (
      <SelectList
        filteredItems={list.filteredItems}
        activeItem={list.activeItem}
        menuWidth={!filterable ? effectiveMenuWidth : undefined}
        renderItem={renderItem}
        filterable={filterable}
      />
    );
  };

  const mergedPopoverProps: SelectPopoverProps = {
    placement: defaultPlacement,
    ...popoverProps,
    modifiers: deepmerge(
      {offset: {enabled: true, options: {offset: [0, 4]}}},
      popoverProps.modifiers || {},
    ),
    popoverClassName: clsx(
      'dagster-popover',
      popoverProps.popoverClassName,
      popoverProps.className,
    ),
  };

  return (
    <Popover
      {...mergedPopoverProps}
      isOpen={isOpen}
      onInteraction={handleInteraction}
      onOpened={handlePopoverOpened}
      onClosed={handlePopoverClosed}
      disabled={disabled}
      fill={fill}
      usePortal={!filterable}
      targetProps={{...popoverProps.targetProps, onKeyDown: handleTriggerKeyDown}}
      content={
        <div
          className={styles.selectContent}
          style={filterable ? {width: effectiveMenuWidth} : undefined}
          onKeyDown={handleKeyDown}
        >
          {filterable ? (
            <Box padding={8}>
              <TextInput
                ref={filterInputRef}
                icon="search"
                value={list.query}
                onChange={(e) => list.setQuery(e.target.value)}
                placeholder={inputProps.placeholder ?? 'Filter…'}
                style={inputProps.style}
                fill
              />
            </Box>
          ) : null}
          {renderContent()}
        </div>
      }
    >
      {children}
    </Popover>
  );
};

interface SelectListProps<T> {
  filteredItems: T[];
  activeItem: T | null;
  menuWidth?: number | string;
  renderItem: (item: T, index: number) => React.JSX.Element | null;
  filterable?: boolean;
}

const SelectList = <T,>(props: SelectListProps<T>) => {
  const {filteredItems, activeItem, filterable} = props;

  const parentRef = useRef<HTMLDivElement | null>(null);
  const rowVirtualizer = useVirtualizer({
    count: filteredItems.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => MENU_ITEM_HEIGHT,
    overscan: 10,
  });

  const virtualItems = rowVirtualizer.getVirtualItems();
  const totalHeight = rowVirtualizer.getTotalSize();
  const activeIndex = activeItem !== null ? filteredItems.indexOf(activeItem) : -1;

  useEffect(() => {
    if (activeIndex === 0 && parentRef.current) {
      parentRef.current.scrollTop = 0;
    } else if (activeIndex !== -1) {
      rowVirtualizer.scrollToIndex(activeIndex);
    }
  }, [rowVirtualizer, activeIndex]);

  return (
    <div className={styles.selectListWrapper}>
      <Container
        ref={parentRef}
        className={clsx(
          styles.selectListContainer,
          filterable && styles.selectListContainerNoTopPadding,
        )}
        style={{maxHeight: MAX_MENU_HEIGHT, width: props.menuWidth}}
      >
        <Inner totalHeight={totalHeight}>
          {virtualItems.map(({index, key, size, start}) => {
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
