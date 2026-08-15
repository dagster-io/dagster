import {useCallback, useEffect, useMemo, useRef, useState} from 'react';

import type {ItemListPredicate, ItemPredicate, ItemRendererProps} from './selectTypes';

interface UseListItemsProps<T> {
  items: T[];
  itemPredicate?: ItemPredicate<T>;
  itemListPredicate?: ItemListPredicate<T>;
  /** When provided, query state is controlled by the caller. */
  query?: string;
  onQueryChange?: (query: string) => void;
  initialQuery?: string;
  resetOnQuery?: boolean;
  onItemSelect: (item: T, event?: React.MouseEvent<HTMLElement>) => void;
}

interface UseListItemsResult<T> {
  query: string;
  setQuery: (q: string) => void;
  filteredItems: T[];
  activeItem: T | null;
  setActiveItem: (item: T | null) => void;
  activeIndex: number;
  handleKeyDown: (e: React.KeyboardEvent) => void;
  getItemProps: (item: T, index: number) => ItemRendererProps;
  resetQuery: () => void;
}

export function useListItems<T>(props: UseListItemsProps<T>): UseListItemsResult<T> {
  const {
    items,
    itemPredicate,
    itemListPredicate,
    onItemSelect,
    query: controlledQuery,
    onQueryChange,
    initialQuery = '',
    resetOnQuery = true,
  } = props;

  const [uncontrolledQuery, setUncontrolledQuery] = useState(initialQuery);
  const queryIsControlled = controlledQuery !== undefined;
  const query = queryIsControlled ? controlledQuery : uncontrolledQuery;

  const setQuery = useCallback(
    (q: string) => {
      onQueryChange?.(q);
      if (!queryIsControlled) {
        setUncontrolledQuery(q);
      }
    },
    [onQueryChange, queryIsControlled],
  );

  const resetQuery = useCallback(() => {
    setQuery('');
  }, [setQuery]);

  const filteredItems = useMemo(() => {
    if (itemListPredicate) {
      return itemListPredicate(query, items);
    }
    if (itemPredicate) {
      return items.filter((item, index) => itemPredicate(query, item, index));
    }
    return items;
  }, [items, query, itemListPredicate, itemPredicate]);

  const [activeItem, setActiveItem] = useState<T | null>(null);

  const activeIndex = activeItem !== null ? filteredItems.indexOf(activeItem) : -1;

  const prevQueryRef = useRef(query);
  useEffect(() => {
    if (query !== prevQueryRef.current) {
      prevQueryRef.current = query;
      if (resetOnQuery && filteredItems.length > 0) {
        const firstItem = filteredItems[0];
        if (firstItem !== undefined) {
          setActiveItem(firstItem);
        }
      }
    }
  }, [query, filteredItems, resetOnQuery]);

  const queryRef = useRef(query);
  queryRef.current = query;

  const stateRef = useRef({filteredItems, activeItem, activeIndex});
  stateRef.current = {filteredItems, activeItem, activeIndex};

  const onItemSelectRef = useRef(onItemSelect);
  onItemSelectRef.current = onItemSelect;

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    const {filteredItems: items, activeIndex: idx} = stateRef.current;
    const len = items.length;

    switch (e.key) {
      case 'ArrowDown': {
        e.preventDefault();
        if (len > 0) {
          const nextIndex = idx === -1 ? 0 : (idx + 1) % len;
          const nextItem = items[nextIndex];
          if (nextItem !== undefined) {
            setActiveItem(nextItem);
          }
        }
        break;
      }
      case 'ArrowUp': {
        e.preventDefault();
        if (len > 0) {
          const nextIndex = idx <= 0 ? len - 1 : idx - 1;
          const nextItem = items[nextIndex];
          if (nextItem !== undefined) {
            setActiveItem(nextItem);
          }
        }
        break;
      }
      case 'Enter': {
        const {
          activeItem: current,
          activeIndex: currentIdx,
          filteredItems: currentItems,
        } = stateRef.current;
        const itemToSelect = current !== null && currentIdx !== -1 ? current : currentItems[0];
        if (itemToSelect !== undefined) {
          e.preventDefault();
          onItemSelectRef.current(itemToSelect);
        }
        break;
      }
    }
  }, []);

  const getItemProps = useCallback(
    (item: T, index: number): ItemRendererProps => {
      return {
        index,
        modifiers: {
          active: item === activeItem,
          disabled: false,
          matchesPredicate: true,
        },
        query: queryRef.current,
        handleClick: (e: React.MouseEvent<HTMLElement>) => {
          e.preventDefault();
          onItemSelectRef.current(item, e);
        },
        handleFocus: () => {
          setActiveItem(item);
        },
      };
    },
    [activeItem],
  );

  return {
    query,
    setQuery,
    filteredItems,
    activeItem,
    setActiveItem,
    activeIndex,
    handleKeyDown,
    getItemProps,
    resetQuery,
  };
}
