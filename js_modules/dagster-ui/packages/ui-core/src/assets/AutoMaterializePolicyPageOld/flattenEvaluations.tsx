import {ConditionType} from './PolicyEvaluationCondition';
import {AssetConditionEvaluation} from './types';

type FlattenedConditionEvaluation<T> = {
  evaluation: T;
  id: number;
  parentId: number | null;
  depth: number;
  type: ConditionType;
};

export const flattenEvaluations = <T extends AssetConditionEvaluation>(rootEvaluation: T) => {
  const all: FlattenedConditionEvaluation<T>[] = [];
  let counter = 0;

  const append = (evaluation: T, parentId: number | null, depth: number) => {
    const id = counter + 1;

    const type =
      evaluation.childEvaluations && evaluation.childEvaluations.length > 0 ? 'group' : 'leaf';

    all.push({
      evaluation,
      id,
      parentId: parentId === null ? counter : parentId,
      depth,
      type,
    } as FlattenedConditionEvaluation<T>);
    counter = id;

    if (evaluation.childEvaluations) {
      const parentCounter = counter;
      evaluation.childEvaluations.forEach((child) => {
        append(child as T, parentCounter, depth + 1);
      });
    }
  };

  append(rootEvaluation, null, 0);

  return all;
};
