import {buildAutomationConditionEvaluationNode} from '../../../graphql/builders';
import {Evaluation, deriveNewlyTrueMemory, isNewlyTrueNode} from '../flattenEvaluations';

const buildNewlyTrueNode = (
  overrides: Partial<Parameters<typeof buildAutomationConditionEvaluationNode>[0]> = {},
) =>
  buildAutomationConditionEvaluationNode({
    uniqueId: 'newly',
    expandedLabel: ['NEWLY_TRUE', '(missing)'],
    childUniqueIds: ['operand'],
    operatorType: 'identity',
    ...overrides,
  });

const buildOperandNode = (
  overrides: Partial<Parameters<typeof buildAutomationConditionEvaluationNode>[0]> = {},
) =>
  buildAutomationConditionEvaluationNode({
    uniqueId: 'operand',
    expandedLabel: ['missing'],
    childUniqueIds: [],
    operatorType: 'identity',
    ...overrides,
  });

const recordsById = (...nodes: Evaluation[]) =>
  Object.fromEntries(nodes.map((node) => [node.uniqueId, node]));

describe('isNewlyTrueNode', () => {
  it('detects a newly_true node by its stable name segment, regardless of user label', () => {
    expect(isNewlyTrueNode(buildNewlyTrueNode({userLabel: 'newly_missing'}))).toBe(true);
    expect(isNewlyTrueNode(buildNewlyTrueNode({userLabel: null}))).toBe(true);
  });

  it('does not match other nodes', () => {
    expect(
      isNewlyTrueNode(
        buildAutomationConditionEvaluationNode({
          expandedLabel: ['missing'],
          childUniqueIds: [],
        }),
      ),
    ).toBe(false);
    // multiple operands cannot be a newly_true node
    expect(
      isNewlyTrueNode(
        buildAutomationConditionEvaluationNode({
          expandedLabel: ['NEWLY_TRUE', '(x)'],
          childUniqueIds: ['a', 'b'],
        }),
      ),
    ).toBe(false);
  });
});

describe('deriveNewlyTrueMemory', () => {
  describe('unpartitioned', () => {
    it('derives "was already true" when the operand is true but the edge is false', () => {
      const node = buildNewlyTrueNode({isPartitioned: false, numTrue: 0, numCandidates: null});
      const operand = buildOperandNode({isPartitioned: false, numTrue: 1, numCandidates: null});
      expect(deriveNewlyTrueMemory(node, recordsById(node, operand))).toEqual({
        isPartitioned: false,
        trueNow: true,
        trueOnPreviousTick: true,
      });
    });

    it('derives "was false last tick" when the edge is true', () => {
      const node = buildNewlyTrueNode({isPartitioned: false, numTrue: 1, numCandidates: null});
      const operand = buildOperandNode({isPartitioned: false, numTrue: 1, numCandidates: null});
      expect(deriveNewlyTrueMemory(node, recordsById(node, operand))).toEqual({
        isPartitioned: false,
        trueNow: true,
        trueOnPreviousTick: false,
      });
    });

    it('reports the previous tick as unknowable when the operand is false now', () => {
      const node = buildNewlyTrueNode({isPartitioned: false, numTrue: 0, numCandidates: null});
      const operand = buildOperandNode({isPartitioned: false, numTrue: 0, numCandidates: null});
      expect(deriveNewlyTrueMemory(node, recordsById(node, operand))).toEqual({
        isPartitioned: false,
        trueNow: false,
        trueOnPreviousTick: null,
      });
    });
  });

  describe('partitioned', () => {
    it('derives the previously-true count when evaluated against all partitions', () => {
      const node = buildNewlyTrueNode({isPartitioned: true, numTrue: 2, numCandidates: null});
      const operand = buildOperandNode({isPartitioned: true, numTrue: 5, numCandidates: null});
      expect(deriveNewlyTrueMemory(node, recordsById(node, operand))).toEqual({
        isPartitioned: true,
        trueNowCount: 5,
        newlyTrueCount: 2,
        previouslyTrueCount: 3,
      });
    });

    it('omits the previously-true count when the candidate set is narrowed', () => {
      const node = buildNewlyTrueNode({isPartitioned: true, numTrue: 1, numCandidates: 2});
      const operand = buildOperandNode({isPartitioned: true, numTrue: 5, numCandidates: null});
      expect(deriveNewlyTrueMemory(node, recordsById(node, operand))).toEqual({
        isPartitioned: true,
        trueNowCount: 5,
        newlyTrueCount: 1,
        previouslyTrueCount: null,
      });
    });
  });

  it('returns null for skipped nodes', () => {
    const node = buildNewlyTrueNode({isPartitioned: false, numTrue: 0, numCandidates: 0});
    const operand = buildOperandNode({isPartitioned: false, numTrue: 1, numCandidates: null});
    expect(deriveNewlyTrueMemory(node, recordsById(node, operand))).toBeNull();
  });

  it('returns null when the operand node is not in the record', () => {
    const node = buildNewlyTrueNode({isPartitioned: false, numTrue: 1, numCandidates: null});
    expect(deriveNewlyTrueMemory(node, recordsById(node))).toBeNull();
  });

  it('returns null for non-newly_true nodes', () => {
    const node = buildOperandNode({isPartitioned: false, numTrue: 1, numCandidates: null});
    expect(deriveNewlyTrueMemory(node, recordsById(node))).toBeNull();
  });
});
