import {useVirtualizer} from '@tanstack/react-virtual';
import clsx from 'clsx';
import deepmerge from 'deepmerge';
import {useCallback, useEffect, useRef, useState} from 'react';

import {Box} from './Box';
import {Colors} from './Color';
import {Icon, IconName} from './Icon';
import {Intent} from './Intent';
import {Popover} from './Popover';
import {TextInput} from './TextInput';
import {Container, Inner, Row} from './VirtualizedTable';
import styles from './css/Suggest.module.css';
import type {BaseListProps, SelectPopoverProps} from './selectTypes';
import {useListItems} from './useListItems';

export const MENU_ITEM_HEIGHT = 32;

const MAX_MENU_HEIGHT = 240;
const MENU_WIDTH = 250;

interface SuggestInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  rightElement?: React.ReactNode;
  inputRef?: React.RefCallback<HTMLInputElement> | React.MutableRefObject<HTMLInputElement | null>;
  intent?: Intent;
}

interface SuggestProps<T> extends BaseListProps<T> {
  selectedItem?: T | null;
  defaultSelectedItem?: T;
  inputValueRenderer: (item: T) => string;
  menuWidth?: number;
  itemHeight?: number;
  icon?: IconName;
  inputProps?: SuggestInputProps;
  popoverProps?: SelectPopoverProps;
}

export const Suggest = <T,>(props: SuggestProps<T>) => {
  const {
    items,
    itemRenderer,
    onItemSelect,
    itemPredicate,
    itemListPredicate,
    noResults,
    selectedItem = null,
    defaultSelectedItem,
    inputValueRenderer,
    disabled = false,
    query: controlledQuery,
    onQueryChange,
    resetOnQuery = true,
    resetOnSelect = false,
    resetOnClose = false,
    menuWidth = MENU_WIDTH,
    icon,
    popoverProps = {},
    inputProps = {},
  } = props;

  const defaultPlacement = popoverProps.position ? undefined : ('bottom-start' as const);

  const [isOpen, setIsOpen] = useState(false);
  const internalInputRef = useRef<HTMLInputElement | null>(null);

  const setInputRef = useCallback(
    (node: HTMLInputElement | null) => {
      internalInputRef.current = node;
      const consumerRef = inputProps.inputRef;
      if (typeof consumerRef === 'function') {
        consumerRef(node);
      } else if (consumerRef) {
        consumerRef.current = node;
      }
    },
    [inputProps.inputRef],
  );

  const effectiveDefault = selectedItem ?? defaultSelectedItem;
  const [initialQuery] = useState(() =>
    effectiveDefault !== null && effectiveDefault !== undefined
      ? inputValueRenderer(effectiveDefault)
      : '',
  );

  const list = useListItems<T>({
    items,
    itemPredicate,
    itemListPredicate,
    query: controlledQuery,
    onQueryChange,
    initialQuery,
    resetOnQuery,
    onItemSelect: (item, event) => {
      onItemSelect(item, event);
      setIsOpen(false);
      if (resetOnSelect) {
        list.resetQuery();
      } else {
        list.setQuery(inputValueRenderer(item));
      }
    },
  });

  const {setQuery, getItemProps} = list;

  const prevSelectedItemRef = useRef(selectedItem);
  useEffect(() => {
    if (selectedItem !== prevSelectedItemRef.current && controlledQuery === undefined) {
      prevSelectedItemRef.current = selectedItem;
      if (selectedItem !== null) {
        setQuery(inputValueRenderer(selectedItem));
      } else {
        setQuery('');
      }
    }
  }, [selectedItem, controlledQuery, inputValueRenderer, setQuery]);

  // When the popover closes without a selection (blur, Escape), restore the input to the
  // last selected item's label, or clear it if nothing is selected. This prevents the input
  // from showing a partial query string after the user dismisses the dropdown.
  // To verify: type a partial query, press Escape — the input should revert to the selected value.
  const restoreOrResetQuery = () => {
    if (selectedItem !== null) {
      list.setQuery(inputValueRenderer(selectedItem));
    } else {
      list.resetQuery();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    list.handleKeyDown(e);
    if (e.key === 'Escape') {
      setIsOpen(false);
      if (resetOnClose) {
        restoreOrResetQuery();
      }
    }
    inputProps.onKeyDown?.(e);
  };

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    if (!disabled) {
      setIsOpen(true);
      if (list.filteredItems.length > 0) {
        const firstItem = list.filteredItems[0];
        if (firstItem !== undefined) {
          list.setActiveItem(firstItem);
        }
      }
    }
    inputProps.onFocus?.(e);
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsOpen(false);
    if (resetOnClose) {
      restoreOrResetQuery();
    }
    inputProps.onBlur?.(e);
  };

  const handleInteraction = (nextOpen: boolean, e?: React.SyntheticEvent<HTMLElement>) => {
    if (disabled && nextOpen) {
      return;
    }
    if (nextOpen) {
      setIsOpen(true);
    }
    popoverProps.onInteraction?.(nextOpen, e);
  };

  const handlePopoverOpened = (node: HTMLElement) => {
    popoverProps.onOpened?.(node);
  };

  const handlePopoverClosed = (node: HTMLElement) => {
    if (resetOnClose) {
      restoreOrResetQuery();
    }
    popoverProps.onClosed?.(node);
  };

  const renderItem = useCallback(
    (item: T, index: number): React.JSX.Element | null => {
      return itemRenderer(item, getItemProps(item, index));
    },
    [itemRenderer, getItemProps],
  );

  const renderPopoverContent = () => {
    if (list.filteredItems.length === 0 && noResults) {
      return (
        <Box
          padding={{vertical: 4, horizontal: 8}}
          style={{width: menuWidth, outline: 'none', cursor: 'default'}}
        >
          {noResults}
        </Box>
      );
    }
    return (
      <SuggestionList
        filteredItems={list.filteredItems}
        activeItem={list.activeItem}
        menuWidth={menuWidth}
        renderItem={renderItem}
      />
    );
  };

  const mergedPopoverProps: SelectPopoverProps = {
    placement: defaultPlacement,
    ...popoverProps,
    modifiers: deepmerge(
      {offset: {enabled: true, options: {offset: [0, 8]}}},
      popoverProps.modifiers || {},
    ),
    popoverClassName: clsx(
      'dagster-popover',
      popoverProps.popoverClassName,
      popoverProps.className,
    ),
  };

  const suggest = (
    <Popover
      {...mergedPopoverProps}
      isOpen={isOpen}
      onInteraction={handleInteraction}
      onOpened={handlePopoverOpened}
      onClosed={handlePopoverClosed}
      disabled={disabled}
      fill
      content={<div onMouseDown={(e) => e.preventDefault()}>{renderPopoverContent()}</div>}
    >
      <div style={{position: 'relative', width: '100%'}}>
        <TextInput
          ref={setInputRef}
          role="combobox"
          fill
          value={list.query}
          onChange={(e) => {
            list.setQuery(e.target.value);
            if (!isOpen && !disabled) {
              setIsOpen(true);
            }
          }}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={inputProps.placeholder}
          style={{
            ...inputProps.style,
            ...(inputProps.rightElement ? {paddingRight: 28} : {}),
          }}
          className={inputProps.className}
          strokeColor={inputProps.intent === 'danger' ? Colors.accentRed() : undefined}
        />
        {inputProps.rightElement ? (
          <div className={styles.suggestRightElement}>{inputProps.rightElement}</div>
        ) : null}
      </div>
    </Popover>
  );

  if (icon) {
    return (
      <div className={styles.suggestWithIconWrapper}>
        <div>
          <Icon name={icon} />
        </div>
        {suggest}
      </div>
    );
  }

  return suggest;
};

interface SuggestionListProps<T> {
  filteredItems: T[];
  activeItem: T | null;
  menuWidth: number;
  renderItem: (item: T, index: number) => React.JSX.Element | null;
}

const SuggestionList = <T,>(props: SuggestionListProps<T>) => {
  const {filteredItems, activeItem, menuWidth} = props;

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
    if (activeIndex !== -1) {
      rowVirtualizer.scrollToIndex(activeIndex);
    }
  }, [rowVirtualizer, activeIndex]);

  return (
    <div style={{overflow: 'hidden'}}>
      <Container ref={parentRef} style={{maxHeight: MAX_MENU_HEIGHT, width: menuWidth, padding: 4}}>
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
