import {
  Box,
  Colors,
  Icon,
  IconName,
  MiddleTruncate,
  NonIdealState,
  TextInput,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {ChangeEvent, ReactNode, useCallback, useRef, useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {Container, HeaderCell, HeaderRow, Inner, Row} from '../ui/VirtualizedTable';

const ROW_HEIGHT = 44;

interface Props<T> {
  items: T[];
  placeholder: string;
  nameFilter: (item: T, searchValue: string) => boolean;
  renderRow: (item: T) => ReactNode;
}

export const CodeLocationSearchableList = <T,>(props: Props<T>) => {
  const {items, placeholder, nameFilter, renderRow} = props;

  const [searchValue, setSearchValue] = useState('');
  const onChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
  }, []);

  const trimmedValue = searchValue.trim().toLowerCase();
  const filteredItems = items.filter((item) => nameFilter(item, trimmedValue));

  const containerRef = useRef<HTMLDivElement | null>(null);
  const rowVirtualizer = useVirtualizer({
    count: filteredItems.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const virtualItems = rowVirtualizer.getVirtualItems();

  return (
    <Box flex={{direction: 'column'}} style={{overflow: 'hidden'}}>
      <Box padding={{vertical: 8, horizontal: 24}}>
        <TextInput
          value={searchValue}
          onChange={onChange}
          placeholder={placeholder}
          style={{width: '300px'}}
          icon="search"
        />
      </Box>
      <div style={{flex: 1, overflow: 'hidden'}}>
        <Container ref={containerRef}>
          <HeaderRow templateColumns="1fr" sticky>
            <HeaderCell>Name</HeaderCell>
          </HeaderRow>
          {virtualItems.length > 0 ? (
            <Inner $totalHeight={totalHeight}>
              {virtualItems.map(({index, key, size, start}) => {
                const item = filteredItems[index]!;
                return (
                  <Row key={key} $height={size} $start={start}>
                    {renderRow(item)}
                  </Row>
                );
              })}
            </Inner>
          ) : (
            <Box flex={{direction: 'row', justifyContent: 'center'}} padding={{top: 32}}>
              <NonIdealState
                icon="search"
                title="No matching results"
                description={
                  <>
                    No matching results for query <strong>{searchValue}</strong> found in this code
                    location.
                  </>
                }
              />
            </Box>
          )}
        </Container>
      </div>
    </Box>
  );
};

interface SearchableListRowProps {
  iconName: IconName;
  label: string;
  path: string;
}

export const SearchableListRow = ({iconName, label, path}: SearchableListRowProps) => {
  return (
    <Box
      padding={{horizontal: 24}}
      border="bottom"
      flex={{direction: 'column', justifyContent: 'center', alignItems: 'flex-start'}}
      style={{height: ROW_HEIGHT, overflow: 'hidden'}}
    >
      <ListLink to={path} style={{width: '100%', overflow: 'hidden'}}>
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <Icon name={iconName} color={Colors.linkDefault()} />
          <div style={{flex: 1, overflow: 'hidden'}}>
            <MiddleTruncate text={label} />
          </div>
        </Box>
      </ListLink>
    </Box>
  );
};

const ListLink = styled(Link)`
  :active,
  :focus {
    outline: none;
  }
`;
