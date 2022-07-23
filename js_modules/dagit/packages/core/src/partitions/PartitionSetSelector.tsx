import {Button, Icon, MenuItem, Menu, Popover} from '@dagster-io/ui';
import * as React from 'react';

import {PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results} from './types/PipelinePartitionsRootQuery';

type PartitionSet = PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results;

export const PartitionSetSelector: React.FC<{
  selected: PartitionSet;
  partitionSets: PartitionSet[];
  onSelect: (partitionSet: PartitionSet) => void;
}> = ({partitionSets, selected, onSelect}) => {
  const [open, setOpen] = React.useState(false);
  return (
    <Popover
      isOpen={open}
      onInteraction={setOpen}
      position="bottom-left"
      content={
        <Menu style={{minWidth: 280}}>
          {partitionSets.map((partitionSet, idx) => (
            <MenuItem
              key={idx}
              onClick={() => onSelect(partitionSet)}
              active={selected.name === partitionSet.name}
              icon="view_list"
              text={<div>{partitionSet.name}</div>}
            />
          ))}
        </Menu>
      }
    >
      <Button rightIcon={<Icon name="expand_more" />}>{`Partition Set: ${selected.name}`}</Button>
    </Popover>
  );
};
