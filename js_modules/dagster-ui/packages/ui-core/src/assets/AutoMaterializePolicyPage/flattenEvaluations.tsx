import {ConditionType} from './PolicyEvaluationCondition';
import {
  NewEvaluationNodeFragment,
  PartitionedAssetConditionEvaluationNodeFragment,
  SpecificPartitionAssetConditionEvaluationNodeFragment,
  UnpartitionedAssetConditionEvaluationNodeFragment,
} from './types/GetEvaluationsQuery.types';

export type FlattenedConditionEvaluation<T> = {
  evaluation: T;
  id: number;
  parentId: number | null;
  depth: number;
  type: ConditionType;
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

    all.push({
      evaluation,
      id,
      parentId: parentId === null ? counter : parentId,
      depth,
      type,
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
