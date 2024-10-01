import {
  Box,
  Checkbox,
  Colors,
  Icon,
  Menu,
  MenuDivider,
  MenuItem,
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
}: {
  allPartitions: string[];
  selectedPartitions: string[];
  setSelectedPartitions: (tags: string[]) => void;
  health: PartitionStatusHealthSource;
  setShowCreatePartition?: (show: boolean) => void;
  isDynamic: boolean;
  placeholder?: string;
  mode?: 'single' | 'multiple';
}) => {
  const dotForPartitionKey = React.useCallback(
    (partitionKey: string) => {
      const index = allPartitions.indexOf(partitionKey);
      if ('ranges' in health) {
        return <AssetPartitionStatusDot status={partitionStatusAtIndex(health.ranges, index)} />;
      } else {
        return (
          <RunStatusDot
            size={10}
            status={health.runStatusForPartitionKey(partitionKey, index) || RunStatus.NOT_STARTED}
          />
        );
      }
    },
    [allPartitions, health],
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
          return (
            <label>
              <MenuItem
                tagName="div"
                data-testid={testId(`menu-item-${tag}`)}
                onClick={dropdownItemProps.toggle}
                text={
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns:
                        mode === 'multiple' ? 'auto auto minmax(0, 1fr)' : 'auto minmax(0, 1fr)',
                      alignItems: 'center',
                      gap: 12,
                    }}
                  >
                    {mode === 'multiple' && (
                      <Checkbox
                        checked={dropdownItemProps.selected}
                        onChange={() => {
                          // no-op, handled by click on parent, this just silences React warning
                        }}
                      />
                    )}
                    {dotForPartitionKey(tag)}
                    <div data-tooltip={tag} data-tooltip-style={DropdownItemTooltipStyle}>
                      <MiddleTruncate text={tag} />
                    </div>
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
          const isAllSelected = allTags.every((t) => selectedPartitions.includes(t));
          return (
            <Menu style={{width}}>
              <Box padding={4}>
                {isDynamic && setShowCreatePartition && (
                  <>
                    <Box flex={{direction: 'column'}}>
                      <MenuItem
                        tagName="div"
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
                        <MenuItem
                          tagName="div"
                          text={
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
                          }
                        />
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
        [isDynamic, selectedPartitions, setSelectedPartitions, setShowCreatePartition, mode],
      )}
      renderTagList={(tags) => {
        if (tags.length > 4) {
          return <span>{tags.length} partitions selected</span>;
        }
        return tags;
      }}
      searchPlaceholder="Filter partitions"
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
