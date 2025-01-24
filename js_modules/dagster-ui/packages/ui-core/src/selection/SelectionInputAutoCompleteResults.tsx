import {
  BodySmall,
  Box,
  Colors,
  Container,
  Icon,
  IconName,
  Inner,
  Menu,
  MenuItem,
  MonoSmall,
  Row,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useEffect} from 'react';
import styled from 'styled-components';

import {Suggestion} from './SelectionAutoCompleteVisitor';
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
  setSelectedIndex: React.Dispatch<React.SetStateAction<{current: number}>>;
  loading?: boolean;
};

type Attribute =
  | 'column:'
  | 'table_name:'
  | 'column_tag:'
  | 'kind:'
  | 'code_location:'
  | 'group:'
  | 'owner:'
  | 'tag:'
  | 'status:';

const attributeToIcon: {[key in Attribute]: IconName} = {
  'column:': 'view_column',
  'table_name:': 'database',
  'column_tag:': 'label',
  'kind:': 'compute_kind',
  'code_location:': 'code_location',
  'group:': 'asset_group',
  'owner:': 'owner',
  'tag:': 'tag',
  'status:': 'status',
};

export const SelectionInputAutoCompleteResults = React.memo(
  ({
    results,
    width,
    onSelect,
    selectedIndex,
    setSelectedIndex,
    loading,
  }: SelectionInputAutoCompleteResultsProps) => {
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
                        text={<SuggestionItem suggestion={result} />}
                        active={index === selectedIndex}
                        onClick={() => onSelect(result)}
                        onMouseEnter={() => setSelectedIndex({current: index})}
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

const SuggestionItem = ({suggestion}: {suggestion: Suggestion}) => {
  let label;
  let icon: IconName | null = null;
  let value: string | null = suggestion.displayText;
  if (suggestion.nameBase) {
    if (suggestion.text.endsWith('_substring:')) {
      icon = 'magnify_glass_checked';
      label = 'Contains match';
    } else {
      icon = 'magnify_glass';
      label = 'Exact match';
    }
  } else if (suggestion.type === 'down-traversal' || suggestion.type === 'up-traversal') {
    icon = 'curly_braces';
    label =
      suggestion.type === 'down-traversal'
        ? 'Include downstream dependencies'
        : 'Include upstream dependencies';
  } else if (suggestion.type === 'logical_operator') {
    icon = 'curly_braces';
    label = suggestion.displayText.toUpperCase();
  } else if (suggestion.type === 'parenthesis') {
    icon = 'curly_braces';
    label = 'Parenthesis';
  } else if (suggestion.type === 'function') {
    if (suggestion.displayText === 'roots()') {
      label = 'Roots';
      icon = 'arrow_upward';
    } else if (suggestion.displayText === 'sinks()') {
      label = 'Sinks';
      icon = 'arrow_indent';
    }
  } else if (suggestion.type === 'attribute') {
    label = suggestion.displayText.replace(':', '').replace('_', ' ');
    label = label.charAt(0).toUpperCase() + label.slice(1);

    icon = attributeToIcon[suggestion.displayText as Attribute];
  } else if (suggestion.type === 'attribute-with-value') {
    const firstColon = suggestion.displayText.indexOf(':');
    const attributeKey = suggestion.displayText.slice(0, firstColon);
    const attributeValue = suggestion.displayText.slice(firstColon + 1);
    label = (
      <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
        <MonoSmall color={Colors.textLight()}>{attributeKey}:</MonoSmall>
        <MonoSmall>{attributeValue}</MonoSmall>
      </Box>
    );
    value = null;
  } else if (suggestion.type === 'attribute-value') {
    label = suggestion.displayText;
    value = null;
  }
  return (
    <Box flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 24}}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
        {icon ? <Icon name={icon} size={12} style={{margin: 0}} /> : null}
        <BodySmall>{label}</BodySmall>
      </Box>
      <MonoSmall>{value}</MonoSmall>
    </Box>
  );
};

const KeyHintWrapper = styled.div`
  border-radius: 8px;
  padding: 4px;
  background-color: ${Colors.backgroundGrayHover()};
`;
