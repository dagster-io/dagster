import {PartitionKeyRange} from '../../graphql/types';
import {AssetKey} from '../types';

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

/* todo dish: Replace these types with GraphQL generated types */

export enum AssetConditionEvaluationStatus {
  TRUE = 'TRUE',
  FALSE = 'FALSE',
  SKIPPED = 'SKIPPED',
}

export type AssetConditionEvaluation =
  | UnpartitionedAssetConditionEvaluation
  | PartitionedAssetConditionEvaluation;

export type AssetSubset = {
  assetKey: AssetKey;
  subsetValue: AssetSubsetValue;
};

export type AssetSubsetValue = {
  boolValue: boolean | null;
  partitionKeys: string[] | null;
  partitionKeyRanges: PartitionKeyRange[] | null;
  isPartitioned: boolean;
};

export type UnpartitionedAssetConditionEvaluation = {
  __typename: 'UnpartitionedAssetConditionEvaluation';
  description: string;
  startTimestamp: number;
  endTimestamp: number;
  // metadataEntries: [MetadataEntry!]!
  status: AssetConditionEvaluationStatus;
  childEvaluations: UnpartitionedAssetConditionEvaluation[] | null;
};

export type PartitionedAssetConditionEvaluation = {
  __typename: 'PartitionedAssetConditionEvaluation';
  description: string;
  startTimestamp: number;
  endTimestamp: number;
  numTrue: number;
  numFalse: number;
  numSkipped: number;
  childEvaluations: PartitionedAssetConditionEvaluation[] | null;

  // We may want to query for these separately
  trueSubset: AssetSubset;
  falseSubset: AssetSubset;
  candidateSubset: AssetSubset | null;
};
