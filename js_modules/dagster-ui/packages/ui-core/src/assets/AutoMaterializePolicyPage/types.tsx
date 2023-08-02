import {AutoMaterializeEvaluationRecordItemFragment} from './types/GetEvaluationsQuery.types';

export type NoConditionsMetEvaluation = {
  __typename: 'no_conditions_met';
  evaluationId: number;
  amount: number;
  endTimestamp: number | 'now';
  startTimestamp: number;
  numSkipped?: undefined;
  numRequested?: undefined;
  numDiscarded?: undefined;
  numRequests?: undefined;
  conditions?: undefined;
};

export type EvaluationOrEmpty =
  | AutoMaterializeEvaluationRecordItemFragment
  | NoConditionsMetEvaluation;
