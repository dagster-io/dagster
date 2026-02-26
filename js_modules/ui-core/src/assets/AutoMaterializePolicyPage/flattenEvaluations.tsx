import {ConditionType} from './PolicyEvaluationCondition';
import {
  NewEvaluationNodeFragment,
  PartitionedAssetConditionEvaluationNodeFragment,
  SpecificPartitionAssetConditionEvaluationNodeFragment,
  UnpartitionedAssetConditionEvaluationNodeFragment,
} from './types/GetEvaluationsQuery.types';
import {displayNameForAssetKey, tokenForAssetKey} from '../../asset-graph/Utils';
import {AssetCheckhandle, AssetConditionEvaluationStatus, EntityKey} from '../../graphql/types';

export type FlattenedConditionEvaluation<T> = {
  evaluation: T;
  id: number;
  parentId: number | null;
  depth: number;
  type: ConditionType;
  entityKey: EntityKey | null;
};

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

export const flattenEvaluations = ({evaluationNodes, rootUniqueId, expandedRecords}: Config) => {
  const all: FlattenedEvaluation[] = [];
  let counter = 0;

  const recordsById = Object.fromEntries(evaluationNodes.map((node) => [node.uniqueId, node]));

  const append = (evaluation: Evaluation, parentId: number | null, depth: number) => {
    const id = counter + 1;

    const type =
      evaluation.childUniqueIds && evaluation.childUniqueIds.length > 0 ? 'group' : 'leaf';

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

    if (evaluation.childUniqueIds && expandedRecords.has(evaluation.uniqueId)) {
      const parentCounter = counter;
      evaluation.childUniqueIds.forEach((childId) => {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        const child = recordsById[childId]!;
        append(child, parentCounter, depth + 1);
      });
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

export const assetKeyForEntityKey = (entityKey: EntityKey) => {
  if (entityKey.__typename === 'AssetKey') {
    return entityKey;
  }
  return entityKey.assetKey;
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
  const assetCheck = entityKey as AssetCheckhandle;
  return `${assetCheck.name}::${tokenForAssetKey(assetCheck.assetKey)}`;
};

export const displayNameForEntityKey = (entityKey: EntityKey) => {
  if (entityKey.__typename === 'AssetKey') {
    return displayNameForAssetKey(entityKey);
  }
  const assetCheck = entityKey as AssetCheckhandle;
  return `${assetCheck.name} (${displayNameForAssetKey(assetCheck.assetKey)})`;
};

export const buildEntityKey = (
  assetKeyPath: string[],
  assetCheckName: string | undefined,
): EntityKey => {
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
