import * as React from 'react';
import styled from 'styled-components';

import {Box, Subheading, colorTextLight} from '@dagster-io/ui-components';

import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {AssetKey} from '../types';
import {AutoMaterializeExperimentalBanner} from './AutoMaterializeExperimentalBanner';
import {AutomaterializeLeftPanel} from './AutomaterializeLeftPanel';
import {AutomaterializeMiddlePanel} from './AutomaterializeMiddlePanel';
import {AutomaterializeRightPanel} from './AutomaterializeRightPanel';
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

  const {evaluations} = React.useMemo(() => {
    if (
      queryResult.data?.autoMaterializeAssetEvaluationsOrError?.__typename ===
        'AutoMaterializeAssetEvaluationRecords' &&
      queryResult.data?.assetNodeOrError?.__typename === 'AssetNode'
    ) {
      return {
        evaluations: queryResult.data?.autoMaterializeAssetEvaluationsOrError.records,
        currentAutoMaterializeEvaluationId:
          queryResult.data.assetNodeOrError.currentAutoMaterializeEvaluationId,
      };
    }
    return {evaluations: [], currentAutoMaterializeEvaluationId: null};
  }, [
    queryResult.data?.autoMaterializeAssetEvaluationsOrError,
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
        <Box flex={{direction: 'column', grow: 1}}>
          <Box
            flex={{alignItems: 'center'}}
            padding={{vertical: 16, horizontal: 24}}
            border="bottom"
          >
            <Subheading>Evaluation history</Subheading>
          </Box>
          <Box flex={{direction: 'row'}} style={{flex: 1, minHeight: 0}}>
            <Box border="right" flex={{grow: 0, direction: 'column'}} style={{flex: '0 0 296px'}}>
              <AutomaterializeLeftPanel
                assetHasDefinedPartitions={assetHasDefinedPartitions}
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
                assetKey={assetKey}
                assetHasDefinedPartitions={assetHasDefinedPartitions}
                // Use the evaluation ID of the current evaluation object, if any. Otherwise
                // fall back to the evaluation ID from the query parameter, if any.
                selectedEvaluationId={selectedEvaluation?.evaluationId || selectedEvaluationId}
              />
            </Box>
          </Box>
        </Box>
        <Box border="left">
          <AutomaterializeRightPanel assetKey={assetKey} />
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
