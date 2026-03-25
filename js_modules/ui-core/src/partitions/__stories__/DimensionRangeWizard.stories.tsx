import {Box, Colors} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import {useState} from 'react';

import {AssetPartitionStatus} from '../../assets/AssetPartitionStatus';
import {Range} from '../../assets/usePartitionHealthData';
import {PartitionDefinitionType} from '../../graphql/types';
import {DimensionRangeWizard} from '../DimensionRangeWizard';
import {PartitionStatusHealthSource} from '../PartitionStatus';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Partitions/DimensionRangeWizard',
  component: DimensionRangeWizard,
};

// --- Helpers ---

const generateDailyKeys = (startDate: string, count: number) =>
  Array.from({length: count}, (_, i) => dayjs(startDate).add(i, 'day').format('YYYY-MM-DD'));

const generateHourlyKeys = (startDate: string, count: number) =>
  Array.from({length: count}, (_, i) =>
    dayjs(startDate).add(i, 'hour').format('YYYY-MM-DDTHH:mm:ss'),
  );

const generateMonthlyKeys = (startDate: string, count: number) =>
  Array.from({length: count}, (_, i) => dayjs(startDate).add(i, 'month').format('YYYY-MM'));

const buildHealthRanges = (keys: string[], statusPattern: AssetPartitionStatus[]): Range[] => {
  const chunkSize = Math.ceil(keys.length / statusPattern.length);
  return statusPattern.map((status, i) => {
    const startIdx = i * chunkSize;
    const endIdx = Math.min((i + 1) * chunkSize - 1, keys.length - 1);
    return {
      start: {idx: startIdx, key: keys[startIdx] ?? ''},
      end: {idx: endIdx, key: keys[endIdx] ?? ''},
      value: [status],
    };
  });
};

const allMaterializedHealth = (keys: string[]): PartitionStatusHealthSource => ({
  ranges: [
    {
      start: {idx: 0, key: keys[0] ?? ''},
      end: {idx: keys.length - 1, key: keys[keys.length - 1] ?? ''},
      value: [AssetPartitionStatus.MATERIALIZED],
    },
  ],
});

const mixedHealth = (keys: string[]): PartitionStatusHealthSource => ({
  ranges: buildHealthRanges(keys, [
    AssetPartitionStatus.MATERIALIZED,
    AssetPartitionStatus.MISSING,
    AssetPartitionStatus.FAILED,
    AssetPartitionStatus.MATERIALIZED,
  ]),
});

// --- Data ---

const dailyKeys = generateDailyKeys('2024-01-01', 90);
const hourlyKeys = generateHourlyKeys('2024-06-01T00:00:00', 72);
const monthlyKeys = generateMonthlyKeys('2022-01', 24);
const nonDateKeys = Array.from(
  {length: 30},
  (_, i) => `partition_${i.toString().padStart(3, '0')}`,
);

// --- Wrapper ---

const StoryWrapper = ({
  partitionKeys,
  health,
  dimensionType,
  showQuickSelectOptionsForStatuses = true,
}: {
  partitionKeys: string[];
  health: PartitionStatusHealthSource;
  dimensionType: PartitionDefinitionType;
  showQuickSelectOptionsForStatuses?: boolean;
}) => {
  const [selected, setSelected] = useState<string[]>(partitionKeys);

  return (
    <Box padding={20} style={{maxWidth: 800}}>
      <DimensionRangeWizard
        selected={selected}
        setSelected={setSelected}
        partitionKeys={partitionKeys}
        health={health}
        dimensionType={dimensionType}
        showQuickSelectOptionsForStatuses={showQuickSelectOptionsForStatuses}
      />
      <Box margin={{top: 12}} style={{fontSize: 13, color: Colors.textLight()}}>
        {selected.length} of {partitionKeys.length} partitions selected
        {selected.length > 0 && selected.length <= 5 && <span>: {selected.join(', ')}</span>}
      </Box>
    </Box>
  );
};

// --- Stories ---

export const DailyPartitionsWithDateRangeFilter = () => (
  <StoryWrapper
    partitionKeys={dailyKeys}
    health={mixedHealth(dailyKeys)}
    dimensionType={PartitionDefinitionType.TIME_WINDOW}
  />
);

export const HourlyPartitionsWithDateRangeFilter = () => (
  <StoryWrapper
    partitionKeys={hourlyKeys}
    health={allMaterializedHealth(hourlyKeys)}
    dimensionType={PartitionDefinitionType.TIME_WINDOW}
  />
);

export const MonthlyPartitionsWithDateRangeFilter = () => (
  <StoryWrapper
    partitionKeys={monthlyKeys}
    health={mixedHealth(monthlyKeys)}
    dimensionType={PartitionDefinitionType.TIME_WINDOW}
  />
);

export const NonDatePartitionsNoDateFilter = () => (
  <StoryWrapper
    partitionKeys={nonDateKeys}
    health={allMaterializedHealth(nonDateKeys)}
    dimensionType={PartitionDefinitionType.TIME_WINDOW}
  />
);

export const WithoutQuickSelectButtons = () => (
  <StoryWrapper
    partitionKeys={dailyKeys}
    health={allMaterializedHealth(dailyKeys)}
    dimensionType={PartitionDefinitionType.TIME_WINDOW}
    showQuickSelectOptionsForStatuses={false}
  />
);

export const SmallDailyRange = () => {
  const keys = generateDailyKeys('2024-06-01', 7);
  return (
    <StoryWrapper
      partitionKeys={keys}
      health={mixedHealth(keys)}
      dimensionType={PartitionDefinitionType.TIME_WINDOW}
    />
  );
};

export const StaticPartitions = () => (
  <StoryWrapper
    partitionKeys={nonDateKeys}
    health={allMaterializedHealth(nonDateKeys)}
    dimensionType={PartitionDefinitionType.STATIC}
  />
);
