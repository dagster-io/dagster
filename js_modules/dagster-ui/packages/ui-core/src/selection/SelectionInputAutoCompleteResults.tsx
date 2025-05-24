import {
  BodySmall,
  Box,
  Colors,
  Container,
  Icon,
  Inner,
  Menu,
  MenuItem,
  Row,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useEffect} from 'react';
import styles from './SelectionInputAutoCompleteResults.module.css';

import {Suggestion} from './SelectionAutoCompleteProvider';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';

type SelectionInputAutoCompleteResultsProps = {
  results: {
    list: Suggestion[];
    from: number;
    to: number;
  } | null;
  width?: number;
  onSelect: (suggestion: Suggestion) => void;
  selectedIndex: number;
  loading?: boolean;
};

export const SelectionInputAutoCompleteResults = React.memo(
  ({results, width, onSelect, selectedIndex, loading}: SelectionInputAutoCompleteResultsProps) => {
    const menuRef = React.useRef<HTMLDivElement | null>(null);
    const rowVirtualizer = useVirtualizer({
      count: results?.list.length ?? 0,
      getScrollElement: () => menuRef.current,
      estimateSize: () => 28,
      overscan: 5,
    });

    const index = (results?.list.length ?? -1) > selectedIndex ? selectedIndex : -1;

    useEffect(() => {
      if (index !== -1) {
        rowVirtualizer.scrollToIndex(index);
      }
    }, [rowVirtualizer, index]);

    if (!results && !loading) {
      return null;
    }

    const items = rowVirtualizer.getVirtualItems();
    const totalHeight = rowVirtualizer.getTotalSize();

    return (
      <div style={{minWidth: width}}>
        <Menu>
          <Container ref={menuRef} style={{maxHeight: '300px', overflowY: 'auto'}}>
            <Inner $totalHeight={totalHeight}>
              {items.map(({index, key, size, start}) => {
                const result = results!.list[index]!;
                return (
                  <Row key={key} $height={size} $start={start}>
                    <div ref={rowVirtualizer.measureElement} data-index={index}>
                      {'type' in result && result.type === 'no-match' ? (
                        <Box
                          flex={{direction: 'row', alignItems: 'center', gap: 4}}
                          style={{padding: '6px 8px 6px 12px'}}
                        >
                          {result.jsx}
                        </Box>
                      ) : (
                        <MenuItem
                          text={result.jsx}
                          active={index === selectedIndex}
                          onClick={() => onSelect(result)}
                        />
                      )}
                    </div>
                  </Row>
                );
              })}
            </Inner>
          </Container>
        </Menu>
        {results?.list.length ? (
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
                <BodySmall>to navigate</BodySmall>
              </Box>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <div className={styles.keyHintWrapper}>
                  <BodySmall>Tab</BodySmall>
                </div>
                <BodySmall>to select</BodySmall>
              </Box>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <div className={styles.keyHintWrapper}>
                  <BodySmall>Enter</BodySmall>
                </div>
                <BodySmall>to search</BodySmall>
              </Box>
            </Box>
            <Box
              as="a"
              href="https://docs.dagster.io/guides/build/assets/asset-selection-syntax"
              target="_blank"
              rel="noopener noreferrer"
              flex={{direction: 'row', alignItems: 'center', gap: 4}}
            >
              <BodySmall>View documentation</BodySmall>
              <Icon name="open_in_new" color={Colors.linkDefault()} />
            </Box>
          </Box>
        ) : null}
        <IndeterminateLoadingBar $loading={loading} />
      </div>
    );
  },
);

