import {useQuery} from '@apollo/client';
import {
  Box,
  Icon,
  NonIdealState,
  Subheading,
  Subtitle2,
  Tag,
  colorAccentGray,
  colorAccentGreen,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {ErrorWrapper} from '../../app/PythonErrorInfo';
import {formatElapsedTimeWithoutMsec} from '../../app/Util';
import {Timestamp} from '../../app/time/Timestamp';
import {numberFormatter} from '../../ui/formatters';
import {AssetKey} from '../types';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

import {StatusDot} from './AutomaterializeLeftPanel';
import {AutomaterializeRunsTable} from './AutomaterializeRunsTable';
import {
  GET_EVALUATIONS_QUERY,
  GET_EVALUATIONS_SPECIFIC_PARTITION_QUERY,
} from './GetEvaluationsQuery';
import {PolicyEvaluationTable} from './PolicyEvaluationTable';
import {
  AssetConditionEvaluationRecordFragment,
  GetEvaluationsQuery,
  GetEvaluationsQueryVariables,
  GetEvaluationsSpecificPartitionQuery,
  GetEvaluationsSpecificPartitionQueryVariables,
} from './types/GetEvaluationsQuery.types';

interface Props {
  assetKey: AssetKey;
  selectedEvaluationId: number | undefined;
  selectedEvaluation?: AssetConditionEvaluationRecordFragment;
  definition?: AssetViewDefinitionNodeFragment | null;
}

export const AutomaterializeMiddlePanel = (props: Props) => {
  const {
    assetKey,
    selectedEvaluationId,
    selectedEvaluation: _selectedEvaluation,
    definition,
  } = props;

  const [selectedPartition, setSelectPartition] = React.useState<string | null>(null);

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
      skip: !!_selectedEvaluation || !!selectedPartition,
    },
  );

  const {data: specificPartitionData} = useQuery<
    GetEvaluationsSpecificPartitionQuery,
    GetEvaluationsSpecificPartitionQueryVariables
  >(GET_EVALUATIONS_SPECIFIC_PARTITION_QUERY, {
    variables: {
      assetKey,
      evaluationId: selectedEvaluationId!,
      partition: selectedPartition!,
    },
    skip: !selectedEvaluationId || !selectedPartition,
  });

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

  return (
    <AutomaterializeMiddlePanelWithData
      selectedEvaluation={selectedEvaluation}
      specificPartitionData={specificPartitionData}
      definition={definition}
      selectPartition={setSelectPartition}
      selectedPartition={selectedPartition}
    />
  );
};

export const AutomaterializeMiddlePanelWithData = ({
  selectedEvaluation,
  definition,
  selectPartition,
  specificPartitionData,
  selectedPartition,
}: {
  definition?: AssetViewDefinitionNodeFragment | null;
  selectedEvaluation?: AssetConditionEvaluationRecordFragment;
  selectPartition: (partitionKey: string | null) => void;
  specificPartitionData?: GetEvaluationsSpecificPartitionQuery;
  selectedPartition: string | null;
}) => {
  const statusTag = React.useMemo(() => {
    if (selectedEvaluation?.numRequested) {
      if (definition?.partitionDefinition) {
        return (
          <Tag intent="success">
            <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
              <StatusDot $color={colorAccentGreen()} />
              {selectedEvaluation.numRequested} Requested
            </Box>
          </Tag>
        );
      }
      return (
        <Tag intent="success">
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            <StatusDot $color={colorAccentGreen()} />
            Requested
          </Box>
        </Tag>
      );
    }
    return (
      <Tag>
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <StatusDot $color={colorAccentGray()} />
          Not Requested
        </Box>
      </Tag>
    );
  }, [definition, selectedEvaluation]);

  const evaluation = selectedEvaluation?.evaluation;
  let partitionsEvaluated = 0;
  if (evaluation) {
    const rootEvaluationNode = evaluation.evaluationNodes.find(
      (node) => node.uniqueId === evaluation.rootUniqueId,
    )!;
    if (rootEvaluationNode.__typename === 'PartitionedAssetConditionEvaluationNode') {
      partitionsEvaluated =
        rootEvaluationNode.numTrue + rootEvaluationNode.numFalse + rootEvaluationNode.numSkipped;
    }
  }

  return (
    <Box flex={{direction: 'column', grow: 1}}>
      <Box
        style={{flex: '0 0 48px'}}
        padding={{horizontal: 16}}
        border="bottom"
        flex={{alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Subheading>Result</Subheading>
      </Box>
      {selectedEvaluation ? (
        <Box padding={{horizontal: 24, vertical: 12}}>
          <Box border="bottom" padding={{vertical: 12}} margin={{bottom: 12}}>
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 24}}>
              <Box flex={{direction: 'column', gap: 5}}>
                <Subtitle2>Evaluation Result</Subtitle2>
                <div>{statusTag}</div>
              </Box>
              {selectedEvaluation?.timestamp ? (
                <Box flex={{direction: 'column', gap: 5}}>
                  <Subtitle2>Timestamp</Subtitle2>
                  <Timestamp timestamp={{unix: selectedEvaluation?.timestamp}} />
                </Box>
              ) : null}
              <Box flex={{direction: 'column', gap: 5}}>
                <Subtitle2>Duration</Subtitle2>
                <div>
                  {selectedEvaluation?.startTimestamp && selectedEvaluation?.endTimestamp
                    ? formatElapsedTimeWithoutMsec(
                        (selectedEvaluation.endTimestamp - selectedEvaluation.startTimestamp) *
                          1000,
                      )
                    : '\u2013'}
                </div>
              </Box>
            </div>
          </Box>
          <Box
            border="bottom"
            padding={{vertical: 12}}
            margin={{top: 12, bottom: partitionsEvaluated ? undefined : 12}}
          >
            <Subtitle2>Policy evaluation</Subtitle2>
          </Box>
          {partitionsEvaluated ? (
            <Box padding={{vertical: 12}} flex={{justifyContent: 'space-between'}}>
              {numberFormatter.format(partitionsEvaluated)} partitions evaluated
              {selectedPartition ? (
                <Tag>
                  <Box flex={{alignItems: 'center', gap: 4}}>
                    {selectedPartition}
                    <div
                      onClick={() => {
                        selectPartition(null);
                      }}
                    >
                      <Icon name="close" />
                    </div>
                  </Box>
                </Tag>
              ) : null}
            </Box>
          ) : null}
          <PolicyEvaluationTable
            evaluationRecord={
              specificPartitionData?.assetConditionEvaluationForPartition
                ? {evaluation: specificPartitionData.assetConditionEvaluationForPartition}
                : selectedEvaluation
            }
            definition={definition}
            selectPartition={selectPartition}
          />
          <Box border="bottom" padding={{vertical: 12}} margin={{vertical: 12}}>
            <Subtitle2>Runs launched ({selectedEvaluation.runIds.length})</Subtitle2>
          </Box>
          <AutomaterializeRunsTable runIds={selectedEvaluation.runIds} />
        </Box>
      ) : null}
    </Box>
  );
};
