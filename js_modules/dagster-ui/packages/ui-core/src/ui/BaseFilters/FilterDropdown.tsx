import {
  Box,
  Button,
  Colors,
  Icon,
  IconWrapper,
  Menu,
  MenuItem,
  Popover,
  Spinner,
  TextInput,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useRef, useState} from 'react';
import * as React from 'react';
import styled, {createGlobalStyle} from 'styled-components';
import {v4 as uuidv4} from 'uuid';

import {FilterObject} from './useFilter';
import {ShortcutHandler} from '../../app/ShortcutHandler';
import {useSetStateUpdateCallback} from '../../hooks/useSetStateUpdateCallback';
import {useUpdatingRef} from '../../hooks/useUpdatingRef';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';

interface FilterDropdownProps {
  filters: FilterObject[];
  setIsOpen: (isOpen: boolean) => void;
  setPortaledElements: React.Dispatch<React.SetStateAction<JSX.Element[]>>;
}

export const FilterDropdown = ({filters, setIsOpen, setPortaledElements}: FilterDropdownProps) => {
  const [menuKey, _] = React.useState(() => uuidv4());
  const [focusedItemIndex, setFocusedItemIndex] = React.useState(-1);
  const [search, setSearch] = useState('');
  const [selectedFilterName, _setSelectedFilterName] = useState<string | null>(null);
  const selectedFilter = React.useMemo(() => {
    return filters.find((filter) => filter.name === selectedFilterName);
  }, [filters, selectedFilterName]);

  const setSelectedFilterName = useSetStateUpdateCallback(selectedFilterName, (nextName) => {
    _setSelectedFilterName(nextName);
    if (nextName === null) {
      if (selectedFilter) {
        selectedFilter.onUnselected?.();
      }
    }
  });

  const selectedFilterRef = useUpdatingRef(selectedFilter);
  React.useLayoutEffect(() => {
    return () => {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      selectedFilterRef.current?.onUnselected?.();
    };
  }, [selectedFilterRef]);

  const {results, filteredFilters} = React.useMemo(() => {
    const filteredFilters = selectedFilter
      ? []
      : search
      ? filters.filter((filter) => filter.name.toLowerCase().includes(search.toLowerCase()))
      : filters;

    const results: Record<string, {label: JSX.Element; key: string; value: any}[]> = {};
    if (search) {
      filters.forEach((filter) => {
        results[filter.name] = filter.getResults(search);
      });
    }
    return {results, filteredFilters};
  }, [search, filters, selectedFilter]);

  const selectValue = React.useCallback(
    (filter: FilterObject, value: any) => {
      filter.onSelect({
        value,
        close: () => {
          setSearch('');
          setSelectedFilterName(null);
          setFocusedItemIndex(-1);
          setIsOpen(false);
        },
        clearSearch: () => {
          setSearch('');
        },
        createPortal: (portaledElement) => {
          const portalElement = (
            <React.Fragment key={filter.name}>{portaledElement}</React.Fragment>
          );
          setPortaledElements((portaledElements) => [...portaledElements, portalElement]);
          return () => {
            setPortaledElements((portaledElements) =>
              portaledElements.filter((element) => element !== portalElement),
            );
          };
        },
      });
    },
    [setIsOpen, setPortaledElements, setSelectedFilterName],
  );

  const allResultsJsx = React.useMemo(() => {
    if (selectedFilter) {
      if (selectedFilter.isLoadingFilters) {
        return [];
      }
      return selectedFilter
        .getResults(search)
        .map((result, resultIndex) => (
          <FilterDropdownMenuItem
            key={`filter:${selectedFilter.name}:${result.key}`}
            onClick={() => selectValue(selectedFilter, result.value)}
            text={result.label}
            index={resultIndex}
            menuKey={menuKey}
            active={focusedItemIndex === resultIndex}
          />
        ));
    }
    const jsxResults: JSX.Element[] = [];
    filters.forEach((filter) => {
      if (filteredFilters.includes(filter)) {
        const index = jsxResults.length;
        jsxResults.push(
          <FilterDropdownMenuItem
            key={`filter:${filter.name}`}
            onClick={() => {
              setSelectedFilterName(filter.name);
              setFocusedItemIndex(-1);
            }}
            text={
              <Box flex={{direction: 'row', gap: 4}}>
                <Icon name={filter.icon} />
                {filter.name}
              </Box>
            }
            index={index}
            menuKey={menuKey}
            active={focusedItemIndex === index}
          />,
        );
      }
      results[filter.name]?.forEach((result) => {
        const index = jsxResults.length;
        jsxResults.push(
          <FilterDropdownMenuItem
            key={`filter-result:${filter.name}:${result.key}`}
            onClick={() => {
              setSelectedFilterName(filter.name);
              selectValue(filter, result.value);
            }}
            text={result.label}
            index={index}
            menuKey={menuKey}
            active={focusedItemIndex === index}
          />,
        );
      });
    });
    return jsxResults;
  }, [
    selectedFilter,
    filters,
    search,
    menuKey,
    focusedItemIndex,
    selectValue,
    filteredFilters,
    results,
    setSelectedFilterName,
  ]);

  const inputRef = useRef<HTMLInputElement | null>(null);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  const handleKeyDown = React.useCallback(
    async (event: React.KeyboardEvent) => {
      const maxIndex = allResultsJsx.length - 1;
      if (event.key === 'ArrowDown' || (event.key === 'Tab' && !event.shiftKey)) {
        setFocusedItemIndex((prevIndex) => (prevIndex === maxIndex ? -1 : prevIndex + 1));
        event.preventDefault();
      } else if (event.key === 'ArrowUp' || (event.key === 'Tab' && event.shiftKey)) {
        setFocusedItemIndex((prevIndex) => (prevIndex === -1 ? maxIndex : prevIndex - 1));
        event.preventDefault();
      } else if (event.key === 'Enter' || event.key === ' ') {
        if (focusedItemIndex === -1) {
          // They're typing in the search bar
          if (event.key === 'Enter' && allResultsJsx.length === 1) {
            // "Enter" submits the current search term
            event.preventDefault();
            allResultsJsx[0]?.props.onClick?.();
          }
          return;
        }
        event.preventDefault();
        allResultsJsx[focusedItemIndex]?.props.onClick?.();
      } else if (event.key === 'Escape') {
        if (selectedFilter) {
          setSelectedFilterName(null);
          setFocusedItemIndex(-1);
        } else {
          setIsOpen(false);
        }
      } else if (event.target === inputRef.current) {
        setFocusedItemIndex(-1);
      }
    },
    [allResultsJsx, focusedItemIndex, selectedFilter, setSelectedFilterName, setIsOpen],
  );

  const parentRef = React.useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: allResultsJsx.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 32,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <div>
      <TextInputWrapper>
        <TextInput
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search filters..."
          ref={(el) => {
            inputRef.current = el;
            el?.focus();
          }}
          aria-label="Search filters"
          aria-activedescendant={
            focusedItemIndex !== -1 ? itemId(menuKey, focusedItemIndex) : undefined
          }
          role="combobox"
          aria-expanded="true"
          aria-owns={menuKey}
        />
        <Box
          flex={{justifyContent: 'center', alignItems: 'center'}}
          padding={{vertical: 12, horizontal: 16}}
        >
          <SlashShortcut>f</SlashShortcut>
        </Box>
      </TextInputWrapper>
      <Menu>
        <DropdownMenuContainer id={menuKey} ref={dropdownRef} onKeyDown={handleKeyDown}>
          {selectedFilter && selectedFilter.isLoadingFilters ? (
            <Box padding={{vertical: 12, horizontal: 16}}>
              <Spinner purpose="section" />
            </Box>
          ) : allResultsJsx.length ? (
            <Container
              ref={parentRef}
              style={{
                maxHeight: `min(500px, 50vh)`,
                overflowY: 'auto',
                width: selectedFilter?.menuWidth || 'auto',
              }}
            >
              <Inner $totalHeight={totalHeight}>
                {items.map(({index, size, start}) => {
                  return (
                    <Row $height={size} $start={start} key={index}>
                      {allResultsJsx[index]}
                    </Row>
                  );
                })}
              </Inner>
            </Container>
          ) : (
            <Box padding={{vertical: 12, horizontal: 12}} style={{color: Colors.textLight()}}>
              {selectedFilter?.getNoResultsPlaceholder?.(search) || 'No results'}
            </Box>
          )}
        </DropdownMenuContainer>
      </Menu>
    </div>
  );
};

type FilterDropdownButtonProps = {
  filters: FilterObject[];
  label?: string;
};
export const FilterDropdownButton = React.memo(({filters, label}: FilterDropdownButtonProps) => {
  const keyRef = React.useRef(0);

  const [isOpen, _setIsOpen] = useState(false);
  const prevOpenRef = React.useRef(isOpen);

  const setIsOpen = useSetStateUpdateCallback(isOpen, (isOpen) => {
    _setIsOpen(isOpen);
    if (isOpen && !prevOpenRef.current) {
      // Reset the key when the dropdown is opened
      // But not when its closed because of the closing animation
      keyRef.current++;
    }
    prevOpenRef.current = isOpen;
  });

  const [portaledElements, setPortaledElements] = useState<JSX.Element[]>([]);

  const buttonRef = React.useRef<HTMLButtonElement>(null);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  /**
   * Popover doesn't seem to support canOutsideClickClose, so we have to do this ourselves.
   */
  React.useLayoutEffect(() => {
    const listener = (e: MouseEvent) => {
      if (
        buttonRef.current?.contains(e.target as Node) ||
        dropdownRef.current?.contains(e.target as Node) ||
        !document.contains(e.target as Node)
      ) {
        return;
      }
      setIsOpen(false);
    };
    document.body.addEventListener('mousedown', listener);
    return () => {
      document.body.removeEventListener('mousedown', listener);
    };
  }, [setIsOpen]);

  return (
    <ShortcutHandler
      shortcutLabel="F"
      shortcutFilter={(e) =>
        e.code === 'KeyF' && !(e.metaKey || e.ctrlKey || e.altKey || e.shiftKey)
      }
      onShortcut={() => setIsOpen((isOpen) => !isOpen)}
    >
      <PopoverStyle />
      <Popover
        content={
          <div ref={dropdownRef}>
            <FilterDropdown
              filters={filters}
              setIsOpen={setIsOpen}
              key={keyRef.current}
              setPortaledElements={setPortaledElements}
            />
          </div>
        }
        canEscapeKeyClose
        popoverClassName="filter-dropdown"
        isOpen={isOpen}
        placement="bottom-start"
        onClosing={() => {
          prevOpenRef.current = false;
        }}
      >
        <div>
          <Popover
            content={<>{portaledElements}</>}
            canEscapeKeyClose
            isOpen={!!portaledElements.length}
            position="bottom"
          >
            <Button
              ref={buttonRef}
              icon={<Icon name="filter_alt" />}
              onClick={() => {
                setIsOpen((isOpen) => !isOpen);
              }}
            >
              {label ?? 'Filter'}
            </Button>
          </Popover>
        </div>
      </Popover>
    </ShortcutHandler>
  );
});

const DropdownMenuContainer = styled.div`
  ${IconWrapper} {
    margin-left: 0 !important;
  }
`;

const TextInputWrapper = styled.div`
  display: flex;
  flex-direction: row;
  flex-gap: 12px;

  > *:first-child {
    flex-grow: 1;
  }

  input {
    background-color: ${Colors.popoverBackground()};
    padding: 12px 16px;

    &,
    :focus,
    :active,
    :hover {
      box-shadow: none;
      background-color: ${Colors.popoverBackground()};
    }
  }
`;

type FilterDropdownMenuItemProps = React.ComponentProps<typeof MenuItem> & {
  menuKey: string;
  index: number;
};
export const FilterDropdownMenuItem = React.memo(
  ({menuKey, index, ...rest}: FilterDropdownMenuItemProps) => {
    const divRef = React.useRef<HTMLDivElement | null>(null);
    React.useLayoutEffect(() => {
      if (rest.active) {
        if (divRef.current) {
          divRef.current?.scrollIntoView?.({block: 'center'});
        }
      }
    }, [rest.active]);
    return (
      <div
        role="option"
        id={itemId(menuKey, index)}
        aria-selected={rest.active ? 'true' : 'false'}
        ref={divRef}
      >
        <StyledMenuItem {...rest} />
      </div>
    );
  },
);

const StyledMenuItem = styled(MenuItem)`
  &.bp5-active:focus {
    box-shadow: initial;
  }
`;

const SlashShortcut = styled.div`
  border-radius: 4px;
  padding: 0px 6px;
  background: ${Colors.backgroundLight()};
  color: ${Colors.textLight()};
`;

const PopoverStyle = createGlobalStyle`
  .filter-dropdown.filter-dropdown.filter-dropdown.filter-dropdown {
    border-radius: 8px;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    .bp5-popover-content {
      border-radius: 8px;
    }
  }
  
  .bp5-overlay-content {
    max-width: 100%;
  }
`;

function itemId(menuKey: string, index: number) {
  return `item-${menuKey}-${index}`;
}
