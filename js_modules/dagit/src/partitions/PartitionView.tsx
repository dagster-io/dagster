import {Spinner, Button} from '@blueprintjs/core';
import {Colors} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {CursorHistoryControls} from 'src/CursorControls';
import {
  PIPELINE_LABEL,
  StepSelector,
  getPipelineDurationForRun,
  getStepDurationsForRun,
  getPipelineExpectationFailureForRun,
  getPipelineExpectationSuccessForRun,
  getPipelineExpectationRateForRun,
  getPipelineMaterializationCountForRun,
  getStepExpectationFailureForRun,
  getStepExpectationRateForRun,
  getStepExpectationSuccessForRun,
  getStepMaterializationCountForRun,
} from 'src/RunGraphUtils';
import {TokenizingFieldValue} from 'src/TokenizingField';
import {PartitionGraph} from 'src/partitions/PartitionGraph';
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
import {RunsFilter} from 'src/runs/RunsFilter';

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
        <PartitionContent partitions={partitions} allStepKeys={Object.keys(allStepKeys)} />
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

const PartitionContent = ({
  partitions,
  allStepKeys,
}: {
  partitions: Partition[];
  allStepKeys: string[];
}) => {
  const initial: {[stepKey: string]: boolean} = {[PIPELINE_LABEL]: true};
  allStepKeys.forEach((stepKey) => (initial[stepKey] = true));
  const [selectedStepKeys, setSelectedStepKeys] = React.useState(initial);
  const [tokens, setTokens] = React.useState<TokenizingFieldValue[]>([]);
  const durationGraph = React.useRef<any>(undefined);
  const materializationGraph = React.useRef<any>(undefined);
  const successGraph = React.useRef<any>(undefined);
  const failureGraph = React.useRef<any>(undefined);
  const rateGraph = React.useRef<any>(undefined);
  const graphs = [durationGraph, materializationGraph, successGraph, failureGraph, rateGraph];

  const onStepChange = (selectedKeys: {[stepKey: string]: boolean}) => {
    setSelectedStepKeys(selectedKeys);
    graphs.forEach((graph) => {
      const chart = graph?.current?.chart?.current?.chartInstance;
      const datasets = chart?.data?.datasets || [];
      datasets.forEach((dataset: any, idx: number) => {
        const meta = chart.getDatasetMeta(idx);
        meta.hidden = dataset.label in selectedKeys ? !selectedKeys[dataset.label] : false;
      });
    });
  };

  const runsByPartitionName = {};
  partitions.forEach((partition) => {
    runsByPartitionName[partition.name] = partition.runs.filter(
      (run) => !tokens.length || tokens.every((token) => applyFilter(token, run)),
    );
  });

  return (
    <PartitionContentContainer>
      <div style={{flex: 1}}>
        <PartitionGraph
          title="Execution Time by Partition"
          yLabel="Execution time (secs)"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineDurationForRun}
          getStepDataForRun={getStepDurationsForRun}
          ref={durationGraph}
        />
        <PartitionGraph
          title="Materialization Count by Partition"
          yLabel="Number of materializations"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineMaterializationCountForRun}
          getStepDataForRun={getStepMaterializationCountForRun}
          ref={materializationGraph}
        />
        <PartitionGraph
          title="Expectation Successes by Partition"
          yLabel="Number of successes"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationSuccessForRun}
          getStepDataForRun={getStepExpectationSuccessForRun}
          ref={successGraph}
        />
        <PartitionGraph
          title="Expectation Failures by Partition"
          yLabel="Number of failures"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationFailureForRun}
          getStepDataForRun={getStepExpectationFailureForRun}
          ref={failureGraph}
        />
        <PartitionGraph
          title="Expectation Rate by Partition"
          yLabel="Rate of success"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationRateForRun}
          getStepDataForRun={getStepExpectationRateForRun}
          ref={rateGraph}
        />
      </div>
      <div style={{width: 450}}>
        <NavContainer>
          <NavSectionHeader>Run filters</NavSectionHeader>
          <NavSection>
            <RunsFilter tokens={tokens} onChange={setTokens} enabledFilters={['status', 'tag']} />
          </NavSection>
          <StepSelector selected={selectedStepKeys} onChange={onStepChange} />
        </NavContainer>
      </div>
    </PartitionContentContainer>
  );
};

const NavSectionHeader = styled.div`
  border-bottom: 1px solid ${Colors.GRAY5};
  margin-bottom: 10px;
  padding-bottom: 5px;
  display: flex;
`;
const NavSection = styled.div`
  margin-bottom: 30px;
`;
const NavContainer = styled.div`
  margin: 20px 0 0 10px;
  padding: 10px;
  background-color: #fff;
  border: 1px solid ${Colors.GRAY5};
  overflow: auto;
`;

const PartitionContentContainer = styled.div`
  display: flex;
  flex-direction: row;
  position: relative;
  max-width: 1600px;
  margin: 0 auto;
`;

const applyFilter = (filter: TokenizingFieldValue, run: Run) => {
  if (filter.token === 'id') {
    return run.runId === filter.value;
  }
  if (filter.token === 'status') {
    return run.status === filter.value;
  }
  if (filter.token === 'tag') {
    return run.tags.some((tag) => filter.value === `${tag.key}=${tag.value}`);
  }
  return true;
};

interface PartitionPagerProps {
  displayed: Partition[];
  pageSize: number | undefined;
  setPageSize: React.Dispatch<React.SetStateAction<number | undefined>>;
  hasPrevPage: boolean;
  hasNextPage: boolean;
  pushCursor: (nextCursor: string) => void;
  popCursor: () => void;
  setCursor: (cursor: string | undefined) => void;
}
