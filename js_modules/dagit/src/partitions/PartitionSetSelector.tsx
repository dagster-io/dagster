import {Button, Menu, MenuItem, Popover} from '@blueprintjs/core';
import * as React from 'react';

import {PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results} from 'src/partitions/types/PipelinePartitionsRootQuery';

type PartitionSet = PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results;

export const PartitionSetSelector: React.FunctionComponent<{
  selected: PartitionSet;
  partitionSets: PartitionSet[];
  onSelect: (partitionSet: PartitionSet) => void;
}> = ({partitionSets, selected, onSelect}) => {
  const [open, setOpen] = React.useState(false);
  return (
    <Popover
      isOpen={open}
      onInteraction={setOpen}
      minimal
      wrapperTagName="span"
      position={'bottom-left'}
      content={
        <Menu style={{minWidth: 280}}>
          {partitionSets.map((partitionSet, idx) => (
            <MenuItem
              key={idx}
              onClick={() => onSelect(partitionSet)}
              active={selected.name === partitionSet.name}
              icon={'git-repo'}
              text={<div>{partitionSet.name}</div>}
            />
          ))}
        </Menu>
      }
    >
      <Button text={`Partition Set: ${selected.name}`} rightIcon="caret-down" />
    </Popover>
  );
};
