import {Box, Heading, Icon} from '@dagster-io/ui-components';
import {Dispatch, SetStateAction} from 'react';

import {DimensionRangeWizard} from './DimensionRangeWizard';
import {PartitionDateFilter} from './partitionDateFilter';
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
  dateFilter,
  onDateFilterChange,
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
  dateFilter?: PartitionDateFilter | null;
  onDateFilterChange?: (filter: PartitionDateFilter | null) => void;
}) => {
  // The date window is a single value shared by the caller, so only hand it to
  // a lone time-window dimension - the one case where the wizard renders the
  // date range dropdown and the user can change or clear it.
  const dateFilterDimension =
    selections.length === 1 && selections[0]?.dimension.type === PartitionDefinitionType.TIME_WINDOW
      ? selections[0].dimension
      : null;

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
              <Heading size={14} weight={600}>
                {range.dimension.name}
              </Heading>
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
            dateFilter={range.dimension === dateFilterDimension ? dateFilter : undefined}
            onDateFilterChange={
              range.dimension === dateFilterDimension ? onDateFilterChange : undefined
            }
          />
        </Box>
      ))}
    </>
  );
};
