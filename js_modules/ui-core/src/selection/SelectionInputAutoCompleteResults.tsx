import {
  Box,
  Colors,
  Container,
  Icon,
  Inner,
  Menu,
  MenuItem,
  Row,
  Text,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useEffect} from 'react';

import {Suggestion} from './SelectionAutoCompleteProvider';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';
import {assertExists} from '../util/invariant';
import styles from './css/SelectionInputAutoCompleteResults.module.css';

// Provider suggestions, plus the recent-search rows and divider the input prepends.
export type ResultItem =
  | Suggestion
  | {type: 'recent'; text: string; jsx: React.ReactNode}
  | {type: 'divider'};

// 4px padding above and below a 1px rule.
const DIVIDER_HEIGHT = 9;

const isDivider = (item: ResultItem | undefined) =>
  !!item && 'type' in item && item.type === 'divider';

export type SelectableResult = Exclude<ResultItem, {type: 'divider'} | {type: 'no-match'}>;

export const isSelectableResult = (item: ResultItem): item is SelectableResult =>
  !('type' in item) || item.type === 'recent';

// Keyed by content, not index: rows shift as recents appear and disappear, and the
// virtualizer would otherwise reuse the divider's cached height for a suggestion.
const getResultKey = (item: ResultItem | undefined, index: number) => {
  if (!item) {
    return index;
  }
  if (!('type' in item)) {
    return `suggestion:${item.text}`;
  }
  return item.type === 'divider' ? 'divider' : `${item.type}:${item.text}`;
};

const ResultRow = ({
  result,
  active,
  onSelect,
}: {
  result: ResultItem;
  active: boolean;
  onSelect: (item: ResultItem) => void;
}) => {
  if ('type' in result && result.type === 'divider') {
    return (
      <div className={styles.dividerWrapper} role="separator">
        <div className={styles.divider} />
      </div>
    );
  }
  if ('type' in result && result.type === 'no-match') {
    return (
      <Box
        flex={{direction: 'row', alignItems: 'center', gap: 4}}
        style={{padding: '6px 8px 6px 12px'}}
      >
        {result.jsx}
      </Box>
    );
  }
  return (
    <MenuItem
      text={result.jsx}
      active={active}
      onMouseDown={(e) => {
        e.preventDefault();
        onSelect(result);
      }}
    />
  );
};

type SelectionInputAutoCompleteResultsProps = {
  results: {
    list: ResultItem[];
    from: number;
    to: number;
  };
  width?: number;
  onSelect: (item: ResultItem) => void;
  selectedIndex: number;
  loading?: boolean;
};

export const SelectionInputAutoCompleteResults = React.memo(
  ({results, width, onSelect, selectedIndex, loading}: SelectionInputAutoCompleteResultsProps) => {
    const menuRef = React.useRef<HTMLDivElement | null>(null);
    const rowVirtualizer = useVirtualizer({
      count: results.list.length,
      getScrollElement: () => menuRef.current,
      estimateSize: (index) => (isDivider(results.list[index]) ? DIVIDER_HEIGHT : 28),
      getItemKey: (index) => getResultKey(results.list[index], index),
      overscan: 5,
    });

    const index = results.list.length > selectedIndex ? selectedIndex : -1;

    useEffect(() => {
      if (index !== -1) {
        rowVirtualizer.scrollToIndex(index);
      }
    }, [rowVirtualizer, index]);

    const items = rowVirtualizer.getVirtualItems();
    const totalHeight = rowVirtualizer.getTotalSize();

    return (
      <div style={{minWidth: width}}>
        <Menu>
          <Container ref={menuRef} style={{maxHeight: '300px', overflowY: 'auto'}}>
            <Inner totalHeight={totalHeight}>
              {items.map(({index, key, size, start}) => {
                const result = assertExists(results.list[index]);
                return (
                  <Row key={key} height={size} start={start}>
                    <div ref={rowVirtualizer.measureElement} data-index={index}>
                      <ResultRow
                        result={result}
                        active={index === selectedIndex}
                        onSelect={onSelect}
                      />
                    </div>
                  </Row>
                );
              })}
            </Inner>
          </Container>
        </Menu>
        {results.list.length ? (
          <Box
            flex={{
              direction: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 32,
            }}
            padding={{vertical: 4, horizontal: 12}}
            style={{color: Colors.textLight(), backgroundColor: Colors.backgroundGray()}}
          >
            <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <div className={styles.keyHintWrapper}>
                  <Icon name="arrow_upward" size={12} style={{margin: 0}} />
                </div>
                <div className={styles.keyHintWrapper}>
                  <Icon name="arrow_downward" size={12} style={{margin: 0}} />
                </div>
                <Text size={12}>to navigate</Text>
              </Box>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <div className={styles.keyHintWrapper}>
                  <Text size={12}>Tab</Text>
                </div>
                <Text size={12}>to select</Text>
              </Box>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <div className={styles.keyHintWrapper}>
                  <Text size={12}>Enter</Text>
                </div>
                <Text size={12}>to search</Text>
              </Box>
            </Box>
            <a
              href="https://docs.dagster.io/guides/build/assets/asset-selection-syntax"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <Text size={12}>View documentation</Text>
                <Icon name="open_in_new" color={Colors.linkDefault()} />
              </Box>
            </a>
          </Box>
        ) : null}
        <IndeterminateLoadingBar $loading={loading} />
      </div>
    );
  },
);
