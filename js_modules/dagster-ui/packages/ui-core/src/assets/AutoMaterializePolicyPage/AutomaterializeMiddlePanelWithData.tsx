import {
  Box,
  Colors,
  NonIdealState,
  Popover,
  Subheading,
  Subtitle2,
  Tag,
} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {StatusDot} from './AutomaterializeLeftPanel';
import {AutomaterializeRunsTable} from './AutomaterializeRunsTable';
import {PartitionSubsetList} from './PartitionSubsetList';
import {PartitionTagSelector} from './PartitionTagSelector';
import {PolicyEvaluationTable} from './PolicyEvaluationTable';
import {runTableFiltersForEvaluation} from './runTableFiltersForEvaluation';
import {
  AssetConditionEvaluationRecordFragment,
  GetEvaluationsSpecificPartitionQuery,
} from './types/GetEvaluationsQuery.types';
import {usePartitionsForAssetKey} from './usePartitionsForAssetKey';
import {useFeatureFlags} from '../../app/Flags';
import {formatElapsedTimeWithMsec} from '../../app/Util';
import {Timestamp} from '../../app/time/Timestamp';
import {RunsFeedTableWithFilters} from '../../runs/RunsFeedTable';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

interface Props {
  definition?: AssetViewDefinitionNodeFragment | null;
  selectedEvaluation?: AssetConditionEvaluationRecordFragment;
  selectPartition: (partitionKey: string | null) => void;
  specificPartitionData?: GetEvaluationsSpecificPartitionQuery;
  selectedPartition: string | null;
}

export const AutomaterializeMiddlePanelWithData = ({
  selectedEvaluation,
  definition,
  selectPartition,
  specificPartitionData,
  selectedPartition,
}: Props) => {
  const {flagLegacyRunsPage} = useFeatureFlags();
  const evaluation = selectedEvaluation?.evaluation;
  const rootEvaluationNode = useMemo(
    () => evaluation?.evaluationNodes.find((node) => node.uniqueId === evaluation.rootUniqueId),
    [evaluation],
  );
  const rootUniqueId = evaluation?.rootUniqueId;

  const statusTag = useMemo(() => {
    const partitionDefinition = definition?.partitionDefinition;
    const assetKeyPath = definition?.assetKey.path || [];
    const numRequested = selectedEvaluation?.numRequested;

    const numTrue =
      rootEvaluationNode?.__typename === 'PartitionedAssetConditionEvaluationNode'
        ? rootEvaluationNode.numTrue
        : null;

    if (numRequested) {
      if (partitionDefinition && rootUniqueId && numTrue) {
        return (
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            <Popover
              interactionKind="hover"
              placement="bottom"
              hoverOpenDelay={50}
              hoverCloseDelay={50}
              content={
                <PartitionSubsetList
                  description="Requested assets"
                  assetKeyPath={assetKeyPath}
                  evaluationId={selectedEvaluation.evaluationId}
                  nodeUniqueId={rootUniqueId}
                  selectPartition={selectPartition}
                />
              }
            >
              <Tag intent="success">
                <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                  <StatusDot $color={Colors.accentGreen()} $size={8} />
                  {numRequested} requested
                </Box>
              </Tag>
            </Popover>
          </Box>
        );
      }

      return (
        <Tag intent="success">
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            <StatusDot $color={Colors.accentGreen()} />
            Requested
          </Box>
        </Tag>
      );
    }

    return (
      <Tag>
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <StatusDot $color={Colors.accentGray()} />
          Not requested
        </Box>
      </Tag>
    );
  }, [definition, rootEvaluationNode, selectedEvaluation, rootUniqueId, selectPartition]);

  const {partitions: allPartitions} = usePartitionsForAssetKey(definition?.assetKey.path || []);

  const runsFilter = useMemo(
    () => runTableFiltersForEvaluation(selectedEvaluation?.runIds || []),
    [selectedEvaluation],
  );

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
                <Subtitle2>Evaluation result</Subtitle2>
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
                    ? formatElapsedTimeWithMsec(
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
            margin={flagLegacyRunsPage ? {vertical: 12} : {top: 12}}
          >
            <Subtitle2>Runs launched ({selectedEvaluation.runIds.length})</Subtitle2>
          </Box>
          {flagLegacyRunsPage ? (
            <AutomaterializeRunsTable runIds={selectedEvaluation.runIds} />
          ) : runsFilter ? (
            <RunsFeedTableWithFilters filter={runsFilter} includeRunsFromBackfills={false} />
          ) : (
            <Box padding={{vertical: 12}}>
              <NonIdealState
                icon="run"
                title="No runs launched"
                description="No runs were launched by this evaluation."
              />
            </Box>
          )}
          <Box border="bottom" padding={{vertical: 12}}>
            <Subtitle2>Policy evaluation</Subtitle2>
          </Box>
          {definition?.partitionDefinition && selectedEvaluation.isLegacy ? (
            <Box padding={{vertical: 12}} flex={{justifyContent: 'flex-end'}}>
              <PartitionTagSelector
                allPartitions={allPartitions}
                selectedPartition={selectedPartition}
                selectPartition={selectPartition}
              />
            </Box>
          ) : null}
          <PolicyEvaluationTable
            assetKeyPath={definition?.assetKey.path ?? null}
            evaluationId={selectedEvaluation.evaluationId}
            evaluationNodes={
              !selectedEvaluation.isLegacy
                ? selectedEvaluation.evaluationNodes
                : selectedPartition && specificPartitionData?.assetConditionEvaluationForPartition
                  ? specificPartitionData.assetConditionEvaluationForPartition.evaluationNodes
                  : selectedEvaluation.evaluation.evaluationNodes
            }
            isLegacyEvaluation={selectedEvaluation.isLegacy}
            rootUniqueId={selectedEvaluation.evaluation.rootUniqueId}
            selectPartition={selectPartition}
          />
        </Box>
      ) : null}
    </Box>
  );
};
