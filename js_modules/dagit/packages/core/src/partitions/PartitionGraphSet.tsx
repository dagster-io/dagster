import {gql} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../ui/Colors';

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

export const PartitionGraphSet: React.FunctionComponent<{
  partitions: {name: string; runs: PartitionGraphSetRunFragment[]}[];
  allStepKeys: string[];
}> = ({partitions, allStepKeys}) => {
  const [hiddenStepKeys, setHiddenStepKeys] = React.useState<string[]>([]);
  const durationGraph = React.useRef<any>(undefined);
  const materializationGraph = React.useRef<any>(undefined);
  const successGraph = React.useRef<any>(undefined);
  const failureGraph = React.useRef<any>(undefined);
  const rateGraph = React.useRef<any>(undefined);
  const graphs = [durationGraph, materializationGraph, successGraph, failureGraph, rateGraph];

  const onChangeHiddenStepKeys = (hiddenKeys: string[]) => {
    setHiddenStepKeys(hiddenKeys);

    graphs.forEach((graph) => {
      const chart = graph?.current?.getChartInstance();
      const datasets = chart?.data?.datasets || [];
      datasets.forEach((dataset: any, idx: number) => {
        const meta = chart.getDatasetMeta(idx);
        meta.hidden = hiddenKeys.includes(dataset.label);
      });
    });
  };

  const runsByPartitionName = {};
  partitions.forEach((partition) => {
    runsByPartitionName[partition.name] = partition.runs;
  });

  return (
    <PartitionContentContainer>
      <div style={{flex: 1, minWidth: 450}}>
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
          <StepSelector
            all={allStepKeys}
            hidden={hiddenStepKeys}
            onChangeHidden={onChangeHiddenStepKeys}
          />
        </NavContainer>
      </div>
    </PartitionContentContainer>
  );
};

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

const NavContainer = styled.div`
  margin: 20px 0 0 10px;
  padding: 10px;
  background-color: #fff;
  border: 1px solid ${ColorsWIP.Gray200};
  overflow: auto;
`;

const PartitionContentContainer = styled.div`
  display: flex;
  flex-direction: row;
  position: relative;
  margin: 0 auto;
`;
