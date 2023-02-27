import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {Checkbox} from './Checkbox';
import {Colors} from './Colors';
import {Icon} from './Icon';
import {Menu, MenuDivider, MenuItem} from './Menu';
import {TagSelector} from './TagSelector';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TagSelector',
  component: TagSelector,
} as Meta;

const allTags = ['NY', 'NJ', 'VC', 'FL', 'AL', 'CA'];

export const Basic = () => {
  const [selectedTags, setSelectedTags] = React.useState<string[]>(['NY', 'NJ']);
  return (
    <TagSelector
      allTags={['NY', 'NJ', 'VC', 'FL', 'AL', 'CA']}
      selectedTags={selectedTags}
      setSelectedTags={setSelectedTags}
    />
  );
};

export const Styled = () => {
  const [selectedTags, setSelectedTags] = React.useState<string[]>(allTags.slice(0, 2));
  const isAllSelected = selectedTags.length === 6;
  return (
    <TagSelector
      allTags={['NY', 'NJ', 'VC', 'FL', 'AL', 'CA']}
      selectedTags={selectedTags}
      setSelectedTags={setSelectedTags}
      renderDropdownItem={(tag, dropdownItemProps) => {
        return (
          <MenuItem
            text={
              <Box as="label" flex={{alignItems: 'center', gap: 12}}>
                <Checkbox
                  checked={dropdownItemProps.selected}
                  onChange={dropdownItemProps.toggle}
                />
                <Dot color={Math.random() > 0.5 ? Colors.Green500 : Colors.Gray500} />
                <span>{tag}</span>
              </Box>
            }
          />
        );
      }}
      renderDropdown={(dropdown) => {
        const toggleAll = () => {
          if (isAllSelected) {
            setSelectedTags([]);
          } else {
            setSelectedTags(allTags);
          }
        };
        return (
          <Menu>
            <Box padding={4}>
              <Box flex={{direction: 'column'}} padding={{horizontal: 8}}>
                <Box flex={{direction: 'row', alignItems: 'center'}}>
                  <StyledIcon name="add" size={24} />
                  <span>Create Partition</span>
                </Box>
              </Box>
              <MenuDivider />
              <MenuItem
                text={
                  <Box as="label" flex={{alignItems: 'center', gap: 8}}>
                    <Checkbox checked={isAllSelected} onChange={toggleAll} />
                    <span>Select All ({allTags.length})</span>
                  </Box>
                }
              />
              {dropdown}
            </Box>
          </Menu>
        );
      }}
    />
  );
};

const StyledIcon = styled(Icon)`
  font-weight: 500;
`;

const Dot = styled.div<{color: string}>`
  width: 8px;
  height: 8px;
  border-radius: 4px;
  background-color: ${({color}) => color};
  display: inline-block;
`;
