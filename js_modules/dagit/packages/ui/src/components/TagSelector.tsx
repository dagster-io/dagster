import React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {Checkbox} from './Checkbox';
import {Colors} from './Colors';
import {Icon} from './Icon';
import {MenuItem, Menu} from './Menu';
import {Popover} from './Popover';
import {Tag} from './Tag';

type TagProps = {
  close: (ev: React.SyntheticEvent<HTMLDivElement>) => void;
};
type DropdownItemProps = {
  toggle: () => void;
  selected: boolean;
};
type Props = {
  allTags: string[];
  selectedTags: string[];
  setSelectedTags: (tags: React.SetStateAction<string[]>) => void;
  renderTag?: (tag: string, tagProps: TagProps) => JSX.Element;
  renderDropdown?: (dropdown: JSX.Element) => JSX.Element;
  renderDropdownItem?: (tag: string, dropdownItemProps: DropdownItemProps) => JSX.Element;
  dropdownStyles?: React.CSSProperties;
};

const defaultRenderTag = (tag: string, tagProps: TagProps) => {
  return (
    <Tag>
      <Box flex={{direction: 'row', gap: 4, justifyContent: 'space-between', alignItems: 'center'}}>
        <span>{tag}</span>
        <Box style={{cursor: 'pointer'}} onClick={tagProps.close}>
          <Icon name="close" />
        </Box>
      </Box>
    </Tag>
  );
};

const defaultRenderDropdownItem = (tag: string, dropdownItemProps: DropdownItemProps) => {
  return (
    <MenuItem
      text={
        <Box flex={{alignItems: 'center', gap: 8}}>
          <Checkbox
            checked={dropdownItemProps.selected}
            onChange={() => {}}
            onClick={(ev) => {
              ev.stopPropagation();
            }}
          />
          <span>{tag}</span>
        </Box>
      }
      onClick={dropdownItemProps.toggle}
    />
  );
};

export const TagSelector = ({
  allTags,
  selectedTags,
  setSelectedTags,
  renderTag,
  renderDropdownItem,
  renderDropdown,
  dropdownStyles,
}: Props) => {
  const [isDropdownOpen, setIsDropdownOpen] = React.useState(false);
  const dropdown = React.useMemo(() => {
    const dropdownContent = (
      <Box
        style={{
          maxHeight: '500px',
          overflowY: 'auto',
          ...dropdownStyles,
        }}
      >
        {allTags.map((tag) => {
          const selected = selectedTags.includes(tag);
          const toggle = () => {
            setSelectedTags(
              selected ? selectedTags.filter((t) => t !== tag) : [...selectedTags, tag],
            );
          };
          if (renderDropdownItem) {
            return <div key={tag}>{renderDropdownItem(tag, {toggle, selected})}</div>;
          }
          return defaultRenderDropdownItem(tag, {toggle, selected});
        })}
      </Box>
    );
    if (renderDropdown) {
      return renderDropdown(dropdownContent);
    }
    return <Menu>{dropdownContent}</Menu>;
  }, [allTags, dropdownStyles, renderDropdown, renderDropdownItem, selectedTags, setSelectedTags]);

  const dropdownContainer = React.useRef<HTMLDivElement>(null);

  return (
    <Popover
      placement="bottom"
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
      <Box
        as={Container}
        padding={{vertical: 4, horizontal: 6 as any}}
        flex={{gap: 6, alignItems: 'center'}}
        onClick={() => {
          setIsDropdownOpen((isOpen) => !isOpen);
        }}
      >
        <Box flex={{grow: 1, gap: 6}}>
          {selectedTags.map((tag) =>
            (renderTag || defaultRenderTag)(tag, {
              close: (ev) => {
                setSelectedTags((tags) => tags.filter((t) => t !== tag));
                ev.stopPropagation();
              },
            }),
          )}
        </Box>
        <div style={{cursor: 'pointer'}}>
          <Icon name={isDropdownOpen ? 'expand_less' : 'expand_more'} />
        </div>
      </Box>
    </Popover>
  );
};

const Container = styled.div`
  border: 1px solid ${Colors.Gray300};
  border-radius: 8px;
`;
