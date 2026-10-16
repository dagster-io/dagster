import {ConditionType} from './PolicyEvaluationCondition';
import {
  EntityKeyFragment_AssetCheckhandle as AssetCheckhandle,
  EntityKeyFragment as EntityKey,
  NewEvaluationNodeFragment,
  PartitionedAssetConditionEvaluationNodeFragment,
  SpecificPartitionAssetConditionEvaluationNodeFragment,
  UnpartitionedAssetConditionEvaluationNodeFragment,
} from './types/GetEvaluationsQuery.types';
import {displayNameForAssetKey, tokenForAssetKey} from '../../asset-graph/Utils';
import {AssetConditionEvaluationStatus} from '../../graphql/types';

export type FlattenedConditionEvaluation<T> = {
  evaluation: T;
  id: number;
  parentId: number | null;
  depth: number;
  type: ConditionType;
  entityKey: EntityKey | null;
};

/**
 * A synthetic row rendered beneath a history-dependent node, showing one of the remembered values
 * that actually determines the node's truth (rather than an operand's current value). Rendered as
 * `[status icon] [temporal tag] [condition]`.
 */
export type EvaluationMemoryRow = {
  rowType: 'memory';
  id: number;
  parentId: number;
  depth: number;
  conditionLabel: string;
  tag:
    | {kind: 'currentTick'}
    | {kind: 'lastTick'}
    | {kind: 'set'; timestamp: number | null; evaluationId: string | null}
    | {kind: 'reset'; timestamp: number | null; evaluationId: string | null};
  result:
    | {isPartitioned: false; value: boolean | null}
    | {isPartitioned: true; numTrue: number | null};
  entityKey: EntityKey | null;
};

type EvaluationMemoryRowSpec = Pick<EvaluationMemoryRow, 'conditionLabel' | 'tag' | 'result'>;

export type Evaluation =
  | PartitionedAssetConditionEvaluationNodeFragment
  | UnpartitionedAssetConditionEvaluationNodeFragment
  | SpecificPartitionAssetConditionEvaluationNodeFragment
  | NewEvaluationNodeFragment;

type FlattenedEvaluation =
  | FlattenedConditionEvaluation<PartitionedAssetConditionEvaluationNodeFragment>
  | FlattenedConditionEvaluation<UnpartitionedAssetConditionEvaluationNodeFragment>
  | FlattenedConditionEvaluation<SpecificPartitionAssetConditionEvaluationNodeFragment>
  | FlattenedConditionEvaluation<NewEvaluationNodeFragment>;

type Config = {
  evaluationNodes: Evaluation[];
  rootUniqueId: string;
  expandedRecords: Set<string>;
};

const isNewEvaluationNode = (evaluation: Evaluation): evaluation is NewEvaluationNodeFragment =>
  evaluation.__typename === 'AutomationConditionEvaluationNode';

/**
 * A `newly_true` node (also surfaced as `newly_missing`, and nested inside `eager`) is an *edge*:
 * true only where its operand is true now but was not true on the previous tick. Its name segment
 * is stable regardless of any user-provided label, and it always has exactly one operand.
 */
export const isNewlyTrueNode = (evaluation: Evaluation): boolean =>
  isNewEvaluationNode(evaluation) &&
  evaluation.expandedLabel[0] === 'NEWLY_TRUE' &&
  evaluation.childUniqueIds.length === 1;

export type NewlyTrueMemory =
  | {
      isPartitioned: false;
      trueNow: boolean;
      // null when the operand is not true now: the edge is false regardless of history, so the
      // previous-tick value is irrelevant (and not recoverable from the record).
      trueOnPreviousTick: boolean | null;
    }
  | {
      isPartitioned: true;
      trueNowCount: number;
      newlyTrueCount: number;
      // of the partitions true now, how many were already true on the previous tick. null when
      // the node was evaluated against a narrowed candidate set, where the subtraction below
      // would overcount.
      previouslyTrueCount: number | null;
    };

/**
 * Both inputs to a `newly_true` edge (operand true now AND NOT true on the previous tick) are
 * recoverable from the evaluation record itself, so the previous-tick value never needs to be
 * persisted or fetched:
 *
 * - The operand's current value is its own node in this record (the operator always evaluates its
 *   operand against all partitions, so the operand's `numTrue` is not narrowed by candidates).
 * - Unpartitioned: when the operand is true now, the previous-tick value is the complement of
 *   this node's own value.
 * - Partitioned: of the partitions true now, `numTrue(operand) - numTrue(node)` were already true
 *   on the previous tick. Partitions true previously but no longer true never affect the edge.
 *   This is exact only when the node itself was evaluated against all partitions
 *   (`numCandidates === null`).
 */
export const deriveNewlyTrueMemory = (
  evaluation: Evaluation,
  recordsById: {[uniqueId: string]: Evaluation},
): NewlyTrueMemory | null => {
  if (!isNewEvaluationNode(evaluation) || !isNewlyTrueNode(evaluation)) {
    return null;
  }
  if (statusForEvaluation(evaluation) === AssetConditionEvaluationStatus.SKIPPED) {
    return null;
  }
  const operandId = evaluation.childUniqueIds[0];
  const operand = operandId ? recordsById[operandId] : null;
  if (!operand || !isNewEvaluationNode(operand)) {
    return null;
  }

  const newlyTrueCount = evaluation.numTrue ?? 0;
  const trueNowCount = operand.numTrue ?? 0;
  if (evaluation.isPartitioned) {
    return {
      isPartitioned: true,
      trueNowCount,
      newlyTrueCount,
      previouslyTrueCount:
        evaluation.numCandidates === null ? Math.max(trueNowCount - newlyTrueCount, 0) : null,
    };
  }
  const trueNow = trueNowCount > 0;
  return {
    isPartitioned: false,
    trueNow,
    trueOnPreviousTick: trueNow ? newlyTrueCount === 0 : null,
  };
};

const labelForOperand = (operand: Evaluation | undefined, fallbackSegment: string | undefined) => {
  if (operand && isNewEvaluationNode(operand)) {
    return operand.userLabel || operand.expandedLabel.join(' ');
  }
  return fallbackSegment?.startsWith('(') && fallbackSegment.endsWith(')')
    ? fallbackSegment.slice(1, -1)
    : (fallbackSegment ?? '');
};

/**
 * The memory rows for a history-dependent node, or null for ordinary nodes (which render their
 * real child nodes instead):
 *
 * - `since` latch: the ticks its trigger ("set") and reset last fired, from sinceMetadata.
 * - `newly_true` edge: its operand's value on the current vs. the previous tick, derived from the
 *   record itself (deriveNewlyTrueMemory).
 *
 * Operands deliberately do not render as expandable sub-trees beneath these nodes: a sub-tree
 * would show *current* values, not the values at the remembered tick, re-creating the misleading
 * green-parent/gray-child juxtaposition one level down. To inspect why a latch fired, the set /
 * reset tags navigate to that tick's evaluation.
 */
export const memoryRowSpecsForEvaluation = (
  evaluation: Evaluation,
  recordsById: {[uniqueId: string]: Evaluation},
): EvaluationMemoryRowSpec[] | null => {
  if (!isNewEvaluationNode(evaluation)) {
    return null;
  }

  // Unlike edges, a skipped latch still renders memory rows: its set/reset timestamps are
  // persisted history, accurate regardless of the current tick's candidate set.
  const {sinceMetadata, expandedLabel} = evaluation;
  if (
    sinceMetadata &&
    evaluation.childUniqueIds.length === 2 &&
    expandedLabel.length === 3 &&
    expandedLabel[1] === 'SINCE'
  ) {
    const [triggerId, resetId] = evaluation.childUniqueIds;
    return [
      {
        conditionLabel: labelForOperand(
          triggerId ? recordsById[triggerId] : undefined,
          evaluation.expandedLabel[0],
        ),
        tag: {
          kind: 'set',
          timestamp: sinceMetadata.triggerTimestamp,
          evaluationId: sinceMetadata.triggerEvaluationId,
        },
        result: {isPartitioned: false, value: sinceMetadata.triggerTimestamp !== null},
      },
      {
        conditionLabel: labelForOperand(
          resetId ? recordsById[resetId] : undefined,
          evaluation.expandedLabel[2],
        ),
        tag: {
          kind: 'reset',
          timestamp: sinceMetadata.resetTimestamp,
          evaluationId: sinceMetadata.resetEvaluationId,
        },
        result: {isPartitioned: false, value: sinceMetadata.resetTimestamp !== null},
      },
    ];
  }

  const memory = deriveNewlyTrueMemory(evaluation, recordsById);
  if (memory) {
    const operandId = evaluation.childUniqueIds[0];
    const conditionLabel = labelForOperand(
      operandId ? recordsById[operandId] : undefined,
      evaluation.expandedLabel[1],
    );
    return [
      {
        conditionLabel,
        tag: {kind: 'currentTick'},
        result: memory.isPartitioned
          ? {isPartitioned: true, numTrue: memory.trueNowCount}
          : {isPartitioned: false, value: memory.trueNow},
      },
      {
        conditionLabel,
        tag: {kind: 'lastTick'},
        result: memory.isPartitioned
          ? {isPartitioned: true, numTrue: memory.previouslyTrueCount}
          : {isPartitioned: false, value: memory.trueOnPreviousTick},
      },
    ];
  }

  return null;
};

export const flattenEvaluations = ({evaluationNodes, rootUniqueId, expandedRecords}: Config) => {
  const all: (FlattenedEvaluation | EvaluationMemoryRow)[] = [];
  let counter = 0;

  const recordsById = Object.fromEntries(evaluationNodes.map((node) => [node.uniqueId, node]));

  const append = (evaluation: Evaluation, parentId: number | null, depth: number) => {
    const id = counter + 1;

    // A history-dependent node renders its memory as the rows beneath it — the values that
    // actually determine its truth — instead of its operands' current values, which can
    // contradict the parent (e.g. a green `missing` under a gray `newly_missing`).
    const memoryRowSpecs = memoryRowSpecsForEvaluation(evaluation, recordsById);
    const childIdsToRender = memoryRowSpecs ? [] : (evaluation.childUniqueIds ?? []);

    const type = (memoryRowSpecs?.length ?? childIdsToRender.length) > 0 ? 'group' : 'leaf';

    const childRecords = evaluation.childUniqueIds.map((childId) => {
      return recordsById[childId];
    });
    const entityKey =
      evaluation.__typename === 'AutomationConditionEvaluationNode'
        ? entityKeyForEvaluation(
            evaluation as NewEvaluationNodeFragment,
            childRecords.filter(
              (child) => child && child.__typename === 'AutomationConditionEvaluationNode',
            ) as NewEvaluationNodeFragment[],
          )
        : null;
    all.push({
      evaluation,
      id,
      parentId: parentId === null ? counter : parentId,
      depth,
      type,
      entityKey,
    } as FlattenedEvaluation);
    counter = id;

    if (expandedRecords.has(evaluation.uniqueId)) {
      const parentCounter = counter;
      if (memoryRowSpecs) {
        memoryRowSpecs.forEach((spec) => {
          counter += 1;
          all.push({
            rowType: 'memory',
            id: counter,
            parentId: parentCounter,
            depth: depth + 1,
            entityKey,
            ...spec,
          });
        });
      } else {
        childIdsToRender.forEach((childId) => {
          const child = recordsById[childId];
          if (child) {
            append(child, parentCounter, depth + 1);
          }
        });
      }
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  append(recordsById[rootUniqueId]!, null, 0);

  return all;
};

export const entityKeyMatches = (
  a: EntityKey | null | undefined,
  b: EntityKey | null | undefined,
) => {
  if (!a && !b) {
    return true;
  }
  if (!a || !b) {
    return false;
  }
  if (a.__typename !== b.__typename) {
    return false;
  }
  if (a.__typename === 'AssetKey') {
    return b.__typename === 'AssetKey' && tokenForAssetKey(a) === tokenForAssetKey(b);
  }
  if (a.__typename === 'AssetJobKey') {
    return b.__typename === 'AssetJobKey' && a.jobName === b.jobName;
  }
  return (
    b.__typename === 'AssetCheckhandle' &&
    a.name === b.name &&
    tokenForAssetKey(a.assetKey) === tokenForAssetKey(b.assetKey)
  );
};

export const statusForEvaluation = (evaluation: Evaluation) => {
  if (evaluation.__typename !== 'AutomationConditionEvaluationNode') {
    return undefined;
  }
  const {numTrue, numCandidates} = evaluation;
  const anyCandidatePartitions = numCandidates === null || numCandidates > 0;
  return numTrue === 0 && !anyCandidatePartitions
    ? AssetConditionEvaluationStatus.SKIPPED
    : numTrue && numTrue > 0
      ? AssetConditionEvaluationStatus.TRUE
      : AssetConditionEvaluationStatus.FALSE;
};

export const assetKeyForEntityKey = (
  entityKey: EntityKey,
): {__typename: 'AssetKey'; path: string[]} | null => {
  if (entityKey.__typename === 'AssetKey') {
    return entityKey;
  }
  if (entityKey.__typename === 'AssetJobKey') {
    return null;
  }
  return entityKey.assetKey;
};

export const assetCheckNameForEntityKey = (entityKey: EntityKey): string | undefined => {
  return entityKey.__typename === 'AssetCheckhandle' ? entityKey.name : undefined;
};

export const jobNameForEntityKey = (entityKey: EntityKey): string | undefined => {
  return entityKey.__typename === 'AssetJobKey' ? entityKey.jobName : undefined;
};

export const entityKeyForEvaluation = (
  node: NewEvaluationNodeFragment,
  childNodes: NewEvaluationNodeFragment[],
): EntityKey | null => {
  const childEntityKeys = childNodes.map((childNode) => childNode.entityKey);
  const childEntityKey = childEntityKeys.length ? childEntityKeys[0] : null;
  return childEntityKey &&
    childEntityKeys.every((entityKey) => entityKey && entityKeyMatches(entityKey, childEntityKey))
    ? childEntityKey
    : node.entityKey;
};

export const tokenForEntityKey = (entityKey: EntityKey) => {
  if (entityKey.__typename === 'AssetKey') {
    return tokenForAssetKey(entityKey);
  }
  if (entityKey.__typename === 'AssetJobKey') {
    return `job:${entityKey.jobName}`;
  }
  const assetCheck = entityKey as AssetCheckhandle;
  return `${assetCheck.name}::${tokenForAssetKey(assetCheck.assetKey)}`;
};

export const displayNameForEntityKey = (entityKey: EntityKey) => {
  if (entityKey.__typename === 'AssetKey') {
    return displayNameForAssetKey(entityKey);
  }
  if (entityKey.__typename === 'AssetJobKey') {
    return entityKey.jobName;
  }
  const assetCheck = entityKey as AssetCheckhandle;
  return `${assetCheck.name} (${displayNameForAssetKey(assetCheck.assetKey)})`;
};

export const buildEntityKey = (
  assetKeyPath: string[],
  assetCheckName: string | undefined,
  jobName?: string,
): EntityKey => {
  if (jobName) {
    return {
      __typename: 'AssetJobKey',
      jobName,
    };
  }
  return assetCheckName
    ? {
        __typename: 'AssetCheckhandle',
        name: assetCheckName,
        assetKey: {
          __typename: 'AssetKey',
          path: assetKeyPath,
        },
      }
    : {
        __typename: 'AssetKey',
        path: assetKeyPath,
      };
};

/**
 * Collect the unique IDs of every node in the tree that has children, i.e. every node that can be
 * expanded or collapsed. Used to drive the "expand all"/"collapse all" control.
 */
export const expandableUniqueIds = ({
  evaluationNodes,
  rootUniqueId,
}: {
  evaluationNodes: Evaluation[];
  rootUniqueId: string;
}) => {
  const expandable: Set<string> = new Set();
  const recordsById = Object.fromEntries(evaluationNodes.map((node) => [node.uniqueId, node]));

  const visit = (evaluation: Evaluation) => {
    if (!evaluation.childUniqueIds?.length || expandable.has(evaluation.uniqueId)) {
      return;
    }
    expandable.add(evaluation.uniqueId);
    // A history-dependent node expands into memory rows, not its operand subtree, so its
    // descendants never render and are not expandable.
    if (memoryRowSpecsForEvaluation(evaluation, recordsById)) {
      return;
    }
    evaluation.childUniqueIds.forEach((childId) => {
      const child = recordsById[childId];
      if (child) {
        visit(child);
      }
    });
  };

  const rootEvaluation = recordsById[rootUniqueId];
  if (rootEvaluation) {
    visit(rootEvaluation);
  }

  return expandable;
};

export const defaultExpanded = ({
  evaluationNodes,
  rootUniqueId,
}: {
  evaluationNodes: Evaluation[];
  rootUniqueId: string;
}) => {
  const expanded: Set<string> = new Set([]);
  const recordsById = Object.fromEntries(evaluationNodes.map((node) => [node.uniqueId, node]));
  const expand = (evaluation: Evaluation, rootEntityKey: EntityKey) => {
    if (evaluation.__typename !== 'AutomationConditionEvaluationNode') {
      // only default expand non-legacy nodes
      return;
    }

    // get the status of the evaluation
    const status = statusForEvaluation(evaluation);
    if (status === AssetConditionEvaluationStatus.SKIPPED) {
      return;
    }

    const children = evaluation.childUniqueIds
      .map((childId) => {
        return recordsById[childId];
      })
      .filter((child) => {
        return child && child.__typename === 'AutomationConditionEvaluationNode';
      }) as NewEvaluationNodeFragment[];
    const entityKey = entityKeyForEvaluation(evaluation, children);
    if (entityKey && !entityKeyMatches(entityKey, rootEntityKey)) {
      return;
    }
    expanded.add(evaluation.uniqueId);

    switch (evaluation.operatorType) {
      case 'and':
        if (status === AssetConditionEvaluationStatus.TRUE) {
          children.forEach((child) => {
            expand(child, rootEntityKey);
          });
        } else if (status === AssetConditionEvaluationStatus.FALSE) {
          // expand the first False child
          const firstFalse = children.find((child) => {
            return statusForEvaluation(child) === AssetConditionEvaluationStatus.FALSE;
          });
          if (firstFalse) {
            expand(firstFalse, rootEntityKey);
          }
        }
        break;
      case 'or':
        if (status === AssetConditionEvaluationStatus.TRUE) {
          // expand the first True child
          const firstTrue = children.find((child) => {
            return statusForEvaluation(child) === AssetConditionEvaluationStatus.TRUE;
          });
          if (firstTrue) {
            expand(firstTrue, rootEntityKey);
          }
        } else {
          // expand all children
          children.forEach((child) => {
            expand(child, rootEntityKey);
          });
        }
        break;
      case 'not':
        children.forEach((child) => {
          expand(child, rootEntityKey);
        });
        break;
      case 'identity':
        children.forEach((child) => {
          expand(child, rootEntityKey);
        });
        break;
      default:
        throw new Error(`Unknown operator type: ${evaluation.operatorType}`);
        break;
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const rootEvaluation = recordsById[rootUniqueId]!;
  expand(rootEvaluation, rootEvaluation.entityKey);

  return expanded;
};
