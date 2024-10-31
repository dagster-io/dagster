import {
  buildAutomationConditionEvaluationNode,
  buildPartitionedAssetConditionEvaluationNode,
  buildSpecificPartitionAssetConditionEvaluationNode,
  buildUnpartitionedAssetConditionEvaluationNode,
} from '../../../graphql/types';
import {PolicyEvaluationTable} from '../PolicyEvaluationTable';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/PolicyEvaluationTable',
  component: PolicyEvaluationTable,
};

export const NonPartitioned = () => {
  const nodes = [
    buildUnpartitionedAssetConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'a',
      description: 'parent condition',
      childUniqueIds: ['b'],
    }),
    buildUnpartitionedAssetConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'b',
      description: 'child condition',
    }),
  ];

  return (
    <PolicyEvaluationTable
      evaluationNodes={nodes}
      assetKeyPath={['foo', 'bar']}
      evaluationId="1"
      rootUniqueId="a"
      isLegacyEvaluation
      selectPartition={() => {}}
    />
  );
};

export const NewTableStyle = () => {
  const nodes = [
    buildAutomationConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'a',
      userLabel: 'parent condition',
      expandedLabel: ['(must be)', 'something'],
      isPartitioned: false,
      numTrue: 0,
      childUniqueIds: ['b', 'c'],
    }),
    buildAutomationConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'b',
      userLabel: 'child condition',
      expandedLabel: ['(a OR b)', 'NOT', '(c OR d)'],
      numTrue: 0,
      isPartitioned: false,
    }),
    buildAutomationConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'c',
      userLabel: null,
      expandedLabel: ['(e OR f)', 'NOT', '(g OR h)'],
      numTrue: 1,
      isPartitioned: false,
    }),
  ];

  return (
    <PolicyEvaluationTable
      evaluationNodes={nodes}
      assetKeyPath={['foo', 'bar']}
      evaluationId="1"
      rootUniqueId="a"
      isLegacyEvaluation={false}
      selectPartition={() => {}}
    />
  );
};

export const Partitioned = () => {
  const nodes = [
    buildPartitionedAssetConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'a',
      description: 'hi i am partitioned',
      numCandidates: 3,
      childUniqueIds: ['b'],
    }),
    buildPartitionedAssetConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'b',
      description: 'child condition',
      numCandidates: 3,
    }),
  ];

  return (
    <PolicyEvaluationTable
      evaluationNodes={nodes}
      assetKeyPath={['foo', 'bar']}
      evaluationId="1"
      rootUniqueId="a"
      isLegacyEvaluation
      selectPartition={() => {}}
    />
  );
};

export const SpecificPartition = () => {
  const nodes = [
    buildSpecificPartitionAssetConditionEvaluationNode({
      uniqueId: 'a',
      description: 'parent condition',
      childUniqueIds: ['b'],
    }),
    buildSpecificPartitionAssetConditionEvaluationNode({
      uniqueId: 'b',
      description: 'child condition',
    }),
  ];

  return (
    <PolicyEvaluationTable
      evaluationNodes={nodes}
      assetKeyPath={['foo', 'bar']}
      evaluationId="1"
      rootUniqueId="a"
      isLegacyEvaluation
      selectPartition={() => {}}
    />
  );
};
