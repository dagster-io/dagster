import {useMemo} from 'react';

import {GET_EVALUATIONS_QUERY} from './GetEvaluationsQuery';
import {GetEvaluationsQuery, GetEvaluationsQueryVariables} from './types/GetEvaluationsQuery.types';
import {useCursorPaginatedQuery} from '../../runs/useCursorPaginatedQuery';
import {AssetKey} from '../types';

export const PAGE_SIZE = 30;

// This function exists mostly to use the return type later
export function useEvaluationsQueryResult({assetKey}: {assetKey: AssetKey}) {
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    GetEvaluationsQuery,
    GetEvaluationsQueryVariables
  >({
    nextCursorForResult: (data) => {
      if (
        data.assetConditionEvaluationRecordsOrError?.__typename ===
        'AssetConditionEvaluationRecords'
      ) {
        return data.assetConditionEvaluationRecordsOrError.records[PAGE_SIZE - 1]?.evaluationId;
      }
      return undefined;
    },
    getResultArray: (data) => {
      if (
        data?.assetConditionEvaluationRecordsOrError?.__typename ===
        'AssetConditionEvaluationRecords'
      ) {
        return data.assetConditionEvaluationRecordsOrError.records;
      }
      return [];
    },
    variables: {
      assetKey,
    },
    query: GET_EVALUATIONS_QUERY,
    pageSize: PAGE_SIZE,
  });

  const {data} = queryResult;
  const evaluations = useMemo(() => {
    if (
      data?.assetConditionEvaluationRecordsOrError?.__typename ===
        'AssetConditionEvaluationRecords' &&
      data?.assetNodeOrError?.__typename === 'AssetNode'
    ) {
      return data.assetConditionEvaluationRecordsOrError.records;
    }
    return [];
  }, [data]);

  return {evaluations, queryResult, paginationProps};
}
