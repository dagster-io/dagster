import {Box, CursorHistoryControls, NonIdealState} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {useParams} from 'react-router-dom';

import {explorerPathFromString} from './PipelinePathUtils';
import {gql} from '../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {EvaluationList} from '../assets/AutoMaterializePolicyPage/EvaluationList';
import {ASSET_CONDITION_EVALUATION_RECORD_FRAGMENT} from '../assets/AutoMaterializePolicyPage/GetEvaluationsQuery';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';
import {
  JobAutomationListQuery,
  JobAutomationListQueryVariables,
} from './types/JobAutomationRoot.types';

const PAGE_SIZE = 30;

interface Props {
  repoAddress: RepoAddress;
}

export const JobAutomationRoot = ({repoAddress}: Props) => {
  useTrackPageView();

  const params = useParams<{pipelinePath: string}>();
  const {pipelinePath} = params;
  const explorerPath = explorerPathFromString(pipelinePath);
  const {pipelineName} = explorerPath;

  const repo = useRepository(repoAddress);
  const isPartitioned = (repo?.repository.partitionSets || []).some(
    (partitionSet) => partitionSet.pipelineName === pipelineName,
  );

  const {queryResult, evaluations, paginationProps} = useJobEvaluationsQueryResult({
    jobName: pipelineName,
  });

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  if (!evaluations.length && !queryResult.loading) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="automation"
          title="No evaluations"
          description="No automation evaluations have been recorded for this job."
        />
      </Box>
    );
  }

  return (
    <>
      <Box
        padding={{vertical: 12, horizontal: 20}}
        flex={{direction: 'row', justifyContent: 'flex-end'}}
      >
        <CursorHistoryControls {...paginationProps} style={{marginTop: 0}} />
      </Box>
      <EvaluationList
        assetKey={null}
        isPartitioned={isPartitioned}
        jobName={pipelineName}
        evaluations={evaluations}
      />
    </>
  );
};

function useJobEvaluationsQueryResult({jobName}: {jobName: string}) {
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    JobAutomationListQuery,
    JobAutomationListQueryVariables
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
      assetJobKey: {jobName},
    },
    query: JOB_AUTOMATION_LIST_QUERY,
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

export const JOB_AUTOMATION_LIST_QUERY = gql`
  query JobAutomationListQuery($assetJobKey: AssetJobKeyInput!, $limit: Int!, $cursor: String) {
    assetConditionEvaluationRecordsOrError(
      assetJobKey: $assetJobKey
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
