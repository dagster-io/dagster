import {EvaluationOrEmpty} from './types';
import {AutoMaterializeEvaluationRecordItemFragment} from './types/GetEvaluationsQuery.types';

type Config = {
  evaluations: AutoMaterializeEvaluationRecordItemFragment[];
  currentEvaluationId: number | null;
  isFirstPage: boolean;
  isLastPage: boolean;
  isLoading: boolean;
};

export const getEvaluationsWithEmptyAdded = ({
  isLoading,
  currentEvaluationId,
  evaluations,
  isFirstPage,
  isLastPage,
}: Config): EvaluationOrEmpty[] => {
  if (isLoading) {
    return [];
  }

  const evalsWithSkips = [];

  let current =
    isFirstPage && currentEvaluationId !== null
      ? currentEvaluationId
      : evaluations[0]?.evaluationId || 1;

  evaluations.forEach((evaluation, i) => {
    const prevEvaluation = evaluations[i - 1];
    if (evaluation.evaluationId !== current) {
      evalsWithSkips.push({
        __typename: 'no_conditions_met' as const,
        evaluationId: current,
        amount: current - evaluation.evaluationId,
        endTimestamp: prevEvaluation?.timestamp ? prevEvaluation?.timestamp - 60 : ('now' as const),
        startTimestamp: evaluation.timestamp + 60,
      });
    }
    evalsWithSkips.push(evaluation);
    current = evaluation.evaluationId - 1;
  });

  if (isLastPage) {
    const lastEvaluation = evaluations[evaluations.length - 1];
    evalsWithSkips.push({
      __typename: 'no_conditions_met' as const,
      evaluationId: current,
      amount: current,
      endTimestamp: lastEvaluation?.timestamp ? lastEvaluation?.timestamp - 60 : ('now' as const),
      startTimestamp: 0,
    });
  }

  return evalsWithSkips;
};
