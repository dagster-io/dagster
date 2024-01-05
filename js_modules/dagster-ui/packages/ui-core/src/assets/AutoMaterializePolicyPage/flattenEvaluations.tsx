import {ConditionType} from './PolicyEvaluationCondition';
import {
  AssetConditionEvaluationRecordFragment,
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

type Evaluation =
  | PartitionedAssetConditionEvaluationNodeFragment
  | UnpartitionedAssetConditionEvaluationNodeFragment
  | SpecificPartitionAssetConditionEvaluationNodeFragment;

type FlattenedEvaluation =
  | FlattenedConditionEvaluation<PartitionedAssetConditionEvaluationNodeFragment>
  | FlattenedConditionEvaluation<UnpartitionedAssetConditionEvaluationNodeFragment>
  | FlattenedConditionEvaluation<SpecificPartitionAssetConditionEvaluationNodeFragment>;

export const flattenEvaluations = (
  evaluationRecord: Pick<AssetConditionEvaluationRecordFragment, 'evaluation'>,
) => {
  const all: FlattenedEvaluation[] = [];
  let counter = 0;

  const recordsById = Object.fromEntries(
    evaluationRecord.evaluation.evaluationNodes.map((node) => [node.uniqueId, node]),
  );

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

    if (evaluation.childUniqueIds) {
      const parentCounter = counter;
      evaluation.childUniqueIds.forEach((childId) => {
        const child = recordsById[childId]!;
        append(child, parentCounter, depth + 1);
      });
    }
  };

  append(recordsById[evaluationRecord.evaluation.rootUniqueId]!, null, 0);

  return all;
};
