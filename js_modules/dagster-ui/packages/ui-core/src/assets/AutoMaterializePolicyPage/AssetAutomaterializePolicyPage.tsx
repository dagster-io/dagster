import {Box, colorTextLight} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {AssetKey} from '../types';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

import {AutoMaterializeExperimentalBanner} from './AutoMaterializeExperimentalBanner';
import {AutomaterializeLeftPanel} from './AutomaterializeLeftPanel';
import {AutomaterializeMiddlePanel} from './AutomaterializeMiddlePanel';
import {useEvaluationsQueryResult} from './useEvaluationsQueryResult';

export const AssetAutomaterializePolicyPage = ({
  assetKey,
  definition,
}: {
  assetKey: AssetKey;
  definition?: AssetViewDefinitionNodeFragment | null;
}) => {
  const {queryResult, paginationProps} = useEvaluationsQueryResult({assetKey});

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const evaluations = React.useMemo(() => {
    if (
      queryResult.data?.assetConditionEvaluationRecordsOrError?.__typename ===
        'AssetConditionEvaluationRecords' &&
      queryResult.data?.assetNodeOrError?.__typename === 'AssetNode'
    ) {
      return queryResult.data?.assetConditionEvaluationRecordsOrError.records;
    }
    return [];
  }, [
    queryResult.data?.assetConditionEvaluationRecordsOrError,
    queryResult.data?.assetNodeOrError,
  ]);

  const isFirstPage = !paginationProps.hasPrevCursor;

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
    // If we're looking at the most recent slice and have not selected an evaluation ID,
    // default to the first item in the list. Otherwise, don't assume that we should
    // automatically select the first item -- an evaluation on another page might be our
    // active evaluation ID.
    if (selectedEvaluationId === undefined && isFirstPage) {
      return evaluations[0];
    }
    return evaluations.find((evaluation) => evaluation.evaluationId === selectedEvaluationId);
  }, [selectedEvaluationId, isFirstPage, evaluations]);

  return (
    <AutomaterializePage
      style={{flex: 1, minHeight: 0, color: colorTextLight(), overflow: 'hidden'}}
      flex={{direction: 'column'}}
    >
      <Box padding={{horizontal: 24, vertical: 12}} border="bottom">
        <AutoMaterializeExperimentalBanner />
      </Box>
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
