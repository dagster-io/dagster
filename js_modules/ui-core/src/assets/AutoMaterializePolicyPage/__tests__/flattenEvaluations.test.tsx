import {
  buildAutomationConditionEvaluationNode,
  buildSinceConditionMetadata,
} from '../../../graphql/builders';
import {
  assetKeyForEntityKey,
  buildEntityKey,
  displayNameForEntityKey,
  entityKeyMatches,
  expandableUniqueIds,
  memoryRowSpecsForEvaluation,
  tokenForEntityKey,
} from '../flattenEvaluations';
import {EntityKeyFragment} from '../types/GetEvaluationsQuery.types';

const assetKey: EntityKeyFragment = {__typename: 'AssetKey', path: ['foo', 'bar']};
const checkKey: EntityKeyFragment = {
  __typename: 'AssetCheckhandle',
  name: 'my_check',
  assetKey: {__typename: 'AssetKey', path: ['foo', 'bar']},
};
const jobKey: EntityKeyFragment = {__typename: 'AssetJobKey', jobName: 'my_job'};

describe('tokenForEntityKey', () => {
  it('tokenizes each entity key type distinctly', () => {
    expect(tokenForEntityKey(assetKey)).toBe('foo/bar');
    expect(tokenForEntityKey(checkKey)).toBe('my_check::foo/bar');
    expect(tokenForEntityKey(jobKey)).toBe('job:my_job');
  });
});

describe('displayNameForEntityKey', () => {
  it('displays the bare job name for job keys', () => {
    expect(displayNameForEntityKey(jobKey)).toBe('my_job');
  });

  it('displays asset and check names', () => {
    expect(displayNameForEntityKey(assetKey)).toBe('foo / bar');
    expect(displayNameForEntityKey(checkKey)).toBe('my_check (foo / bar)');
  });
});

describe('assetKeyForEntityKey', () => {
  it('returns the asset key for asset and check keys', () => {
    expect(assetKeyForEntityKey(assetKey)).toEqual(assetKey);
    expect(assetKeyForEntityKey(checkKey)).toEqual({__typename: 'AssetKey', path: ['foo', 'bar']});
  });

  it('returns null for job keys, which have no asset key', () => {
    expect(assetKeyForEntityKey(jobKey)).toBeNull();
  });
});

describe('entityKeyMatches', () => {
  it('matches job keys by job name', () => {
    expect(entityKeyMatches(jobKey, {__typename: 'AssetJobKey', jobName: 'my_job'})).toBe(true);
    expect(entityKeyMatches(jobKey, {__typename: 'AssetJobKey', jobName: 'other_job'})).toBe(false);
  });

  it('does not match job keys against other entity key types', () => {
    expect(entityKeyMatches(jobKey, assetKey)).toBe(false);
    expect(entityKeyMatches(jobKey, checkKey)).toBe(false);
  });
});

describe('buildEntityKey', () => {
  it('builds an asset key by default', () => {
    expect(buildEntityKey(['foo', 'bar'], undefined)).toEqual(assetKey);
  });

  it('builds a check handle when a check name is provided', () => {
    expect(buildEntityKey(['foo', 'bar'], 'my_check')).toEqual(checkKey);
  });

  it('builds a job key when a job name is provided', () => {
    expect(buildEntityKey([], undefined, 'my_job')).toEqual(jobKey);
  });

  it('prefers the job name over a check name when both are provided', () => {
    expect(buildEntityKey(['foo', 'bar'], 'my_check', 'my_job')).toEqual(jobKey);
  });
});

const sinceLatchNodes = () => {
  const since = buildAutomationConditionEvaluationNode({
    uniqueId: 'since',
    expandedLabel: ['(newly_updated)', 'SINCE', '(newly_requested)'],
    childUniqueIds: ['trigger', 'reset'],
    operatorType: 'identity',
    sinceMetadata: buildSinceConditionMetadata({
      triggerTimestamp: 1719777600,
      triggerEvaluationId: '42',
      resetTimestamp: null,
      resetEvaluationId: null,
    }),
  });
  const trigger = buildAutomationConditionEvaluationNode({
    uniqueId: 'trigger',
    expandedLabel: ['NEWLY_TRUE', '(updated)'],
    childUniqueIds: ['trigger_operand'],
    operatorType: 'identity',
    sinceMetadata: null,
  });
  const triggerOperand = buildAutomationConditionEvaluationNode({
    uniqueId: 'trigger_operand',
    expandedLabel: ['updated'],
    childUniqueIds: [],
    operatorType: 'identity',
    sinceMetadata: null,
  });
  const reset = buildAutomationConditionEvaluationNode({
    uniqueId: 'reset',
    expandedLabel: ['newly_requested'],
    childUniqueIds: [],
    operatorType: 'identity',
    sinceMetadata: null,
  });
  return [since, trigger, triggerOperand, reset];
};

const recordsById = (nodes: ReturnType<typeof sinceLatchNodes>) =>
  Object.fromEntries(nodes.map((node) => [node.uniqueId, node]));

describe('memoryRowSpecsForEvaluation', () => {
  it('emits set/reset memory rows for a since latch', () => {
    const nodes = sinceLatchNodes();
    const [since] = nodes;
    const rows = since ? memoryRowSpecsForEvaluation(since, recordsById(nodes)) : null;
    expect(rows?.map((row) => row.tag.kind)).toEqual(['set', 'reset']);
  });

  it('requires the three-segment SINCE label shape, not just populated sinceMetadata', () => {
    // A non-since node whose sinceMetadata a loose backend (or the mock builder) populated
    // anyway must not be treated as a latch.
    const andNode = buildAutomationConditionEvaluationNode({
      uniqueId: 'and',
      expandedLabel: ['(missing)', 'AND', '(in_progress)'],
      childUniqueIds: ['trigger', 'reset'],
      operatorType: 'and',
      sinceMetadata: buildSinceConditionMetadata({
        triggerTimestamp: 1719777600,
        triggerEvaluationId: '42',
        resetTimestamp: null,
        resetEvaluationId: null,
      }),
    });
    const nodes = sinceLatchNodes();
    expect(memoryRowSpecsForEvaluation(andNode, recordsById(nodes))).toBeNull();
  });
});

describe('expandableUniqueIds', () => {
  it('excludes operand subtrees hidden behind memory rows', () => {
    const nodes = sinceLatchNodes();
    // `trigger` has a child of its own, but it never renders beneath the latch's memory
    // rows, so it must not count toward the expand-all state.
    const expandable = expandableUniqueIds({evaluationNodes: nodes, rootUniqueId: 'since'});
    expect(expandable).toEqual(new Set(['since']));
  });

  it('recurses through ordinary group nodes', () => {
    const nodes = sinceLatchNodes();
    const and = buildAutomationConditionEvaluationNode({
      uniqueId: 'and',
      expandedLabel: ['(newly_updated)', 'AND', '(newly_requested)'],
      childUniqueIds: ['trigger', 'reset'],
      operatorType: 'and',
      sinceMetadata: null,
    });
    // the AND recurses into its children; `trigger` is itself expandable (into memory rows)
    // but its own operand subtree still does not count
    const expandable = expandableUniqueIds({
      evaluationNodes: [...nodes, and],
      rootUniqueId: 'and',
    });
    expect(expandable).toEqual(new Set(['and', 'trigger']));
  });
});
