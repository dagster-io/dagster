import {Spinner, Button, Dialog, Colors} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {CursorHistoryControls} from 'src/CursorControls';
import {TokenizingFieldValue} from 'src/TokenizingField';
import {PartitionGraphSet} from 'src/partitions/PartitionGraphSet';
import {PartitionPageSizeSelector} from 'src/partitions/PartitionPageSizeSelector';
import {PartitionRunMatrix} from 'src/partitions/PartitionRunMatrix';
import {PartitionSetSelector} from 'src/partitions/PartitionSetSelector';
import {PartitionsBackfillPartitionSelector} from 'src/partitions/PartitionsBackfill';
import {PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results} from 'src/partitions/types/PipelinePartitionsRootQuery';
import {useChunkedPartitionsQuery} from 'src/partitions/useChunkedPartitionsQuery';
import {RepoAddress} from 'src/workspace/types';

type PartitionSet = PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results;

interface PartitionViewProps {
  pipelineName: string;
  partitionSet: PartitionSet;
  partitionSets: PartitionSet[];
  onChangePartitionSet: (set: PartitionSet) => void;
  repoAddress: RepoAddress;
}

export const PartitionView: React.FunctionComponent<PartitionViewProps> = ({
  pipelineName,
  partitionSet,
  partitionSets,
  onChangePartitionSet,
  repoAddress,
}) => {
  const [pageSize, setPageSize] = React.useState<number | 'all'>(30);
  const [runTags, setRunTags] = React.useState<TokenizingFieldValue[]>([]);
  const [showBackfillSetup, setShowBackfillSetup] = React.useState(false);
  const {loading, partitions, paginationProps} = useChunkedPartitionsQuery(
    partitionSet.name,
    pageSize,
    runTags,
    repoAddress,
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
      <Dialog
        onClose={() => setShowBackfillSetup(false)}
        style={{width: 800, background: Colors.WHITE}}
        title={`Launch ${partitionSet.name} backfill`}
        isOpen={showBackfillSetup}
      >
        {showBackfillSetup && (
          <PartitionsBackfillPartitionSelector
            partitionSetName={partitionSet.name}
            pipelineName={pipelineName}
            onLaunch={(backfillId: string) => {
              setRunTags([{token: 'tag', value: `dagster/backfill=${backfillId}`}]);
              setShowBackfillSetup(false);
            }}
            repoAddress={repoAddress}
          />
        )}
      </Dialog>
      <PartitionPagerContainer>
        <PartitionSetSelector
          selected={partitionSet}
          partitionSets={partitionSets}
          onSelect={onChangePartitionSet}
        />
        <div style={{width: 10}} />
        <Button
          onClick={() => setShowBackfillSetup(!showBackfillSetup)}
          icon={IconNames.ADD}
          active={showBackfillSetup}
        >
          Launch a partition backfill
        </Button>
        {loading && (
          <div style={{marginLeft: 15, display: 'flex', alignItems: 'center'}}>
            <Spinner size={19} />
            <div style={{width: 5}} />
            Loading Partitions...
          </div>
        )}
        <div style={{flex: 1}} />
        <PartitionPageSizeSelector
          value={paginationProps.hasPrevCursor ? undefined : pageSize}
          onChange={(value) => {
            setPageSize(value);
            paginationProps.reset();
          }}
        />
        <div style={{width: 10}} />
        <CursorHistoryControls {...paginationProps} />
      </PartitionPagerContainer>
      <div style={{position: 'relative'}}>
        <PartitionRunMatrix
          partitions={partitions}
          pipelineName={pipelineName}
          repoAddress={repoAddress}
          runTags={runTags}
          setRunTags={setRunTags}
        />
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
