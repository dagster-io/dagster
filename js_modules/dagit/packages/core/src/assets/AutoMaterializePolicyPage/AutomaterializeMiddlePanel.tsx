import {useQuery} from '@apollo/client';
import {Box, Colors, NonIdealState, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {ErrorWrapper} from '../../app/PythonErrorInfo';
import {AssetKey} from '../types';

import {AutomaterializeMiddlePanelNoPartitions} from './AutomaterializeMiddlePanelNoPartitions';
import {AutomaterializeMiddlePanelWithPartitions} from './AutomaterializeMiddlePanelWithPartitions';
import {GET_EVALUATIONS_QUERY} from './GetEvaluationsQuery';
import {EvaluationOrEmpty} from './types';
import {GetEvaluationsQuery, GetEvaluationsQueryVariables} from './types/GetEvaluationsQuery.types';

interface Props {
  assetKey: AssetKey;
  assetHasDefinedPartitions: boolean;
  maxMaterializationsPerMinute: number;
  selectedEvaluationId: number | undefined;
}

export const AutomaterializeMiddlePanel = (props: Props) => {
  const {
    assetKey,
    assetHasDefinedPartitions,
    maxMaterializationsPerMinute,
    selectedEvaluationId,
  } = props;

  // We receive the selected evaluation ID and retrieve it here because the middle panel
  // may be displaying an evaluation that was not retrieved at the page level for the
  // left panel, e.g. as we paginate away from it, we don't want to lose it.
  const {data, loading, error} = useQuery<GetEvaluationsQuery, GetEvaluationsQueryVariables>(
    GET_EVALUATIONS_QUERY,
    {
      variables: {
        assetKey,
        cursor: selectedEvaluationId ? `${selectedEvaluationId + 1}` : undefined,
        limit: 2,
      },
    },
  );

  if (loading && !data) {
    return (
      <Box flex={{direction: 'column', grow: 1}}>
        <Box
          style={{flex: '0 0 48px'}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
          padding={{horizontal: 16}}
          flex={{alignItems: 'center', justifyContent: 'space-between'}}
        >
          <Subheading>Result</Subheading>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box flex={{direction: 'column', grow: 1}}>
        <Box flex={{direction: 'row', justifyContent: 'center'}} padding={24}>
          <ErrorWrapper>{JSON.stringify(error)}</ErrorWrapper>
        </Box>
      </Box>
    );
  }

  if (
    data?.autoMaterializeAssetEvaluationsOrError?.__typename ===
    'AutoMaterializeAssetEvaluationNeedsMigrationError'
  ) {
    return (
      <Box flex={{direction: 'column', grow: 1}}>
        <Box flex={{direction: 'row', justifyContent: 'center'}} padding={{vertical: 24}}>
          <NonIdealState
            icon="error"
            title="Error"
            description={data.autoMaterializeAssetEvaluationsOrError.message}
          />
        </Box>
      </Box>
    );
  }

  const evaluations = data?.autoMaterializeAssetEvaluationsOrError?.records || [];
  const findSelectedEvaluation = (): EvaluationOrEmpty => {
    const found = evaluations.find(
      (evaluation) => evaluation.evaluationId === selectedEvaluationId,
    );

    if (found) {
      return found;
    }

    return {
      __typename: 'no_conditions_met',
      evaluationId: 0,
      amount: 0,
      endTimestamp: 0,
      startTimestamp: 0,
    };
  };

  const selectedEvaluation = findSelectedEvaluation();

  if (assetHasDefinedPartitions) {
    return (
      <AutomaterializeMiddlePanelWithPartitions
        selectedEvaluation={selectedEvaluation}
        maxMaterializationsPerMinute={maxMaterializationsPerMinute}
      />
    );
  }

  return (
    <AutomaterializeMiddlePanelNoPartitions
      selectedEvaluation={selectedEvaluation}
      maxMaterializationsPerMinute={maxMaterializationsPerMinute}
    />
  );
};
