import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {Checkbox} from './Checkbox';
import {Colors} from './Colors';
import {Icon} from './Icon';
import {MenuItem, Menu} from './Menu';
import {Popover} from './Popover';
import {Tag} from './Tag';
import {TextInput, TextInputStyles} from './TextInput';
import {Container as VirtualContainer, Inner, Row} from './VirtualizedTable';
import {useViewport} from './useViewport';

export type TagSelectorTagProps = {
  remove: (ev: React.SyntheticEvent<HTMLDivElement>) => void;
};
export type TagSelectorDropdownItemProps = {
  toggle: () => void;
  selected: boolean;
};
export type TagSelectorDropdownProps = {
  width: string;
  allTags: string[];
};
type Props = {
  placeholder?: React.ReactNode;
  allTags: string[];
  selectedTags: string[];
  setSelectedTags: (tags: string[]) => void;
  renderTag?: (tag: string, tagProps: TagSelectorTagProps) => React.ReactNode;
  renderTagList?: (tags: React.ReactNode[]) => React.ReactNode;
  renderDropdown?: (
    dropdown: React.ReactNode,
    dropdownProps: TagSelectorDropdownProps,
  ) => React.ReactNode;
  renderDropdownItem?: (
    tag: string,
    dropdownItemProps: TagSelectorDropdownItemProps,
  ) => React.ReactNode;
  dropdownStyles?: React.CSSProperties;
  rowWidth?: number;
  rowHeight?: number;
};

const defaultRenderTag = (tag: string, tagProps: TagSelectorTagProps) => {
  return (
    <Tag key={tag}>
      <Box flex={{direction: 'row', gap: 4, justifyContent: 'space-between', alignItems: 'center'}}>
        <span>{tag}</span>
        <Box style={{cursor: 'pointer'}} onClick={tagProps.remove}>
          <Icon name="close" />
        </Box>
      </Box>
    </Tag>
  );
};

const defaultRenderDropdownItem = (
  tag: string,
  dropdownItemProps: TagSelectorDropdownItemProps,
) => {
  return (
    <label>
      <MenuItem
        text={
          <Box flex={{alignItems: 'center', gap: 8}}>
            <Checkbox checked={dropdownItemProps.selected} onChange={dropdownItemProps.toggle} />
            <span>{tag}</span>
          </Box>
        }
        tagName="div"
      />
    </label>
  );
};

const MENU_ITEM_HEIGHT = 32;

export const TagSelector = ({
  allTags,
  placeholder,
  selectedTags,
  setSelectedTags,
  renderTag,
  renderDropdownItem,
  renderDropdown,
  dropdownStyles,
  renderTagList,
  rowHeight = MENU_ITEM_HEIGHT,
}: Props) => {
  const [isDropdownOpen, setIsDropdownOpen] = React.useState(false);
  const {viewport, containerProps} = useViewport();

  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const rowVirtualizer = useVirtualizer({
    count: allTags.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (_) => rowHeight,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  const dropdown = React.useMemo(() => {
    const dropdownContent = (
      <VirtualContainer
        ref={parentRef}
        style={{
          maxHeight: '300px',
          overflowY: 'auto',
          ...dropdownStyles,
        }}
      >
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, start, end}) => {
            const tag = allTags[index]!;
            function content() {
              const selected = selectedTags.includes(tag);
              const toggle = () => {
                setSelectedTags(
                  selected ? selectedTags.filter((t) => t !== tag) : [...selectedTags, tag],
                );
              };
              if (renderDropdownItem) {
                return <div>{renderDropdownItem(tag, {toggle, selected})}</div>;
              }
              return defaultRenderDropdownItem(tag, {toggle, selected});
            }
            return (
              <Row key={tag} $height={end - start} $start={start}>
                {content()}
              </Row>
            );
          })}
        </Inner>
      </VirtualContainer>
    );
    if (renderDropdown) {
      return renderDropdown(dropdownContent, {width: viewport.width + 'px', allTags});
    }
    return <Menu style={{width: viewport.width + 'px'}}>{dropdownContent}</Menu>;
  }, [
    allTags,
    dropdownStyles,
    items,
    renderDropdown,
    renderDropdownItem,
    selectedTags,
    setSelectedTags,
    totalHeight,
    viewport.width,
  ]);

  const dropdownContainer = React.useRef<HTMLDivElement>(null);

  const tagsContent = React.useMemo(() => {
    if (selectedTags.length === 0) {
      return <Placeholder>{placeholder || 'Select tags'}</Placeholder>;
    }
    const tags = selectedTags.map((tag) =>
      (renderTag || defaultRenderTag)(tag, {
        remove: (ev) => {
          setSelectedTags(selectedTags.filter((t) => t !== tag));
          ev.stopPropagation();
        },
      }),
    );
    if (renderTagList) {
      return renderTagList(tags);
    }
    return tags;
  }, [selectedTags, renderTagList, placeholder, renderTag, setSelectedTags]);

  return (
    <Popover
      placement="bottom-start"
      isOpen={isDropdownOpen}
      onInteraction={(nextOpenState, e) => {
        const target = e?.target;
        if (isDropdownOpen && target instanceof HTMLElement) {
          const isClickInside = dropdownContainer.current?.contains(target);
          if (!isClickInside) {
            setIsDropdownOpen(nextOpenState);
          }
        }
      }}
      content={<div ref={dropdownContainer}>{dropdown}</div>}
      targetTagName="div"
    >
      <Container
        onClick={() => {
          setIsDropdownOpen((isOpen) => !isOpen);
        }}
        {...containerProps}
      >
        <TagsContainer flex={{grow: 1, gap: 6}}>{tagsContent}</TagsContainer>
        <div style={{cursor: 'pointer'}}>
          <Icon name={isDropdownOpen ? 'expand_less' : 'expand_more'} />
        </div>
      </Container>
    </Popover>
  );
};

const Container = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;

  ${TextInputStyles}
`;

const Placeholder = styled.div`
  color: ${Colors.Gray400};
`;

const TagsContainer = styled(Box)`
  overflow-x: auto;

  &::-webkit-scrollbar {
    display: none;
  }
  scrollbar-width: none;
  -ms-overflow-style: none;
`;

export const TagSelectorWithSearch = (
  props: Props & {
    searchPlaceholder?: string;
  },
) => {
  const [search, setSearch] = React.useState('');
  const {
    allTags,
    selectedTags,
    setSelectedTags,
    rowHeight,
    renderDropdown,
    searchPlaceholder,
    ...rest
  } = props;
  const filteredTags = React.useMemo(() => {
    if (search.trim() === '') {
      return allTags;
    }
    return allTags.filter((tag) => tag.toLowerCase().includes(search.toLowerCase()));
  }, [allTags, search]);
  return (
    <TagSelector
      {...rest}
      allTags={filteredTags}
      selectedTags={selectedTags}
      setSelectedTags={setSelectedTags}
      dropdownStyles={{width: 'auto'}}
      renderDropdown={React.useCallback(
        (dropdownContent: React.ReactNode, dropdownProps: TagSelectorDropdownProps) => {
          return (
            <Menu style={{width: 'auto'}}>
              <Box flex={{direction: 'column'}}>
                <Box flex={{direction: 'column', grow: 1}} padding={{horizontal: 8}}>
                  <TextInput
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder={searchPlaceholder || 'Search'}
                    ref={(input) => {
                      if (input) {
                        input.focus();
                      }
                    }}
                  />
                </Box>
                {renderDropdown ? renderDropdown(dropdownContent, dropdownProps) : dropdownContent}
              </Box>
            </Menu>
          );
        },
        [renderDropdown, search, searchPlaceholder],
      )}
    />
  );
};
