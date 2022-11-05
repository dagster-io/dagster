import {Box, Button, Checkbox, Icon} from '@dagster-io/ui';
import groupBy from 'lodash/groupBy';
import * as React from 'react';

import {PartitionRangeInput} from './PartitionRangeInput';
import {PartitionState, PartitionStatus} from './PartitionStatus';

export const PartitionRangeWizard: React.FC<{
  selected: string[];
  setSelected: (selected: string[]) => void;
  all: string[];
  partitionData: {[name: string]: PartitionState};
}> = ({selected, setSelected, all, partitionData}) => {
  const byState = React.useMemo(() => {
    return groupBy(Object.keys(partitionData), (name) => partitionData[name]);
  }, [partitionData]);

  const successPartitions = byState[PartitionState.SUCCESS] || [];
  const failedPartitions = byState[PartitionState.FAILURE] || [];
  const missingPartitions = byState[PartitionState.MISSING] || [];

  return (
    <>
      <Box>
        Select the set of partitions to include in the backfill. You can specify a range using the
        text selector, or by dragging a range selection in the status indicator.
      </Box>
      <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
          {successPartitions.length ? (
            <Checkbox
              style={{marginBottom: 0, marginLeft: 10}}
              checked={successPartitions.every((x) => selected.includes(x))}
              label="Succeeded"
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                if (e.target.checked) {
                  setSelected(Array.from(new Set(selected.concat(successPartitions))));
                } else {
                  setSelected(selected.filter((x) => !successPartitions.includes(x)));
                }
              }}
            />
          ) : null}
          {failedPartitions.length ? (
            <Checkbox
              style={{marginBottom: 0, marginLeft: 10}}
              checked={failedPartitions.every((x) => selected.includes(x))}
              label="Failed"
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                if (e.target.checked) {
                  setSelected(Array.from(new Set(selected.concat(failedPartitions))));
                } else {
                  setSelected(selected.filter((x) => !failedPartitions.includes(x)));
                }
              }}
            />
          ) : null}
          {missingPartitions.length ? (
            <Checkbox
              style={{marginBottom: 0, marginLeft: 10}}
              checked={missingPartitions.every((x) => selected.includes(x))}
              label="Missing"
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                if (e.target.checked) {
                  setSelected(Array.from(new Set(selected.concat(missingPartitions))));
                } else {
                  setSelected(selected.filter((x) => !missingPartitions.includes(x)));
                }
              }}
            />
          ) : null}
        </Box>
        <Button
          icon={<Icon name="close" />}
          disabled={!all.length}
          style={{marginBottom: 0, marginLeft: 10}}
          small={true}
          onClick={() => {
            setSelected([]);
          }}
        >
          Clear selection
        </Button>
      </Box>
      <PartitionRangeInput value={selected} partitionNames={all} onChange={setSelected} />
      <Box margin={{top: 8}}>
        <PartitionStatus
          partitionNames={all}
          partitionData={partitionData}
          selected={selected}
          onSelect={setSelected}
        />
      </Box>
    </>
  );
};
