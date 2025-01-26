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
import styled from 'styled-components';

import {BaseSuggestion} from './SelectionAutoCompleteProvider';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';

type SelectionInputAutoCompleteResultsProps<T extends {text: string}> = {
  results: {
    list: Array<T | BaseSuggestion>;
    from: number;
    to: number;
  } | null;
  width?: number;
  onSelect: (suggestion: T | BaseSuggestion) => void;
  renderResult: (suggestion: T | BaseSuggestion) => React.ReactNode;
  selectedIndex: number;
  setSelectedIndex: React.Dispatch<React.SetStateAction<{current: number}>>;
  loading?: boolean;
};

export const SelectionInputAutoCompleteResults = React.memo(
  <T extends {text: string}>({
    results,
    width,
    onSelect,
    selectedIndex,
    setSelectedIndex,
    loading,
    renderResult,
  }: SelectionInputAutoCompleteResultsProps<T>) => {
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
                      <MenuItem
                        key={key}
                        text={renderResult(result)}
                        active={index === selectedIndex}
                        onClick={() => onSelect(result)}
                        onMouseMove={() => setSelectedIndex({current: index})}
                      />
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
            padding={{vertical: 8, horizontal: 12}}
            style={{color: Colors.textLight(), backgroundColor: Colors.backgroundGray()}}
          >
            <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <KeyHintWrapper>
                  <Icon name="arrow_upward" size={12} style={{margin: 0}} />
                </KeyHintWrapper>
                <KeyHintWrapper>
                  <Icon name="arrow_downward" size={12} style={{margin: 0}} />
                </KeyHintWrapper>
                <BodySmall>to navigate</BodySmall>
              </Box>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <KeyHintWrapper>
                  <BodySmall>Tab</BodySmall>
                </KeyHintWrapper>
                <BodySmall>to select</BodySmall>
              </Box>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <KeyHintWrapper>
                  <BodySmall>Enter</BodySmall>
                </KeyHintWrapper>
                <BodySmall>to search</BodySmall>
              </Box>
            </Box>
            <Box as="a" href="#TODO" flex={{direction: 'row', alignItems: 'center', gap: 4}}>
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

const KeyHintWrapper = styled.div`
  border-radius: 8px;
  padding: 4px;
  background-color: ${Colors.backgroundGrayHover()};
`;
