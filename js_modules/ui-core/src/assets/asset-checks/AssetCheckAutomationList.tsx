import {Box, CursorHistoryControls} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {EvaluationList} from '../AutoMaterializePolicyPage/EvaluationList';
import {AssetKey} from '../types';
import {
  AssetCheckAutomationListQuery,
  AssetCheckAutomationListQueryVariables,
} from './types/AssetCheckAutomationList.types';
import {gql} from '../../apollo-client';
import {useCursorPaginatedQuery} from '../../runs/useCursorPaginatedQuery';
import {ASSET_CONDITION_EVALUATION_RECORD_FRAGMENT} from '../AutoMaterializePolicyPage/GetEvaluationsQuery';
import {AssetCheckKeyFragment} from './types/AssetChecksQuery.types';

interface Props {
  assetCheck: AssetCheckKeyFragment;
  checkName: string;
}

export const AssetCheckAutomationList = ({assetCheck, checkName}: Props) => {
  const {queryResult, evaluations, paginationProps} = useAssetCheckEvaluationsQueryResult({
    assetKey: assetCheck.assetKey,
    checkName,
  });

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  return (
    <>
      <Box
        padding={{vertical: 12, horizontal: 20}}
        flex={{direction: 'row', justifyContent: 'flex-end'}}
      >
        <CursorHistoryControls {...paginationProps} style={{marginTop: 0}} />
      </Box>
      <EvaluationList
        assetKey={assetCheck.assetKey}
        isPartitioned={false}
        assetCheckName={checkName}
        evaluations={evaluations}
      />
    </>
  );
};

export const PAGE_SIZE = 30;

export function useAssetCheckEvaluationsQueryResult({
  assetKey,
  checkName,
}: {
  assetKey: AssetKey;
  checkName: string;
}) {
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    AssetCheckAutomationListQuery,
    AssetCheckAutomationListQueryVariables
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
      assetCheckKey: {
        assetKey: {path: assetKey.path},
        name: checkName,
      },
    },
    query: ASSET_CHECK_AUTOMATION_LIST_QUERY,
    pageSize: PAGE_SIZE,
  });

  const {data} = queryResult;
  const evaluations = useMemo(() => {
    if (
      data?.assetConditionEvaluationRecordsOrError?.__typename === 'AssetConditionEvaluationRecords'
    ) {
      return data.assetConditionEvaluationRecordsOrError.records;
    }
    return [];
  }, [data]);

  return {queryResult, evaluations, paginationProps};
}

const ASSET_CHECK_AUTOMATION_LIST_QUERY = gql`
  query AssetCheckAutomationListQuery(
    $assetCheckKey: AssetCheckHandleInput!
    $limit: Int!
    $cursor: String
  ) {
    assetConditionEvaluationRecordsOrError(
      assetKey: null
      assetCheckKey: $assetCheckKey
      limit: $limit
      cursor: $cursor
    ) {
      ... on AssetConditionEvaluationRecords {
        records {
          ...AssetConditionEvaluationRecordFragment
        }
      }
    }
  }
  ${ASSET_CONDITION_EVALUATION_RECORD_FRAGMENT}
`;
