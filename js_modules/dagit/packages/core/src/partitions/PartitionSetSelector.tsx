import {Button} from '@blueprintjs/core';
import * as React from 'react';

import {MenuItemWIP, MenuWIP} from '../ui/Menu';
import {Popover} from '../ui/Popover';

import {PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results} from './types/PipelinePartitionsRootQuery';

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
      position="bottom-left"
      content={
        <MenuWIP style={{minWidth: 280}}>
          {partitionSets.map((partitionSet, idx) => (
            <MenuItemWIP
              key={idx}
              onClick={() => onSelect(partitionSet)}
              active={selected.name === partitionSet.name}
              icon="view_list"
              text={<div>{partitionSet.name}</div>}
            />
          ))}
        </MenuWIP>
      }
    >
      <Button text={`Partition Set: ${selected.name}`} rightIcon="caret-down" />
    </Popover>
  );
};
