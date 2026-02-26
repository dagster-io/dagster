import {useState} from 'react';
import styled from 'styled-components';

import {Box} from '../Box';
import {Checkbox} from '../Checkbox';
import {Colors} from '../Color';
import {Icon} from '../Icon';
import {Menu, MenuDivider, MenuItemForInteractiveContent} from '../Menu';
import {TagSelector, TagSelectorWithSearch} from '../TagSelector';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TagSelector',
  component: TagSelector,
};

const allTags = [
  'NY',
  'NJ',
  'VC',
  'FL',
  'AL',
  'CALIFORNIA_SUPER_LONG_TAG',
  'ANOTHER_REALLY_LONG_TAG',
  'LONG_TAGS_ARE_GREAT_FOR_TESTING_DECEMBER_2020',
];

export const Basic = () => {
  const [selectedTags, setSelectedTags] = useState<string[]>(['NY', 'NJ']);
  return (
    <TagSelector allTags={allTags} selectedTags={selectedTags} setSelectedTags={setSelectedTags} />
  );
};

export const WithSearch = () => {
  const [selectedTags, setSelectedTags] = useState<string[]>(['NY', 'NJ']);
  return (
    <TagSelectorWithSearch
      allTags={allTags}
      selectedTags={selectedTags}
      setSelectedTags={setSelectedTags}
    />
  );
};

export const Styled = () => {
  const [selectedTags, setSelectedTags] = useState<string[]>(allTags.slice(0, 2));
  const isAllSelected = selectedTags.length === allTags.length;

  return (
    <TagSelector
      allTags={allTags}
      selectedTags={selectedTags}
      setSelectedTags={setSelectedTags}
      placeholder="Select a partition or create one"
      renderDropdownItem={(tag, dropdownItemProps) => {
        return (
          <MenuItemForInteractiveContent>
            <Box flex={{alignItems: 'center', gap: 12}}>
              <Checkbox
                checked={dropdownItemProps.selected}
                onChange={dropdownItemProps.toggle}
                label={
                  <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                    <Dot color={Math.random() > 0.5 ? Colors.accentGreen() : Colors.accentGray()} />
                    <span>{tag}</span>
                  </Box>
                }
              />
            </Box>
          </MenuItemForInteractiveContent>
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
                  <span>Add Partition</span>
                </Box>
              </Box>
              <MenuDivider />
              <MenuItemForInteractiveContent>
                <Box flex={{alignItems: 'center', gap: 8}}>
                  <Checkbox
                    checked={isAllSelected}
                    onChange={toggleAll}
                    label={<span>Select all ({allTags.length})</span>}
                  />
                </Box>
              </MenuItemForInteractiveContent>
              {dropdown}
            </Box>
          </Menu>
        );
      }}
      renderTagList={(tags, totalCount) => {
        if (totalCount > 3) {
          return <span>{totalCount} partitions selected</span>;
        }
        return tags;
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
