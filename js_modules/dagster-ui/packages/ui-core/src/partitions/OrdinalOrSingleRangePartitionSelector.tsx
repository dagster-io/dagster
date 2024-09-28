// eslint-disable-next-line no-restricted-imports
import {Box, ButtonGroup, Icon} from '@dagster-io/ui-components';
import {useState} from 'react';

import {OrdinalPartitionSelector} from './OrdinalPartitionSelector';
import {PartitionStatusHealthSource} from './PartitionStatus';
import {
  PartitionDimensionSelection,
  PartitionHealthDimension,
} from '../assets/usePartitionHealthData';
import {PartitionDefinitionType} from '../graphql/types';

const NONE = {key: '', idx: -1};

// Verify that there are no "NONE" values in the selected ranges.
// Note: An empty selection (no ranges and no keys) is valid.
export function isPartitionDimensionSelectionValid(s: PartitionDimensionSelection) {
  return (
    s.selectedKeys.length > 0 ||
    (s.selectedRanges.length > 0 && s.selectedRanges.every((r) => r.start.key && r.end.key))
  );
}

/**
 * This component allows the selection of a single range or list of keys in the dimension.
 * The `selection` can be null (all keys), a valid PartitionDimensionSelection, or an
 * or an invalid (incomplete) PartitionDimensionSelection.
 *
 * Using `null` for "All" allows the parent component to decide how to operate on that
 * selection. In some cases, treating it as a "meta-value" may be preferable to passing
 * every partition key, etc.
 *
 * This component does not yet support creating new partitions of dynamic dimensions.
 */
export const OrdinalOrSingleRangePartitionSelector = ({
  dimension,
  selection,
  setSelection,
  health,
}: {
  dimension: PartitionHealthDimension;
  selection?: PartitionDimensionSelection | null;
  setSelection: (selected: PartitionDimensionSelection | null) => void;
  health: PartitionStatusHealthSource;
}) => {
  const keys = selection?.selectedKeys || [];
  const range = selection?.selectedRanges[0] || {start: NONE, end: NONE};
  const rangeAllowed = dimension.type === PartitionDefinitionType.TIME_WINDOW;
  const partitionKeys = dimension.partitionKeys;

  const [mode, setMode] = useState<'all' | 'ordinal' | 'range'>(
    keys.length ? 'ordinal' : rangeAllowed && selection?.selectedRanges.length ? 'range' : 'all',
  );

  return (
    <Box style={{width: '100%', display: 'grid', gap: 8, gridTemplateColumns: 'auto 1fr'}}>
      <ButtonGroup
        activeItems={new Set([mode])}
        buttons={[
          {id: 'all', label: 'All'},
          {id: 'ordinal', label: 'Single'},
          ...(rangeAllowed ? [{id: 'range' as const, label: 'Range'}] : []),
        ]}
        onClick={(id) => {
          setSelection(id === 'all' ? null : {dimension, selectedKeys: [], selectedRanges: []});
          setMode(id);
        }}
      />
      {mode === 'ordinal' || (mode === 'all' && !rangeAllowed) ? (
        <OrdinalPartitionSelector
          placeholder={mode === 'all' ? `${partitionKeys.length} partitions` : `Select a partition`}
          allPartitions={partitionKeys}
          selectedPartitions={keys}
          health={health}
          isDynamic={false}
          setSelectedPartitions={(selectedKeys) => {
            setSelection({dimension, selectedKeys, selectedRanges: []});
            setMode('ordinal');
          }}
        />
      ) : (
        <Box
          style={{
            display: 'grid',
            alignItems: 'center',
            gridTemplateColumns: '1fr auto 1fr',
            gap: 8,
          }}
        >
          <OrdinalPartitionSelector
            mode="single"
            placeholder={mode === 'all' ? partitionKeys[0] : 'Select a starting partition'}
            allPartitions={partitionKeys}
            selectedPartitions={range.start.key ? [range.start.key] : []}
            health={health}
            isDynamic={false}
            setSelectedPartitions={([selectedKey]) => {
              setMode('range');
              setSelection({
                dimension,
                selectedKeys: [],
                selectedRanges: [
                  {
                    start: selectedKey
                      ? {key: selectedKey, idx: partitionKeys.indexOf(selectedKey)}
                      : NONE,
                    end: range.end,
                  },
                ],
              });
            }}
          />
          <Icon name="arrow_forward" />
          <OrdinalPartitionSelector
            mode="single"
            placeholder={
              mode === 'all'
                ? partitionKeys[partitionKeys.length - 1]
                : 'Select an ending partition'
            }
            allPartitions={partitionKeys}
            selectedPartitions={range.end.key ? [range.end.key] : []}
            health={health}
            isDynamic={false}
            setSelectedPartitions={([selectedKey]) => {
              setMode('range');
              setSelection({
                dimension,
                selectedKeys: [],
                selectedRanges: [
                  {
                    start: range.start,
                    end: selectedKey
                      ? {key: selectedKey, idx: partitionKeys.indexOf(selectedKey)}
                      : NONE,
                  },
                ],
              });
            }}
          />
        </Box>
      )}
    </Box>
  );
};
