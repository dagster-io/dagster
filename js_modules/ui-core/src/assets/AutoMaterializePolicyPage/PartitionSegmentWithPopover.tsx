import {Popover, Tag} from '@dagster-io/ui-components';

import {PartitionSubsetList} from './PartitionSubsetList';
import {AssetConditionEvaluationStatus} from '../../graphql/types';
import {numberFormatter} from '../../ui/formatters';

interface Props {
  description: string;
  numTrue: number;
  assetKeyPath: string[];
  evaluationId: string;
  nodeUniqueId: string;
  selectPartition?: (partitionKey: string | null) => void;
}

export const PartitionSegmentWithPopover = ({
  description,
  selectPartition,
  assetKeyPath,
  evaluationId,
  nodeUniqueId,
  numTrue,
}: Props) => {
  const tag = (
    <Tag intent={numTrue > 0 ? 'success' : 'none'} icon={numTrue > 0 ? 'check_circle' : undefined}>
      {numberFormatter.format(numTrue)} True
    </Tag>
  );

  if (numTrue === 0) {
    return tag;
  }

  return (
    <Popover
      interactionKind="hover"
      placement="bottom"
      hoverOpenDelay={50}
      hoverCloseDelay={50}
      content={
        <PartitionSubsetList
          description={description}
          status={AssetConditionEvaluationStatus.TRUE}
          assetKeyPath={assetKeyPath}
          evaluationId={evaluationId}
          nodeUniqueId={nodeUniqueId}
          selectPartition={selectPartition}
        />
      }
    >
      {tag}
    </Popover>
  );
};
