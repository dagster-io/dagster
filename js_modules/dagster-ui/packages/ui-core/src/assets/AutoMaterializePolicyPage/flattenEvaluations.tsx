import {ConditionType} from './PolicyEvaluationCondition';
import {
  NewEvaluationNodeFragment,
  PartitionedAssetConditionEvaluationNodeFragment,
  SpecificPartitionAssetConditionEvaluationNodeFragment,
  UnpartitionedAssetConditionEvaluationNodeFragment,
} from './types/GetEvaluationsQuery.types';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {AssetKey} from '../types';

export type FlattenedConditionEvaluation<T> = {
  evaluation: T;
  id: number;
  parentId: number | null;
  depth: number;
  type: ConditionType;
  assetKey: AssetKey | null;
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

    const nodeAssetKey =
      evaluation.__typename === 'AutomationConditionEvaluationNode' &&
      evaluation.entityKey.__typename === 'AssetKey'
        ? evaluation.entityKey
        : null;
    const childRecords = evaluation.childUniqueIds.map((childId) => {
      return recordsById[childId];
    });
    const childAssetKeys = childRecords.map((record) => {
      return record?.__typename === 'AutomationConditionEvaluationNode' &&
        record.entityKey.__typename === 'AssetKey'
        ? record.entityKey
        : null;
    });
    const childAssetKey = childAssetKeys.length ? childAssetKeys[0] : null;
    all.push({
      evaluation,
      id,
      parentId: parentId === null ? counter : parentId,
      depth,
      type,
      assetKey:
        childAssetKey &&
        childAssetKeys.every(
          (assetKey) => assetKey && tokenForAssetKey(assetKey) === tokenForAssetKey(childAssetKey),
        )
          ? childAssetKey
          : nodeAssetKey,
    } as FlattenedEvaluation);
    counter = id;

    if (evaluation.childUniqueIds && expandedRecords.has(evaluation.uniqueId)) {
      const parentCounter = counter;
      evaluation.childUniqueIds.forEach((childId) => {
        const child = recordsById[childId]!;
        append(child, parentCounter, depth + 1);
      });
    }
  };

  append(recordsById[rootUniqueId]!, null, 0);

  return all;
};
