import {Box, Colors, Spinner} from '@dagster-io/ui-components';
import * as React from 'react';
import {useMemo} from 'react';
import styled from 'styled-components';

import {AutoMaterializeExperimentalBanner} from './AutoMaterializeExperimentalBanner';
import {AutomaterializeLeftPanel} from './AutomaterializeLeftPanel';
import {
  AutomaterializeMiddlePanel,
  SELECTED_PARTITION_QUERY_STRING_KEY,
} from './AutomaterializeMiddlePanel';
import {useEvaluationsQueryResult} from './useEvaluationsQueryResult';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {AssetKey} from '../types';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

export const AssetAutomaterializePolicyPage = ({
  assetKey,
  definition,
}: {
  assetKey: AssetKey;
  definition?: AssetViewDefinitionNodeFragment | null;
}) => {
  const {queryResult, evaluations, paginationProps} = useEvaluationsQueryResult({assetKey});

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const isFirstPage = !paginationProps.hasPrevCursor;

  const [selectedEvaluationId, setSelectedEvaluationId] = useQueryPersistedState<
    string | undefined
  >({
    queryKey: 'evaluation',
    decode: (raw) => {
      return raw.evaluation;
    },
    encode: (raw) => {
      // Reset the selected partition
      return {evaluation: raw, [SELECTED_PARTITION_QUERY_STRING_KEY]: undefined};
    },
  });

  const selectedEvaluation = useMemo(() => {
    // If we're looking at the most recent slice and have not selected an evaluation ID,
    // default to the first item in the list. Otherwise, don't assume that we should
    // automatically select the first item -- an evaluation on another page might be our
    // active evaluation ID.
    if (selectedEvaluationId === undefined && isFirstPage) {
      return evaluations[0];
    }
    return evaluations.find((evaluation) => evaluation.evaluationId === selectedEvaluationId);
  }, [selectedEvaluationId, isFirstPage, evaluations]);

  if (!queryResult.data && queryResult.loading) {
    return (
      <Box
        style={{height: 390}}
        flex={{direction: 'row', justifyContent: 'center', alignItems: 'center'}}
      >
        <Spinner purpose="page" />
      </Box>
    );
  }

  return (
    <AutomaterializePage
      style={{flex: 1, minHeight: 0, color: Colors.textLight(), overflow: 'hidden'}}
      flex={{direction: 'column'}}
    >
      <AutoMaterializeExperimentalBanner />
      <Box flex={{direction: 'row'}} style={{minHeight: 0, flex: 1}}>
        <Box flex={{direction: 'row'}} style={{flex: 1, minHeight: 0}}>
          <Box border="right" flex={{grow: 0, direction: 'column'}} style={{flex: '0 0 296px'}}>
            <AutomaterializeLeftPanel
              definition={definition}
              evaluations={evaluations}
              paginationProps={paginationProps}
              onSelectEvaluation={(evaluation) => {
                setSelectedEvaluationId(evaluation.evaluationId);
              }}
              selectedEvaluation={selectedEvaluation}
            />
          </Box>
          <Box flex={{grow: 1}} style={{minHeight: 0, overflowY: 'auto'}}>
            <AutomaterializeMiddlePanel
              key={selectedEvaluation?.evaluationId || selectedEvaluationId}
              assetKey={assetKey}
              // Use the evaluation ID of the current evaluation object, if any. Otherwise
              // fall back to the evaluation ID from the query parameter, if any.
              selectedEvaluationId={selectedEvaluation?.evaluationId || selectedEvaluationId}
              selectedEvaluation={selectedEvaluation}
              definition={definition}
            />
          </Box>
        </Box>
      </Box>
    </AutomaterializePage>
  );
};

const AutomaterializePage = styled(Box)`
  a span {
    white-space: normal;
  }
`;
