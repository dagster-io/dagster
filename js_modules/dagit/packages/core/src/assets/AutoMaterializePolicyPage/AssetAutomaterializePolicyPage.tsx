import {Box, Colors, Subheading} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {AssetKey} from '../types';

import {AutomaterializeLeftPanel} from './AutomaterializeLeftPanel';
import {AutomaterializeMiddlePanel} from './AutomaterializeMiddlePanel';
import {AutomaterializeRightPanel} from './AutomaterializeRightPanel';
import {getEvaluationsWithEmptyAdded} from './getEvaluationsWithEmptyAdded';
import {useEvaluationsQueryResult} from './useEvaluationsQueryResult';

export const AssetAutomaterializePolicyPage = ({
  assetKey,
  assetHasDefinedPartitions,
}: {
  assetKey: AssetKey;
  assetHasDefinedPartitions: boolean;
}) => {
  const {queryResult, paginationProps} = useEvaluationsQueryResult({assetKey});

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const {evaluations, currentEvaluationId} = React.useMemo(() => {
    if (
      queryResult.data?.autoMaterializeAssetEvaluationsOrError?.__typename ===
      'AutoMaterializeAssetEvaluationRecords'
    ) {
      return {
        evaluations: queryResult.data?.autoMaterializeAssetEvaluationsOrError.records,
        currentEvaluationId:
          queryResult.data.autoMaterializeAssetEvaluationsOrError.currentEvaluationId,
      };
    }
    return {evaluations: [], currentEvaluationId: null};
  }, [queryResult.data?.autoMaterializeAssetEvaluationsOrError]);

  const isFirstPage = !paginationProps.hasPrevCursor;
  const isLastPage = !paginationProps.hasNextCursor;
  const isLoading = queryResult.loading && !queryResult.data;
  const evaluationsIncludingEmpty = React.useMemo(
    () =>
      getEvaluationsWithEmptyAdded({
        currentEvaluationId,
        evaluations,
        isFirstPage,
        isLastPage,
        isLoading,
      }),
    [currentEvaluationId, evaluations, isFirstPage, isLastPage, isLoading],
  );

  const [selectedEvaluationId, setSelectedEvaluationId] = useQueryPersistedState<
    number | undefined
  >({
    queryKey: 'evaluation',
    decode: (raw) => {
      const value = parseInt(raw.evaluation);
      return isNaN(value) ? undefined : value;
    },
  });

  const selectedEvaluation = React.useMemo(() => {
    if (selectedEvaluationId !== undefined) {
      const found = evaluationsIncludingEmpty.find(
        (evaluation) => evaluation.evaluationId === selectedEvaluationId,
      );
      if (found) {
        return found;
      }
    }
    return evaluationsIncludingEmpty[0];
  }, [selectedEvaluationId, evaluationsIncludingEmpty]);

  const [maxMaterializationsPerMinute, setMaxMaterializationsPerMinute] = React.useState(1);

  return (
    <AutomaterializePage
      style={{flex: 1, minHeight: 0, color: Colors.Gray700, overflow: 'hidden'}}
      flex={{direction: 'row'}}
    >
      <Box flex={{direction: 'column', grow: 1}}>
        <Box
          flex={{alignItems: 'center'}}
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <Subheading>Evaluation history</Subheading>
        </Box>
        <Box flex={{direction: 'row'}} style={{flex: 1, minHeight: 0}}>
          <Box
            border={{side: 'right', color: Colors.KeylineGray, width: 1}}
            flex={{grow: 0, direction: 'column'}}
            style={{flex: '0 0 296px'}}
          >
            <AutomaterializeLeftPanel
              assetHasDefinedPartitions={assetHasDefinedPartitions}
              evaluations={evaluations}
              evaluationsIncludingEmpty={evaluationsIncludingEmpty}
              paginationProps={paginationProps}
              onSelectEvaluation={(evaluation) => {
                setSelectedEvaluationId(evaluation.evaluationId);
              }}
              selectedEvaluation={selectedEvaluation}
            />
          </Box>
          <Box flex={{grow: 1}} style={{minHeight: 0, overflowY: 'auto'}}>
            <AutomaterializeMiddlePanel
              assetKey={assetKey}
              assetHasDefinedPartitions={assetHasDefinedPartitions}
              key={selectedEvaluation?.evaluationId || ''}
              maxMaterializationsPerMinute={maxMaterializationsPerMinute}
              selectedEvaluation={selectedEvaluation}
            />
          </Box>
        </Box>
      </Box>
      <Box border={{side: 'left', color: Colors.KeylineGray, width: 1}}>
        <AutomaterializeRightPanel
          assetKey={assetKey}
          setMaxMaterializationsPerMinute={setMaxMaterializationsPerMinute}
        />
      </Box>
    </AutomaterializePage>
  );
};

const AutomaterializePage = styled(Box)`
  a span {
    white-space: normal;
  }
`;
