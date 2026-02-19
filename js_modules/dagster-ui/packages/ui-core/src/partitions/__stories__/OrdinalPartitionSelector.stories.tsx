import {Box} from '@dagster-io/ui-components';
import {useState} from 'react';

import {AssetPartitionStatus} from '../../assets/AssetPartitionStatus';
import {Range} from '../../assets/usePartitionHealthData';
import {RunStatus} from '../../graphql/types';
import {OrdinalPartitionSelector} from '../OrdinalPartitionSelector';
import {PartitionStatusHealthSource} from '../PartitionStatus';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Partitions/OrdinalPartitionSelector',
  component: OrdinalPartitionSelector,
};

// Mock partition keys for testing
const smallPartitionList = ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'];

const mediumPartitionList = Array.from({length: 20}, (_, i) => {
  const date = new Date('2024-01-01');
  date.setDate(date.getDate() + i);
  const isoDate = date.toISOString().split('T')[0];
  return isoDate || '';
});

const largePartitionList = Array.from(
  {length: 100},
  (_, i) => `partition_${i.toString().padStart(3, '0')}`,
);

// Health sources for different scenarios
const createAssetHealthSource = (ranges: Range[]): PartitionStatusHealthSource => ({
  ranges,
});

const createOpHealthSource = (
  statusMap: Record<string, RunStatus>,
): PartitionStatusHealthSource => ({
  runStatusForPartitionKey: (key: string) => statusMap[key] || RunStatus.NOT_STARTED,
});

// Healthy partitions (all materialized)
const allHealthyRanges: Range[] = [
  {
    start: {idx: 0, key: '2024-01-01'},
    end: {
      idx: smallPartitionList.length - 1,
      key: '2024-01-05',
    },
    value: [AssetPartitionStatus.MATERIALIZED],
  },
];

// Mixed health status
const mixedHealthRanges: Range[] = [
  {
    start: {idx: 0, key: '2024-01-01'},
    end: {idx: 4, key: '2024-01-05'},
    value: [AssetPartitionStatus.MATERIALIZED],
  },
  {
    start: {idx: 5, key: '2024-01-06'},
    end: {idx: 9, key: '2024-01-10'},
    value: [AssetPartitionStatus.MISSING],
  },
  {
    start: {idx: 10, key: '2024-01-11'},
    end: {idx: 14, key: '2024-01-15'},
    value: [AssetPartitionStatus.FAILED],
  },
  {
    start: {idx: 15, key: '2024-01-16'},
    end: {idx: 19, key: '2024-01-20'},
    value: [AssetPartitionStatus.MATERIALIZING],
  },
];

// Op health with run statuses
const opRunStatusMap: Record<string, RunStatus> = {
  '2024-01-01': RunStatus.SUCCESS,
  '2024-01-02': RunStatus.SUCCESS,
  '2024-01-03': RunStatus.FAILURE,
  '2024-01-04': RunStatus.STARTED,
  '2024-01-05': RunStatus.NOT_STARTED,
};

export const MultipleSelectionDefault = () => {
  const [selectedPartitions, setSelectedPartitions] = useState<string[]>([]);

  return (
    <Box padding={20} style={{maxWidth: 600}}>
      <OrdinalPartitionSelector
        allPartitions={mediumPartitionList}
        selectedPartitions={selectedPartitions}
        setSelectedPartitions={setSelectedPartitions}
        health={createAssetHealthSource(mixedHealthRanges)}
        isDynamic={false}
        mode="multiple"
      />
      <Box margin={{top: 12}} style={{fontSize: 14, color: '#666'}}>
        Selected: {selectedPartitions.length > 0 ? selectedPartitions.join(', ') : 'None'}
      </Box>
    </Box>
  );
};

export const SingleSelectionMode = () => {
  const [selectedPartition, setSelectedPartition] = useState<string | undefined>(undefined);

  return (
    <Box padding={20} style={{maxWidth: 600}}>
      <OrdinalPartitionSelector
        allPartitions={smallPartitionList}
        selectedPartitions={selectedPartition ? [selectedPartition] : []}
        setSelectedPartitions={(partitions) => {
          setSelectedPartition(partitions[partitions.length - 1]);
        }}
        health={createAssetHealthSource(allHealthyRanges)}
        isDynamic={false}
        mode="single"
      />
      <Box margin={{top: 12}} style={{fontSize: 14, color: '#666'}}>
        Selected: {selectedPartition || 'None'}
      </Box>
    </Box>
  );
};

export const DynamicPartitionsWithAddButton = () => {
  const [selectedPartitions, setSelectedPartitions] = useState<string[]>([]);
  const [showCreatePartition, setShowCreatePartition] = useState(false);

  return (
    <Box padding={20} style={{maxWidth: 600}}>
      <OrdinalPartitionSelector
        allPartitions={smallPartitionList}
        selectedPartitions={selectedPartitions}
        setSelectedPartitions={setSelectedPartitions}
        health={createAssetHealthSource(allHealthyRanges)}
        isDynamic={true}
        setShowCreatePartition={setShowCreatePartition}
        mode="multiple"
      />
      <Box margin={{top: 12}} style={{fontSize: 14, color: '#666'}}>
        Selected: {selectedPartitions.length > 0 ? selectedPartitions.join(', ') : 'None'}
      </Box>
      {showCreatePartition && (
        <Box
          margin={{top: 12}}
          padding={12}
          style={{
            background: '#f0f0f0',
            borderRadius: 4,
            fontSize: 14,
          }}
        >
          Create partition dialog would appear here
          <button onClick={() => setShowCreatePartition(false)} style={{marginLeft: 12}}>
            Close
          </button>
        </Box>
      )}
    </Box>
  );
};

export const WithRunStatusHealth = () => {
  const [selectedPartitions, setSelectedPartitions] = useState<string[]>(['2024-01-01']);

  return (
    <Box padding={20} style={{maxWidth: 600}}>
      <OrdinalPartitionSelector
        allPartitions={smallPartitionList}
        selectedPartitions={selectedPartitions}
        setSelectedPartitions={setSelectedPartitions}
        health={createOpHealthSource(opRunStatusMap)}
        isDynamic={false}
        mode="multiple"
      />
      <Box margin={{top: 12}} style={{fontSize: 14, color: '#666'}}>
        Selected: {selectedPartitions.join(', ')}
      </Box>
      <Box margin={{top: 8}} style={{fontSize: 12, color: '#999'}}>
        Shows run status dots: Success (green), Failure (red), Started (blue), Not Started (gray)
      </Box>
    </Box>
  );
};

export const ManyPartitionsSelected = () => {
  const [selectedPartitions, setSelectedPartitions] = useState<string[]>(
    mediumPartitionList.slice(0, 15),
  );

  return (
    <Box padding={20} style={{maxWidth: 600}}>
      <OrdinalPartitionSelector
        allPartitions={mediumPartitionList}
        selectedPartitions={selectedPartitions}
        setSelectedPartitions={setSelectedPartitions}
        health={createAssetHealthSource(mixedHealthRanges)}
        isDynamic={false}
        mode="multiple"
      />
      <Box margin={{top: 12}} style={{fontSize: 14, color: '#666'}}>
        When more than 4 partitions are selected, it shows a count instead of listing them
      </Box>
    </Box>
  );
};

export const LargePartitionList = () => {
  const [selectedPartitions, setSelectedPartitions] = useState<string[]>([]);

  const largeHealthRanges: Range[] = [
    {
      start: {idx: 0, key: 'partition_000'},
      end: {idx: 29, key: 'partition_029'},
      value: [AssetPartitionStatus.MATERIALIZED],
    },
    {
      start: {idx: 30, key: 'partition_030'},
      end: {idx: 59, key: 'partition_059'},
      value: [AssetPartitionStatus.MISSING],
    },
    {
      start: {idx: 60, key: 'partition_060'},
      end: {idx: 99, key: 'partition_099'},
      value: [AssetPartitionStatus.FAILED],
    },
  ];

  return (
    <Box padding={20} style={{maxWidth: 600}}>
      <OrdinalPartitionSelector
        allPartitions={largePartitionList}
        selectedPartitions={selectedPartitions}
        setSelectedPartitions={setSelectedPartitions}
        health={createAssetHealthSource(largeHealthRanges)}
        isDynamic={false}
        mode="multiple"
        placeholder="Select from 100 partitions"
      />
      <Box margin={{top: 12}} style={{fontSize: 14, color: '#666'}}>
        Selected: {selectedPartitions.length} partitions
      </Box>
    </Box>
  );
};

export const CustomPlaceholder = () => {
  const [selectedPartitions, setSelectedPartitions] = useState<string[]>([]);

  return (
    <Box padding={20} style={{maxWidth: 600}}>
      <OrdinalPartitionSelector
        allPartitions={mediumPartitionList}
        selectedPartitions={selectedPartitions}
        setSelectedPartitions={setSelectedPartitions}
        health={createAssetHealthSource(mixedHealthRanges)}
        isDynamic={false}
        mode="multiple"
        placeholder="Choose date partitions to materialize"
      />
      <Box margin={{top: 12}} style={{fontSize: 14, color: '#666'}}>
        Custom placeholder text example
      </Box>
    </Box>
  );
};

export const DisabledState = () => {
  const [selectedPartitions, setSelectedPartitions] = useState<string[]>([
    '2024-01-01',
    '2024-01-02',
  ]);

  return (
    <Box padding={20} style={{maxWidth: 600}}>
      <OrdinalPartitionSelector
        allPartitions={smallPartitionList}
        selectedPartitions={selectedPartitions}
        setSelectedPartitions={setSelectedPartitions}
        health={createAssetHealthSource(allHealthyRanges)}
        isDynamic={false}
        mode="multiple"
        disabled={true}
      />
      <Box margin={{top: 12}} style={{fontSize: 14, color: '#666'}}>
        Disabled state - selector is not interactive
      </Box>
    </Box>
  );
};

export const EmptyPartitionList = () => {
  const [selectedPartitions, setSelectedPartitions] = useState<string[]>([]);

  return (
    <Box padding={20} style={{maxWidth: 600}}>
      <OrdinalPartitionSelector
        allPartitions={[]}
        selectedPartitions={selectedPartitions}
        setSelectedPartitions={setSelectedPartitions}
        health={createAssetHealthSource([])}
        isDynamic={true}
        setShowCreatePartition={() => {}}
        mode="multiple"
      />
      <Box margin={{top: 12}} style={{fontSize: 14, color: '#666'}}>
        No partitions available - shows &ldquo;No matching partitions found&rdquo; in dropdown
      </Box>
    </Box>
  );
};

export const WithSearchFiltering = () => {
  const [selectedPartitions, setSelectedPartitions] = useState<string[]>([]);

  return (
    <Box padding={20} style={{maxWidth: 600}}>
      <OrdinalPartitionSelector
        allPartitions={largePartitionList}
        selectedPartitions={selectedPartitions}
        setSelectedPartitions={setSelectedPartitions}
        health={createAssetHealthSource([
          {
            start: {idx: 0, key: 'partition_000'},
            end: {
              idx: largePartitionList.length - 1,
              key: 'partition_099',
            },
            value: [AssetPartitionStatus.MATERIALIZED],
          },
        ])}
        isDynamic={false}
        mode="multiple"
      />
      <Box margin={{top: 12}} style={{fontSize: 14, color: '#666'}}>
        Click to open and try the search/filter functionality with 100 partitions
      </Box>
    </Box>
  );
};
