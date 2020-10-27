import {Colors} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import styled from 'styled-components/macro';

import {TokenizingFieldValue} from 'src/TokenizingField';
import {PartitionGraph} from 'src/partitions/PartitionGraph';
import {
  PIPELINE_LABEL,
  PARTITION_GRAPH_FRAGMENT,
  NavSectionHeader,
  NavSection,
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
} from 'src/partitions/PartitionGraphUtils';
import {PartitionGraphSetPartitionFragment} from 'src/partitions/types/PartitionGraphSetPartitionFragment';
import {RunsFilter} from 'src/runs/RunsFilter';

export const PartitionGraphSet: React.FunctionComponent<{
  partitions: PartitionGraphSetPartitionFragment[];
  allStepKeys: string[];
}> = ({partitions, allStepKeys}) => {
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

export const PARTITION_GRAPH_SET_PARTITION_FRAGMENT = gql`
  fragment PartitionGraphSetPartitionFragment on Partition {
    name
    runs {
      status
      tags {
        key
        value
      }
      ...PartitionGraphFragment
    }
  }
  ${PARTITION_GRAPH_FRAGMENT}
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

const applyFilter = (
  filter: TokenizingFieldValue,
  run: PartitionGraphSetPartitionFragment['runs'][0],
) => {
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
