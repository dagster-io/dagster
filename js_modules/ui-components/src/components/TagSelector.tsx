import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components';

import {BaseTag} from './BaseTag';
import {Box} from './Box';
import {Checkbox} from './Checkbox';
import {Colors} from './Color';
import {Icon} from './Icon';
import {Menu, MenuItemForInteractiveContent} from './Menu';
import {MiddleTruncate} from './MiddleTruncate';
import {Popover} from './Popover';
import {TextInput} from './TextInput';
import {Inner, Row, Container as VirtualContainer} from './VirtualizedTable';
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
  renderTagList?: (tags: React.ReactNode[], totalCount: number) => React.ReactNode;
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
  closeOnSelect?: boolean;
  usePortal?: boolean;
  disabled?: boolean;
};

const defaultRenderTag = (tag: string, tagProps: TagSelectorTagProps, disabled?: boolean) => {
  return (
    <BaseTag
      fillColor={Colors.backgroundGray()}
      textColor={disabled ? Colors.textDisabled() : Colors.textDefault()}
      label={
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: `1fr ${disabled ? '' : 'auto'}`,
            gap: 4,
            justifyContent: 'space-between',
            alignItems: 'center',
            maxWidth: '120px',
          }}
          data-tooltip={tag}
          data-tooltip-style={TagSelectorDefaultTagTooltipStyle}
        >
          <MiddleTruncate text={tag} />
          {disabled ? null : (
            <Box style={{cursor: 'pointer'}} onClick={tagProps.remove}>
              <Icon name="close" color={disabled ? Colors.textDisabled() : Colors.textDefault()} />
            </Box>
          )}
        </div>
      }
    />
  );
};

const defaultRenderDropdownItem = (
  tag: string,
  dropdownItemProps: TagSelectorDropdownItemProps,
) => {
  return (
    <MenuItemForInteractiveContent>
      <Box flex={{alignItems: 'center', gap: 8}}>
        <Checkbox
          checked={dropdownItemProps.selected}
          onChange={dropdownItemProps.toggle}
          label={<span>{tag}</span>}
        />
      </Box>
    </MenuItemForInteractiveContent>
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
  closeOnSelect,
  usePortal,
  disabled,
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

  // Memoize selectedTags as a Set for O(1) lookups instead of O(n) includes()
  const selectedTagsSet = React.useMemo(() => new Set(selectedTags), [selectedTags]);

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
            const tagAtIndex = allTags[index];
            if (!tagAtIndex) {
              return null;
            }

            function content(tag: string) {
              // Use Set for O(1) lookup instead of O(n) includes()
              const selected = selectedTagsSet.has(tag);
              const toggle = () => {
                setSelectedTags(
                  selected ? selectedTags.filter((t) => t !== tag) : [...selectedTags, tag],
                );
                if (closeOnSelect) {
                  setIsDropdownOpen(false);
                }
              };
              if (renderDropdownItem) {
                return <div>{renderDropdownItem(tag, {toggle, selected})}</div>;
              }
              return defaultRenderDropdownItem(tag, {toggle, selected});
            }

            return (
              <Row key={tagAtIndex} $height={end - start} $start={start}>
                {content(tagAtIndex)}
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
    closeOnSelect,
    dropdownStyles,
    items,
    renderDropdown,
    renderDropdownItem,
    selectedTags,
    selectedTagsSet,
    setSelectedTags,
    totalHeight,
    viewport.width,
  ]);

  const dropdownContainer = React.useRef<HTMLDivElement>(null);

  const tagsContent = React.useMemo(() => {
    if (selectedTags.length === 0) {
      return <Placeholder>{placeholder || 'Select tags'}</Placeholder>;
    }
    // Only render up to MAX_RENDERED_TAGS elements to avoid performance issues
    // with large selections (e.g., 100k partitions). The renderTagList callback
    // receives totalCount so it can display "X items selected" accurately.
    const MAX_RENDERED_TAGS = 100;
    const tagsToRender = selectedTags.slice(0, MAX_RENDERED_TAGS);
    const totalCount = selectedTags.length;

    const tags = tagsToRender.map((tag) =>
      (renderTag || defaultRenderTag)(
        tag,
        {
          remove: (ev) => {
            setSelectedTags(selectedTags.filter((t) => t !== tag));
            ev.stopPropagation();
          },
        },
        disabled,
      ),
    );
    if (renderTagList) {
      return renderTagList(tags, totalCount);
    }
    return tags;
  }, [selectedTags, renderTagList, placeholder, renderTag, setSelectedTags, disabled]);

  return (
    <Popover
      placement="bottom-start"
      isOpen={isDropdownOpen && !disabled}
      onInteraction={(nextOpenState, e) => {
        const target = e?.target;
        if (isDropdownOpen && target instanceof HTMLElement) {
          const isClickInside = dropdownContainer.current?.contains(target);
          if (!isClickInside) {
            setIsDropdownOpen(nextOpenState);
          }
        }
      }}
      content={<div>{dropdown}</div>}
      targetTagName="div"
      onOpening={rowVirtualizer.measure}
      onOpened={rowVirtualizer.measure}
      usePortal={usePortal}
    >
      <TagSelectorContainer
        onClick={() => {
          setIsDropdownOpen((isOpen) => !isOpen);
        }}
        $disabled={disabled}
        {...containerProps}
      >
        <TagSelectorTagsContainer flex={{grow: 1, gap: 6}}>{tagsContent}</TagSelectorTagsContainer>
        <div style={{cursor: 'pointer'}}>
          <Icon
            name={isDropdownOpen ? 'expand_less' : 'expand_more'}
            color={disabled ? Colors.textDisabled() : Colors.textDefault()}
          />
        </div>
      </TagSelectorContainer>
    </Popover>
  );
};

export const TagSelectorContainer = styled.div<{$disabled?: boolean}>`
  display: flex;
  flex-direction: row;
  align-items: center;

  /* Inline TextInputStyles */
  background-color: ${Colors.backgroundDefault()};
  border: none;
  box-shadow: ${Colors.borderDefault()} inset 0px 0px 0px 1px;
  outline: none;
  border-radius: 8px;
  color: ${Colors.textDefault()};
  flex-grow: 1;
  font-size: 14px;
  line-height: 20px;
  padding: 6px 6px 6px 12px;
  margin: 0;
  transition: box-shadow 150ms;

  ::placeholder {
    color: ${Colors.textLighter()};
  }

  :disabled {
    box-shadow: ${Colors.keylineDefault()} inset 0px 0px 0px 1px;
    background-color: ${Colors.backgroundLight()};
    color: ${Colors.textDisabled()};
  }

  :disabled::placeholder {
    color: ${Colors.textDisabled()};
  }

  :focus {
    box-shadow:
      ${Colors.borderDefault()} inset 0px 0px 0px 1px,
      ${Colors.keylineDefault()} inset 2px 2px 1.5px,
      ${Colors.focusRing()} 0 0 0 2px;
    outline: none;
  }

  min-height: 32px;
  padding: 4px 8px;

  ${({$disabled}) =>
    $disabled &&
    `
      box-shadow:
      ${Colors.borderDisabled()} inset 0px 0px 0px 1px,
      ${Colors.keylineDefault()} inset 2px 2px 1.5px;
      background-color: ${Colors.backgroundDisabled()};
       color: ${Colors.textDisabled()};
    `}
`;

const Placeholder = styled.div`
  color: ${Colors.textDisabled()};
`;

export const TagSelectorTagsContainer = styled(Box)`
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
    rowHeight: _rowHeight,
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

export const TagSelectorDefaultTagTooltipStyle = JSON.stringify({
  background: Colors.backgroundDefault(),
  border: `1px solid ${Colors.borderDefault()}`,
  color: Colors.textDefault(),
});
