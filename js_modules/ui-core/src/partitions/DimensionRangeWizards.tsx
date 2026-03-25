import {Box, Icon, Subheading} from '@dagster-io/ui-components';
import {Dispatch, SetStateAction} from 'react';

import {DimensionRangeWizard} from './DimensionRangeWizard';
import {
  PartitionDimensionSelection,
  PartitionHealthDataMerged,
} from '../assets/usePartitionHealthData';
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
          {range.dimension.name !== 'default' ? (
            <Box flex={{alignItems: 'center', gap: 8}} padding={{vertical: 4}}>
              <Icon name="partition" />
              <Subheading>{range.dimension.name}</Subheading>
            </Box>
          ) : null}
          <DimensionRangeWizard
            repoAddress={repoAddress}
            refetch={refetch}
            partitionKeys={range.dimension.partitionKeys}
            health={{
              ranges: displayedHealth.rangesForSingleDimension(
                idx,
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
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
            showQuickSelectOptionsForStatuses={selections.length === 1}
          />
        </Box>
      ))}
    </>
  );
};
