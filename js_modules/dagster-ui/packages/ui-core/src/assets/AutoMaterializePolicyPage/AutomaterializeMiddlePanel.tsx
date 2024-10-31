import {Body2, Box, NonIdealState, Subheading} from '@dagster-io/ui-components';
import React from 'react';

import {AutomaterializeMiddlePanelWithData} from './AutomaterializeMiddlePanelWithData';
import {
  GET_EVALUATIONS_QUERY,
  GET_EVALUATIONS_SPECIFIC_PARTITION_QUERY,
} from './GetEvaluationsQuery';
import {
  AssetConditionEvaluationRecordFragment,
  GetEvaluationsQuery,
  GetEvaluationsQueryVariables,
  GetEvaluationsSpecificPartitionQuery,
  GetEvaluationsSpecificPartitionQueryVariables,
} from './types/GetEvaluationsQuery.types';
import {useQuery} from '../../apollo-client';
import {ErrorWrapper} from '../../app/PythonErrorInfo';
import {SensorType} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {AnchorButton} from '../../ui/AnchorButton';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {AssetKey} from '../types';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

interface Props {
  assetKey: AssetKey;
  selectedEvaluationId: string | undefined;
  selectedEvaluation?: AssetConditionEvaluationRecordFragment;
  definition?: AssetViewDefinitionNodeFragment | null;
}

export const SELECTED_PARTITION_QUERY_STRING_KEY = 'selectedPartition';

export const AutomaterializeMiddlePanel = (props: Props) => {
  const {
    assetKey,
    selectedEvaluationId,
    selectedEvaluation: _selectedEvaluation,
    definition,
  } = props;

  const [selectedPartition, setSelectedPartition] = useQueryPersistedState<string | null>({
    queryKey: SELECTED_PARTITION_QUERY_STRING_KEY,
  });

  const skip = !!_selectedEvaluation || !!selectedPartition;
  const isLegacy = !!_selectedEvaluation?.isLegacy;

  // We receive the selected evaluation ID and retrieve it here because the middle panel
  // may be displaying an evaluation that was not retrieved at the page level for the
  // left panel, e.g. as we paginate away from it, we don't want to lose it.
  const queryResult = useQuery<GetEvaluationsQuery, GetEvaluationsQueryVariables>(
    GET_EVALUATIONS_QUERY,
    {
      variables: {
        assetKey,
        cursor: selectedEvaluationId ? `${BigInt(selectedEvaluationId) + 1n}` : undefined,
        limit: 2,
      },
      skip,
    },
  );

  const {data, loading, error} = queryResult;

  const skipSpecificPartitionQuery = !isLegacy || !selectedEvaluationId || !selectedPartition;

  const queryResult2 = useQuery<
    GetEvaluationsSpecificPartitionQuery,
    GetEvaluationsSpecificPartitionQueryVariables
  >(GET_EVALUATIONS_SPECIFIC_PARTITION_QUERY, {
    variables: {
      assetKey,
      evaluationId: selectedEvaluationId!,
      partition: selectedPartition!,
    },
    skip: skipSpecificPartitionQuery,
  });

  const {data: specificPartitionData, previousData: previousSpecificPartitionData} = queryResult2;

  const sensorName = React.useMemo(
    () =>
      definition?.targetingInstigators.find(
        (instigator) =>
          instigator.__typename === 'Sensor' &&
          (instigator.sensorType === SensorType.AUTO_MATERIALIZE ||
            instigator.sensorType === SensorType.AUTOMATION),
      )?.name,
    [definition],
  );

  if (!_selectedEvaluation && loading && !data) {
    return (
      <Box flex={{direction: 'column', grow: 1}}>
        <Box
          style={{flex: '0 0 48px'}}
          border="bottom"
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
    data?.assetConditionEvaluationRecordsOrError?.__typename ===
    'AutoMaterializeAssetEvaluationNeedsMigrationError'
  ) {
    return (
      <Box flex={{direction: 'column', grow: 1}}>
        <Box flex={{direction: 'row', justifyContent: 'center'}} padding={{vertical: 24}}>
          <NonIdealState
            icon="error"
            title="Error"
            description={data.assetConditionEvaluationRecordsOrError.message}
          />
        </Box>
      </Box>
    );
  }

  const evaluations = data?.assetConditionEvaluationRecordsOrError?.records || [];
  const selectedEvaluation =
    _selectedEvaluation ??
    evaluations.find((evaluation) => evaluation.evaluationId === selectedEvaluationId);

  if (!selectedEvaluationId && !evaluations.length) {
    const repoAddress = definition
      ? buildRepoAddress(definition.repository.name, definition.repository.location.name)
      : null;

    return (
      <Box flex={{direction: 'column', grow: 1}}>
        <Box flex={{direction: 'row', justifyContent: 'center'}} padding={{vertical: 24}}>
          <NonIdealState
            icon="sensors"
            title="No evaluations"
            description={
              <Body2>
                <Box flex={{direction: 'column', gap: 8}}>
                  <Body2>
                    This asset&apos;s automation policy has not been evaluated yet. Make sure your
                    automation sensor is running.
                  </Body2>
                  <div>
                    <AnchorButton
                      to={
                        repoAddress && sensorName
                          ? workspacePathFromAddress(repoAddress, `/sensors/${sensorName}`)
                          : '/overview/automation'
                      }
                    >
                      Manage sensor
                    </AnchorButton>
                  </div>
                  <a href="https://docs.dagster.io/concepts/automation/declarative-automation">
                    Learn more about declarative automation
                  </a>
                </Box>
              </Body2>
            }
          />
        </Box>
      </Box>
    );
  }

  return (
    <AutomaterializeMiddlePanelWithData
      selectedEvaluation={selectedEvaluation}
      specificPartitionData={specificPartitionData || previousSpecificPartitionData}
      definition={definition}
      selectPartition={setSelectedPartition}
      selectedPartition={selectedPartition}
    />
  );
};
