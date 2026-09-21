import {
  buildAutomationConditionEvaluationNode,
  buildPartitionedAssetConditionEvaluationNode,
  buildSinceConditionMetadata,
  buildSpecificPartitionAssetConditionEvaluationNode,
  buildUnpartitionedAssetConditionEvaluationNode,
} from '../../../graphql/builders';
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
      operatorType: 'and',
      // plain boolean operators are not history-dependent, so their children are real inputs; null
      // the sinceMetadata the builder would otherwise fill so the rows aren't suppressed.
      sinceMetadata: null,
    }),
    buildAutomationConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'b',
      userLabel: 'child condition',
      expandedLabel: ['(a OR b)', 'NOT', '(c OR d)'],
      numTrue: 0,
      isPartitioned: false,
      operatorType: 'or',
      sinceMetadata: null,
    }),
    buildAutomationConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'c',
      userLabel: null,
      expandedLabel: ['(e OR f)', 'NOT', '(g OR h)'],
      numTrue: 1,
      isPartitioned: false,
      operatorType: 'identity',
      sinceMetadata: null,
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

// A plain (non-temporal) leaf operand: no children of its own, so it is suppressed when it sits
// under a history-dependent node (its numTrue feeds the derived memory rows), but shown normally
// under boolean operators.
const buildLeafOperand = (uniqueId: string, name: string, numTrue: number) =>
  buildAutomationConditionEvaluationNode({
    uniqueId,
    userLabel: name,
    expandedLabel: [`(${name})`],
    isPartitioned: false,
    numTrue,
    numCandidates: null,
    childUniqueIds: [],
    operatorType: 'identity',
    sinceMetadata: null,
  });

/**
 * `since` latch. The node is TRUE because its trigger fired on a past tick — not because of the
 * current values of `newly_updated` / `newly_requested`. Its operands render as rows annotated with
 * explicit set/reset verbs: `newly_updated` "set at <timestamp>" (clickable → that evaluation) and
 * `newly_requested` "reset: never" — so the true latch over a never-fired reset reads correctly.
 */
export const SinceLatch = () => {
  const nodes = [
    buildAutomationConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'a',
      userLabel: null,
      expandedLabel: ['(newly_updated)', 'SINCE', '(newly_requested)'],
      isPartitioned: false,
      numTrue: 1,
      childUniqueIds: ['trigger', 'reset'],
      operatorType: 'identity',
      sinceMetadata: buildSinceConditionMetadata({
        triggerEvaluationId: '3',
        triggerTimestamp: 1719763200, // trigger last fired
        resetEvaluationId: null,
        resetTimestamp: null, // never reset
      }),
    }),
    buildLeafOperand('trigger', 'newly_updated', 0),
    buildLeafOperand('reset', 'newly_requested', 0),
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

/**
 * `newly_missing` edge (= `missing().newly_true()`) whose asset is STILL missing: the operand is
 * true now and was already true on the previous tick, so the edge is FALSE. Previously this read as
 * a confusing "gray parent / green child"; now the memory rows spell out now vs. last tick.
 */
export const NewlyMissingStillMissing = () => {
  const nodes = [
    buildAutomationConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'a',
      userLabel: 'newly_missing',
      expandedLabel: ['NEWLY_TRUE', '(missing)'],
      isPartitioned: false,
      numTrue: 0, // edge did not fire this tick ⇒ derived: was already missing on the previous tick
      numCandidates: null,
      childUniqueIds: ['missing'],
      operatorType: 'identity',
      sinceMetadata: null,
    }),
    buildLeafOperand('missing', 'missing', 1), // missing now
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

/**
 * `newly_missing` edge that fired this tick: the operand is true now but was NOT true on the
 * previous tick, so the edge is TRUE.
 */
export const NewlyMissingJustFired = () => {
  const nodes = [
    buildAutomationConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'a',
      userLabel: 'newly_missing',
      expandedLabel: ['NEWLY_TRUE', '(missing)'],
      isPartitioned: false,
      numTrue: 1, // edge fired ⇒ derived: was not missing on the previous tick
      numCandidates: null,
      childUniqueIds: ['missing'],
      operatorType: 'identity',
      sinceMetadata: null,
    }),
    buildLeafOperand('missing', 'missing', 1), // missing now
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

/**
 * Partitioned `newly_true` edge: the memory rows show the per-tick partition count ("5 True" /
 * "3 True") in the Result column rather than a single icon, so a partial/mixed result is visible
 * and reconciles with the parent's "2 True" by subtraction (5 missing now − 3 already missing ⇒
 * 2 newly). The second row is tagged "already true" because the derived count is
 * |true now ∩ true last tick|, not the operand's full previous-tick value.
 */
export const NewlyTruePartitioned = () => {
  const nodes = [
    buildAutomationConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'a',
      userLabel: 'newly_missing',
      expandedLabel: ['NEWLY_TRUE', '(missing)'],
      isPartitioned: true,
      numTrue: 2, // 2 partitions newly became missing this tick
      numCandidates: null, // evaluated against all partitions, so the derived count is exact
      childUniqueIds: ['missing'],
      operatorType: 'identity',
      sinceMetadata: null,
    }),
    buildLeafOperand('missing', 'missing', 5), // 5 partitions missing now
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

/**
 * Degraded state: partitioned edge evaluated against a NARROWED candidate set (numCandidates set),
 * the common shape for edges nested as a non-first operand of an AND (e.g. inside `eager`). The
 * `numTrue(operand) − numTrue(edge)` subtraction would overcount here, so the "already true" row
 * pins a dash rather than a count.
 */
export const NewlyTrueNarrowedCandidates = () => {
  const nodes = [
    buildAutomationConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'a',
      userLabel: 'newly_missing',
      expandedLabel: ['NEWLY_TRUE', '(missing)'],
      isPartitioned: true,
      numTrue: 2,
      numCandidates: 3, // a parent narrowed the candidates before this edge evaluated
      childUniqueIds: ['missing'],
      operatorType: 'identity',
      sinceMetadata: null,
    }),
    buildLeafOperand('missing', 'missing', 5),
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

/**
 * Degraded state: unpartitioned edge whose operand is FALSE now. The previous-tick value is
 * unrecoverable from the record (and causally irrelevant — the edge is false regardless), so the
 * "last tick" row pins a dash rather than a status.
 */
export const NewlyMissingNotMissingNow = () => {
  const nodes = [
    buildAutomationConditionEvaluationNode({
      startTimestamp: 0,
      endTimestamp: 10,
      uniqueId: 'a',
      userLabel: 'newly_missing',
      expandedLabel: ['NEWLY_TRUE', '(missing)'],
      isPartitioned: false,
      numTrue: 0,
      numCandidates: null,
      childUniqueIds: ['missing'],
      operatorType: 'identity',
      sinceMetadata: null,
    }),
    buildLeafOperand('missing', 'missing', 0), // not missing now
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
