import {useCursorPaginatedQuery} from '../../runs/useCursorPaginatedQuery';
import {AssetKey} from '../types';
import {GET_EVALUATIONS_QUERY} from './GetEvaluationsQuery';
import {GetEvaluationsQuery, GetEvaluationsQueryVariables} from './types/GetEvaluationsQuery.types';

export const PAGE_SIZE = 30;

// This function exists mostly to use the return type later
export function useEvaluationsQueryResult({assetKey}: {assetKey: AssetKey}) {
  return useCursorPaginatedQuery<GetEvaluationsQuery, GetEvaluationsQueryVariables>({
    nextCursorForResult: (data) => {
      if (
        data.autoMaterializeAssetEvaluationsOrError?.__typename ===
        'AutoMaterializeAssetEvaluationRecords'
      ) {
        return data.autoMaterializeAssetEvaluationsOrError.records[
          PAGE_SIZE - 1
        ]?.evaluationId.toString();
      }
      return undefined;
    },
    getResultArray: (data) => {
      if (
        data?.autoMaterializeAssetEvaluationsOrError?.__typename ===
        'AutoMaterializeAssetEvaluationRecords'
      ) {
        return data.autoMaterializeAssetEvaluationsOrError.records;
      }
      return [];
    },
    variables: {
      assetKey,
    },
    query: GET_EVALUATIONS_QUERY,
    pageSize: PAGE_SIZE,
  });
}
