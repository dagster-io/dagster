import {
  Box,
  Checkbox,
  Colors,
  Icon,
  Menu,
  MenuDivider,
  MenuItem,
  MenuItemForInteractiveContent,
  MiddleTruncate,
  TagSelectorDropdownItemProps,
  TagSelectorDropdownProps,
  TagSelectorWithSearch,
} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {PartitionStatusHealthSource} from './PartitionStatus';
import {AssetPartitionStatusDot} from '../assets/AssetPartitionList';
import {partitionStatusAtIndex} from '../assets/usePartitionHealthData';
import {RunStatus} from '../graphql/types';
import {RunStatusDot} from '../runs/RunStatusDots';
import {testId} from '../testing/testId';

export const OrdinalPartitionSelector = ({
  allPartitions,
  selectedPartitions,
  setSelectedPartitions,
  setShowCreatePartition,
  isDynamic,
  health,
  placeholder,
  mode = 'multiple',
  disabled,
}: {
  allPartitions: string[];
  selectedPartitions: string[];
  setSelectedPartitions: (tags: string[]) => void;
  health: PartitionStatusHealthSource;
  setShowCreatePartition?: (show: boolean) => void;
  isDynamic: boolean;
  placeholder?: string;
  mode?: 'single' | 'multiple';
  disabled?: boolean;
}) => {
  const dotForPartitionKey = React.useCallback(
    (partitionKey: string) => {
      const index = allPartitions.indexOf(partitionKey);
      if ('ranges' in health) {
        return <AssetPartitionStatusDot status={partitionStatusAtIndex(health.ranges, index)} />;
      }
      return (
        <RunStatusDot
          size={10}
          status={health.runStatusForPartitionKey(partitionKey, index) || RunStatus.NOT_STARTED}
        />
      );
    },
    [allPartitions, health],
  );

  // Memoize selectedPartitions as a Set for O(1) lookups instead of O(n) includes()
  const selectedPartitionsSet = React.useMemo(
    () => new Set(selectedPartitions),
    [selectedPartitions],
  );

  return (
    <TagSelectorWithSearch
      allTags={allPartitions}
      selectedTags={selectedPartitions}
      setSelectedTags={setSelectedPartitions}
      placeholder={
        placeholder ||
        (setShowCreatePartition ? 'Select a partition or create one' : 'Select a partition')
      }
      renderDropdownItem={React.useCallback(
        (tag: string, dropdownItemProps: TagSelectorDropdownItemProps) => {
          const sharedContent = (
            <>
              {dotForPartitionKey(tag)}
              <div data-tooltip={tag} data-tooltip-style={DropdownItemTooltipStyle}>
                <MiddleTruncate text={tag} />
              </div>
            </>
          );

          if (mode === 'multiple') {
            return (
              <label key={tag}>
                <MenuItemForInteractiveContent data-testid={testId(`menu-item-${tag}`)}>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'auto auto minmax(0, 1fr)',
                      alignItems: 'center',
                      gap: 12,
                    }}
                  >
                    <Checkbox
                      checked={dropdownItemProps.selected}
                      onChange={() => {
                        dropdownItemProps.toggle();
                      }}
                    />
                    {sharedContent}
                  </div>
                </MenuItemForInteractiveContent>
              </label>
            );
          }

          return (
            <label key={tag}>
              <MenuItem
                onClick={() => dropdownItemProps.toggle()}
                data-testid={testId(`menu-item-${tag}`)}
                text={
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'auto auto minmax(0, 1fr)',
                      alignItems: 'center',
                      gap: 12,
                    }}
                  >
                    {sharedContent}
                  </div>
                }
              />
            </label>
          );
        },
        [dotForPartitionKey, mode],
      )}
      renderDropdown={React.useCallback(
        (dropdown: React.ReactNode, {width, allTags}: TagSelectorDropdownProps) => {
          // Use Set for O(1) lookup instead of O(n) includes() - critical for 100k+ partitions
          const isAllSelected = allTags.every((t) => selectedPartitionsSet.has(t));
          return (
            <Menu style={{width}}>
              <Box padding={4}>
                {isDynamic && setShowCreatePartition && (
                  <>
                    <Box flex={{direction: 'column'}}>
                      <MenuItem
                        text={
                          <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
                            <StyledIcon name="add" size={24} />
                            <span>Add partition</span>
                          </Box>
                        }
                        onClick={() => {
                          setShowCreatePartition(true);
                        }}
                      />
                    </Box>
                    <MenuDivider />
                  </>
                )}
                {allTags.length ? (
                  <>
                    {mode === 'multiple' && (
                      <label>
                        <MenuItemForInteractiveContent>
                          <Box flex={{alignItems: 'center', gap: 12}}>
                            <Checkbox
                              checked={isAllSelected}
                              onChange={() => {
                                if (isAllSelected) {
                                  setSelectedPartitions([]);
                                } else {
                                  setSelectedPartitions(allTags);
                                }
                              }}
                            />
                            <span>Select all ({allTags.length})</span>
                          </Box>
                        </MenuItemForInteractiveContent>
                      </label>
                    )}
                    {dropdown}
                  </>
                ) : (
                  <div style={{padding: '6px 6px 0px 6px', color: Colors.textLight()}}>
                    No matching partitions found
                  </div>
                )}
              </Box>
            </Menu>
          );
        },
        [isDynamic, selectedPartitionsSet, setSelectedPartitions, setShowCreatePartition, mode],
      )}
      renderTagList={(tags, totalCount) => {
        if (totalCount > 4) {
          return <span>{totalCount} partitions selected</span>;
        }
        return tags;
      }}
      searchPlaceholder="Filter partitions"
      disabled={disabled}
    />
  );
};

const StyledIcon = styled(Icon)`
  font-weight: 500;
`;

const DropdownItemTooltipStyle = JSON.stringify({
  background: Colors.backgroundLight(),
  border: `1px solid ${Colors.borderDefault()}`,
  color: Colors.textDefault(),
  fontSize: '14px',
});
