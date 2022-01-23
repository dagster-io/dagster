import {ButtonWIP, IconWIP, MenuItemWIP, MenuWIP, Popover} from '@dagster-io/ui';
import * as React from 'react';

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
      <ButtonWIP
        rightIcon={<IconWIP name="expand_more" />}
      >{`Partition Set: ${selected.name}`}</ButtonWIP>
    </Popover>
  );
};
