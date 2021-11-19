import {gql} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {PartitionGraph} from './PartitionGraph';
import {
  getPipelineDurationForRun,
  getPipelineExpectationFailureForRun,
  getPipelineExpectationRateForRun,
  getPipelineExpectationSuccessForRun,
  getPipelineMaterializationCountForRun,
  getStepDurationsForRun,
  getStepExpectationFailureForRun,
  getStepExpectationRateForRun,
  getStepExpectationSuccessForRun,
  getStepMaterializationCountForRun,
  PARTITION_GRAPH_FRAGMENT,
  StepSelector,
} from './PartitionGraphUtils';
import {PartitionGraphSetRunFragment} from './types/PartitionGraphSetRunFragment';

export const PartitionGraphSet: React.FC<{
  partitions: {name: string; runs: PartitionGraphSetRunFragment[]}[];
  isJob: boolean;
}> = React.memo(({partitions, isJob}) => {
  const allStepKeys = getStepKeys(partitions);
  const [hiddenStepKeys, setHiddenStepKeys] = React.useState<string[]>([]);

  const runsByPartitionName = {};
  partitions.forEach((partition) => {
    runsByPartitionName[partition.name] = partition.runs;
  });

  return (
    <PartitionContentContainer>
      <StepSelector
        isJob={isJob}
        all={allStepKeys}
        hidden={hiddenStepKeys}
        onChangeHidden={setHiddenStepKeys}
      />

      <div style={{flex: 1}}>
        <PartitionGraph
          isJob={isJob}
          title="Execution Time by Partition"
          yLabel="Execution time (secs)"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineDurationForRun}
          getStepDataForRun={getStepDurationsForRun}
          hiddenStepKeys={hiddenStepKeys}
        />
        <PartitionGraph
          isJob={isJob}
          title="Materialization Count by Partition"
          yLabel="Number of materializations"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineMaterializationCountForRun}
          getStepDataForRun={getStepMaterializationCountForRun}
          hiddenStepKeys={hiddenStepKeys}
        />
        <PartitionGraph
          isJob={isJob}
          title="Expectation Successes by Partition"
          yLabel="Number of successes"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationSuccessForRun}
          getStepDataForRun={getStepExpectationSuccessForRun}
          hiddenStepKeys={hiddenStepKeys}
        />
        <PartitionGraph
          isJob={isJob}
          title="Expectation Failures by Partition"
          yLabel="Number of failures"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationFailureForRun}
          getStepDataForRun={getStepExpectationFailureForRun}
          hiddenStepKeys={hiddenStepKeys}
        />
        <PartitionGraph
          isJob={isJob}
          title="Expectation Rate by Partition"
          yLabel="Rate of success"
          runsByPartitionName={runsByPartitionName}
          getPipelineDataForRun={getPipelineExpectationRateForRun}
          getStepDataForRun={getStepExpectationRateForRun}
          hiddenStepKeys={hiddenStepKeys}
        />
      </div>
    </PartitionContentContainer>
  );
});

export const PARTITION_GRAPH_SET_RUN_FRAGMENT = gql`
  fragment PartitionGraphSetRunFragment on PipelineRun {
    id
    status
    tags {
      key
      value
    }
    ...PartitionGraphFragment
  }
  ${PARTITION_GRAPH_FRAGMENT}
`;

const PartitionContentContainer = styled.div`
  display: flex;
  flex-direction: row;
  position: relative;
  margin: 0 auto;
`;

function getStepKeys(partitions: {name: string; runs: PartitionGraphSetRunFragment[]}[]) {
  const allStepKeys = new Set<string>();
  partitions.forEach((partition) => {
    partition.runs.forEach((run) => {
      run.stepStats.forEach((stat) => {
        allStepKeys.add(stat.stepKey);
      });
    });
  });
  return Array.from(allStepKeys).sort();
}
