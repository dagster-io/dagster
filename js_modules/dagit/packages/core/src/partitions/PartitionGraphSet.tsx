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
  StepSelector,
  PARTITION_GRAPH_FRAGMENT,
} from './PartitionGraphUtils';
import {PartitionGraphSetRunFragment} from './types/PartitionGraphSetRunFragment';

const _reverseSortRunCompare = (
  a: PartitionGraphSetRunFragment,
  b: PartitionGraphSetRunFragment,
) => {
  if (!a.stats || a.stats.__typename !== 'RunStatsSnapshot' || !a.stats.startTime) {
    return 1;
  }
  if (!b.stats || b.stats.__typename !== 'RunStatsSnapshot' || !b.stats.startTime) {
    return -1;
  }
  return b.stats.startTime - a.stats.startTime;
};

export const PartitionGraphSet: React.FC<{
  partitions: {name: string; runs: PartitionGraphSetRunFragment[]}[];
  isJob: boolean;
}> = React.memo(({partitions, isJob}) => {
  const allStepKeys = getStepKeys(partitions);
  const [hiddenStepKeys, setHiddenStepKeys] = React.useState<string[]>([]);

  const partitionNames = partitions.map((x) => x.name);

  const jobDurationData = {};
  const stepDurationData = {};
  const jobMaterializationData = {};
  const stepMaterializationData = {};
  const jobExpectationSuccessData = {};
  const stepExpectationSuccessData = {};
  const jobExpectationFailureData = {};
  const stepExpectationFailureData = {};
  const jobExpectationRateData = {};
  const stepExpectationRateData = {};

  partitions.forEach((partition) => {
    if (partition.runs && partition.runs.length) {
      const toSort = partition.runs.slice();
      toSort.sort(_reverseSortRunCompare);
      const latestRun = toSort[0];
      jobDurationData[partition.name] = getPipelineDurationForRun(latestRun);
      stepDurationData[partition.name] = getStepDurationsForRun(latestRun);
      jobMaterializationData[partition.name] = getPipelineMaterializationCountForRun(latestRun);
      stepMaterializationData[partition.name] = getStepMaterializationCountForRun(latestRun);
      jobExpectationSuccessData[partition.name] = getPipelineExpectationSuccessForRun(latestRun);
      stepExpectationSuccessData[partition.name] = getStepExpectationSuccessForRun(latestRun);
      jobExpectationFailureData[partition.name] = getPipelineExpectationFailureForRun(latestRun);
      stepExpectationFailureData[partition.name] = getStepExpectationFailureForRun(latestRun);
      jobExpectationRateData[partition.name] = getPipelineExpectationRateForRun(latestRun);
      stepExpectationRateData[partition.name] = getStepExpectationRateForRun(latestRun);
    }
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
          partitionNames={partitionNames}
          jobDataByPartition={jobDurationData}
          stepDataByPartition={stepDurationData}
          hiddenStepKeys={hiddenStepKeys}
        />

        <PartitionGraph
          isJob={isJob}
          title="Materialization Count by Partition"
          yLabel="Number of materializations"
          partitionNames={partitionNames}
          jobDataByPartition={jobMaterializationData}
          stepDataByPartition={stepMaterializationData}
          hiddenStepKeys={hiddenStepKeys}
        />
        <PartitionGraph
          isJob={isJob}
          title="Expectation Successes by Partition"
          yLabel="Number of successes"
          partitionNames={partitionNames}
          jobDataByPartition={jobExpectationSuccessData}
          stepDataByPartition={stepExpectationSuccessData}
          hiddenStepKeys={hiddenStepKeys}
        />
        <PartitionGraph
          isJob={isJob}
          title="Expectation Failures by Partition"
          yLabel="Number of failures"
          partitionNames={partitionNames}
          jobDataByPartition={jobExpectationFailureData}
          stepDataByPartition={stepExpectationFailureData}
          hiddenStepKeys={hiddenStepKeys}
        />
        <PartitionGraph
          isJob={isJob}
          title="Expectation Rate by Partition"
          yLabel="Rate of success"
          partitionNames={partitionNames}
          jobDataByPartition={jobExpectationRateData}
          stepDataByPartition={stepExpectationRateData}
          hiddenStepKeys={hiddenStepKeys}
        />
      </div>
    </PartitionContentContainer>
  );
});

export const PARTITION_GRAPH_SET_RUN_FRAGMENT = gql`
  fragment PartitionGraphSetRunFragment on PipelineRun {
    id
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
