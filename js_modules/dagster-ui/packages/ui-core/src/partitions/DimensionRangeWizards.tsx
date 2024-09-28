import {Box, Icon, Subheading} from '@dagster-io/ui-components';
import {Dispatch, SetStateAction} from 'react';

import {DimensionRangeWizard} from './DimensionRangeWizard';
import {
  PartitionDimensionSelection,
  PartitionHealthDataMerged,
} from '../assets/usePartitionHealthData';
import {PartitionDefinitionType} from '../graphql/types';
import {RepoAddress} from '../workspace/types';

export const DimensionRangeWizards = ({
  selections,
  setSelections,
  displayedHealth,
  displayedPartitionDefinition,
  repoAddress,
  refetch,
}: {
  selections: PartitionDimensionSelection[];
  setSelections: Dispatch<SetStateAction<PartitionDimensionSelection[]>>;
  displayedHealth: Pick<PartitionHealthDataMerged, 'rangesForSingleDimension'>;
  displayedPartitionDefinition?: {
    name: string | null;
    dimensionTypes: {
      name: string | undefined;
      dynamicPartitionsDefinitionName: string | null;
    }[];
  } | null;
  repoAddress?: RepoAddress;
  refetch?: () => Promise<void>;
}) => {
  return (
    <>
      {selections.map((range, idx) => (
        <Box
          key={range.dimension.name}
          border={idx < selections.length - 1 ? 'bottom' : undefined}
          padding={{vertical: 12, horizontal: 20}}
        >
          <Box as={Subheading} flex={{alignItems: 'center', gap: 8}}>
            <Icon name="partition" />
            {range.dimension.name}
          </Box>
          <Box>
            Select partitions to materialize.{' '}
            {range.dimension.type === PartitionDefinitionType.TIME_WINDOW
              ? 'Click and drag to select a range on the timeline.'
              : null}
          </Box>
          <DimensionRangeWizard
            repoAddress={repoAddress}
            refetch={refetch}
            partitionKeys={range.dimension.partitionKeys}
            health={{
              ranges: displayedHealth.rangesForSingleDimension(
                idx,
                selections.length === 2 ? selections[1 - idx]!.selectedRanges : undefined,
              ),
            }}
            dimensionType={range.dimension.type}
            selected={range.selectedKeys}
            setSelected={(selectedKeys) =>
              setSelections((selections) =>
                selections.map((r) => (r.dimension === range.dimension ? {...r, selectedKeys} : r)),
              )
            }
            dynamicPartitionsDefinitionName={
              displayedPartitionDefinition?.dimensionTypes.find(
                (d) => d.name === range.dimension.name,
              )?.dynamicPartitionsDefinitionName
            }
          />
        </Box>
      ))}
    </>
  );
};
