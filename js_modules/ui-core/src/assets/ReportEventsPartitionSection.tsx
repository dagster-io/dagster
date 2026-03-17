import {Box, Checkbox, Subheading} from '@dagster-io/ui-components';
import {Dispatch, SetStateAction} from 'react';

import {partitionCountString} from './AssetNodePartitionCounts';
import {
  PartitionDimensionSelection,
  PartitionHealthDataMerged,
  keyCountInSelections,
} from './usePartitionHealthData';
import {DimensionRangeWizards} from '../partitions/DimensionRangeWizards';
import {testId} from '../testing/testId';
import {ToggleableSection} from '../ui/ToggleableSection';
import {RepoAddress} from '../workspace/types';

interface Props {
  selections: PartitionDimensionSelection[];
  setSelections: Dispatch<SetStateAction<PartitionDimensionSelection[]>>;
  assetHealth: PartitionHealthDataMerged;
  assetPartitionDef: {
    name: string | null;
    dimensionTypes: {
      name: string;
      dynamicPartitionsDefinitionName: string | null;
    }[];
  } | null;
  repoAddress: RepoAddress;
  setLastRefresh: (ts: number) => void;
  healthFilters?: {
    filterFailed: boolean;
    setFilterFailed: (v: boolean) => void;
    filterMissing: boolean;
    setFilterMissing: (v: boolean) => void;
  };
}

export const ReportEventsPartitionSection = ({
  selections,
  setSelections,
  assetHealth,
  assetPartitionDef,
  repoAddress,
  setLastRefresh,
  healthFilters,
}: Props) => {
  return (
    <ToggleableSection
      isInitiallyOpen={true}
      title={
        <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
          <Subheading>Partition selection</Subheading>
          <span>{partitionCountString(keyCountInSelections(selections))}</span>
        </Box>
      }
    >
      <DimensionRangeWizards
        repoAddress={repoAddress}
        refetch={async () => setLastRefresh(Date.now())}
        selections={selections}
        setSelections={setSelections}
        displayedHealth={assetHealth}
        displayedPartitionDefinition={assetPartitionDef}
      />
      {healthFilters && selections.length > 1 && (
        <Box padding={{vertical: 8, horizontal: 20}} flex={{direction: 'column', gap: 8}}>
          <Checkbox
            data-testid={testId('failed-only-checkbox')}
            label="Report only failed partitions within selection"
            checked={healthFilters.filterFailed}
            onChange={() => healthFilters.setFilterFailed(!healthFilters.filterFailed)}
          />
          <Checkbox
            data-testid={testId('missing-only-checkbox')}
            label="Report only missing partitions within selection"
            checked={healthFilters.filterMissing}
            onChange={() => healthFilters.setFilterMissing(!healthFilters.filterMissing)}
          />
        </Box>
      )}
    </ToggleableSection>
  );
};
