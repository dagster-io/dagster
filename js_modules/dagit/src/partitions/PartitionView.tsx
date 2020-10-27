import {Spinner, Button} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {CursorHistoryControls} from 'src/CursorControls';
import {PartitionGraphSet} from 'src/partitions/PartitionGraphSet';
import {PartitionPageSizeSelector} from 'src/partitions/PartitionPageSizeSelector';
import {PartitionRunMatrix} from 'src/partitions/PartitionRunMatrix';
import {PartitionSetSelector} from 'src/partitions/PartitionSetSelector';
import {PartitionsBackfillPartitionSelector} from 'src/partitions/PartitionsBackfill';
import {
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results,
  PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs,
} from 'src/partitions/types/PartitionLongitudinalQuery';
import {PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results} from 'src/partitions/types/PipelinePartitionsRootQuery';
import {useChunkedPartitionsQuery} from 'src/partitions/useChunkedPartitionsQuery';

type PartitionSet = PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results;
type Partition = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results;
type Run = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs;

interface PartitionViewProps {
  pipelineName: string;
  partitionSet: PartitionSet;
  partitionSets: PartitionSet[];
  onChangePartitionSet: (set: PartitionSet) => void;
}

export const PartitionView: React.FunctionComponent<PartitionViewProps> = ({
  pipelineName,
  partitionSet,
  partitionSets,
  onChangePartitionSet,
}) => {
  const [pageSize, setPageSize] = React.useState<number | 'all'>(30);
  const [runTags, setRunTags] = React.useState<{[key: string]: string}>({});
  const [showBackfillSetup, setShowBackfillSetup] = React.useState(false);
  const {loading, partitions, paginationProps} = useChunkedPartitionsQuery(
    partitionSet.name,
    pageSize,
  );

  const allStepKeys = {};
  partitions.forEach((partition) => {
    partition.runs?.forEach((run) => {
      if (!run) {
        return;
      }
      run.stepStats.forEach((stat) => {
        allStepKeys[stat.stepKey] = true;
      });
    });
  });

  return (
    <div>
      {showBackfillSetup && (
        <PartitionsBackfillPartitionSelector
          partitionSetName={partitionSet.name}
          pipelineName={pipelineName}
          onLaunch={(backfillId: string) => {
            setRunTags({'dagster/backfill': backfillId});
            setShowBackfillSetup(false);
          }}
        />
      )}
      <PartitionPagerContainer>
        <PartitionSetSelector
          selected={partitionSet}
          partitionSets={partitionSets}
          onSelect={onChangePartitionSet}
        />
        <div style={{width: 10}} />
        <PartitionPageSizeSelector
          value={paginationProps.hasPrevCursor ? undefined : pageSize}
          onChange={(value) => {
            setPageSize(value);
            paginationProps.reset();
          }}
        />
        {loading && (
          <div style={{marginLeft: 15, display: 'flex', alignItems: 'center'}}>
            <Spinner size={19} />
            <div style={{width: 5}} />
            Loading Partitions...
          </div>
        )}
        <div style={{flex: 1}} />
        <Button
          onClick={() => setShowBackfillSetup(!showBackfillSetup)}
          icon={IconNames.ADD}
          active={showBackfillSetup}
        >
          Launch a partition backfill
        </Button>
        <div style={{width: 10}} />
        <CursorHistoryControls {...paginationProps} />
      </PartitionPagerContainer>
      <div style={{position: 'relative'}}>
        <PartitionRunMatrix pipelineName={pipelineName} partitions={partitions} runTags={runTags} />
        <PartitionGraphSet partitions={partitions} allStepKeys={Object.keys(allStepKeys)} />
      </div>
    </div>
  );
};

const PartitionPagerContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
`;
