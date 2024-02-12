import {Box, Button, Colors, Dialog, Icon, Table, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';
import styled, {css} from 'styled-components';

import {PartitionSegmentWithPopover} from './PartitionSegmentWithPopover';
import {PolicyEvaluationCondition} from './PolicyEvaluationCondition';
import {PolicyEvaluationStatusTag} from './PolicyEvaluationStatusTag';
import {FlattenedConditionEvaluation, flattenEvaluations} from './flattenEvaluations';
import {
  AssetConditionEvaluationRecordFragment,
  PartitionedAssetConditionEvaluationNodeFragment,
  SpecificPartitionAssetConditionEvaluationNodeFragment,
  UnpartitionedAssetConditionEvaluationNodeFragment,
} from './types/GetEvaluationsQuery.types';
import {AssetConditionEvaluationStatus} from '../../graphql/types';
import {MetadataEntryFragment} from '../../metadata/types/MetadataEntry.types';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {AssetEventMetadataEntriesTable} from '../AssetEventMetadataEntriesTable';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

interface Props {
  evaluationRecord: Pick<AssetConditionEvaluationRecordFragment, 'evaluation'>;
  definition?: AssetViewDefinitionNodeFragment | null;
  selectPartition: (partitionKey: string | null) => void;
}

export const PolicyEvaluationTable = ({evaluationRecord, definition, selectPartition}: Props) => {
  const [collapsedRecords, setcollapsedRecords] = React.useState<Set<string>>(new Set());
  const flattened = React.useMemo(
    () => flattenEvaluations(evaluationRecord, collapsedRecords),
    [evaluationRecord, collapsedRecords],
  );

  const toggleCollapsed = React.useCallback((uniqueId: string) => {
    setcollapsedRecords((collapsedRecords) => {
      const copy = new Set(collapsedRecords);
      if (copy.has(uniqueId)) {
        copy.delete(uniqueId);
      } else {
        copy.add(uniqueId);
      }
      return copy;
    });
  }, []);
  if (flattened[0]?.evaluation.__typename === 'PartitionedAssetConditionEvaluationNode') {
    return (
      <PartitionedPolicyEvaluationTable
        flattenedRecords={
          flattened as FlattenedConditionEvaluation<PartitionedAssetConditionEvaluationNodeFragment>[]
        }
        definition={definition}
        selectPartition={selectPartition}
        toggleCollapsed={toggleCollapsed}
        collapsedRecords={collapsedRecords}
      />
    );
  }

  return (
    <UnpartitionedPolicyEvaluationTable
      flattenedRecords={
        flattened as
          | FlattenedConditionEvaluation<UnpartitionedAssetConditionEvaluationNodeFragment>[]
          | FlattenedConditionEvaluation<SpecificPartitionAssetConditionEvaluationNodeFragment>[]
      }
      toggleCollapsed={toggleCollapsed}
      collapsedRecords={collapsedRecords}
    />
  );
};

const UnpartitionedPolicyEvaluationTable = ({
  flattenedRecords,
  collapsedRecords,
  toggleCollapsed,
}: {
  collapsedRecords: Set<string>;
  toggleCollapsed: (id: string) => void;
  flattenedRecords:
    | FlattenedConditionEvaluation<UnpartitionedAssetConditionEvaluationNodeFragment>[]
    | FlattenedConditionEvaluation<SpecificPartitionAssetConditionEvaluationNodeFragment>[];
}) => {
  const [hoveredKey, setHoveredKey] = React.useState<number | null>(null);
  const isSpecificPartitionAssetConditionEvaluations =
    flattenedRecords[0]?.evaluation.__typename === 'SpecificPartitionAssetConditionEvaluationNode';

  return (
    <VeryCompactTable>
      <thead>
        <tr>
          <th>Condition</th>
          <th>Result</th>
          {isSpecificPartitionAssetConditionEvaluations ? null : <th>Duration</th>}
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        {flattenedRecords.map(({evaluation, id, parentId, depth, type}) => {
          const {description, status, uniqueId} = evaluation;
          let endTimestamp, startTimestamp;
          if ('endTimestamp' in evaluation) {
            endTimestamp = evaluation.endTimestamp;
            startTimestamp = evaluation.startTimestamp;
          }
          return (
            <EvaluationRow
              key={id}
              $highlight={
                hoveredKey === id ? 'hovered' : parentId === hoveredKey ? 'highlighted' : 'none'
              }
              onMouseEnter={() => setHoveredKey(id)}
              onMouseLeave={() => setHoveredKey(null)}
              onClick={() => {
                toggleCollapsed(uniqueId);
              }}
            >
              <td>
                <PolicyEvaluationCondition
                  icon={type === 'group' ? 'resource' : 'wysiwyg'}
                  label={description}
                  skipped={status === AssetConditionEvaluationStatus.SKIPPED}
                  depth={depth}
                  type={type}
                  isCollapsed={!collapsedRecords.has(uniqueId)}
                  hasChildren={evaluation.childUniqueIds.length > 0}
                />
              </td>
              <td>
                <PolicyEvaluationStatusTag status={status} />
              </td>
              {startTimestamp && endTimestamp ? (
                <td>
                  <TimeElapsed startUnix={startTimestamp} endUnix={endTimestamp} showMsec />
                </td>
              ) : null}
              <td>
                {evaluation.metadataEntries?.length ? (
                  <ViewDetailsButton evaluation={evaluation} />
                ) : null}
              </td>
            </EvaluationRow>
          );
        })}
      </tbody>
    </VeryCompactTable>
  );
};

const ViewDetailsButton = ({
  evaluation,
}: {
  evaluation: {metadataEntries: MetadataEntryFragment[]};
}) => {
  const [showDetails, setShowDetails] = React.useState(false);
  return (
    <>
      <Dialog
        title="Evaluation metadata"
        isOpen={showDetails}
        onClose={() => {
          setShowDetails(false);
        }}
      >
        <AssetEventMetadataEntriesTable event={evaluation} />
      </Dialog>
      <Button
        onClick={() => {
          setShowDetails(true);
        }}
      >
        View details
      </Button>
    </>
  );
};

const FULL_SEGMENTS_WIDTH = 200;

const PartitionedPolicyEvaluationTable = ({
  flattenedRecords,
  selectPartition,
  collapsedRecords,
  toggleCollapsed,
}: {
  flattenedRecords: FlattenedConditionEvaluation<PartitionedAssetConditionEvaluationNodeFragment>[];
  definition?: AssetViewDefinitionNodeFragment | null;
  selectPartition: (partitionKey: string | null) => void;
  collapsedRecords: Set<string>;
  toggleCollapsed: (id: string) => void;
}) => {
  const [hoveredKey, setHoveredKey] = React.useState<number | null>(null);

  return (
    <VeryCompactTable>
      <thead>
        <tr>
          <th>Condition</th>
          <th>Partitions evaluated</th>
          <th>Result</th>
          <th>Duration</th>
        </tr>
      </thead>
      <tbody>
        {flattenedRecords.map(({evaluation, id, parentId, depth, type}) => {
          const {description, candidateSubset, endTimestamp, startTimestamp, trueSubset, uniqueId} =
            evaluation;
          const consideredPartitions = candidateSubset?.subsetValue.partitionKeys?.length;

          return (
            <EvaluationRow
              key={id}
              $highlight={
                hoveredKey === id ? 'hovered' : parentId === hoveredKey ? 'highlighted' : 'none'
              }
              onMouseEnter={() => setHoveredKey(id)}
              onMouseLeave={() => setHoveredKey(null)}
              onClick={() => {
                toggleCollapsed(uniqueId);
              }}
            >
              <td>
                <PolicyEvaluationCondition
                  icon={type === 'group' ? 'resource' : 'wysiwyg'}
                  label={description}
                  depth={depth}
                  type={type}
                  isCollapsed={!collapsedRecords.has(evaluation.uniqueId)}
                  hasChildren={evaluation.childUniqueIds.length > 0}
                />
              </td>
              <td>
                {consideredPartitions ? (
                  consideredPartitions
                ) : (
                  <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                    All
                    <Tooltip content="Evaluated against all partitions that existed at the time of evaluation">
                      <Icon name="info" />
                    </Tooltip>
                  </Box>
                )}
              </td>
              <td style={{width: 0}}>
                <Box
                  flex={{direction: 'row', alignItems: 'center', gap: 2}}
                  style={{width: FULL_SEGMENTS_WIDTH}}
                >
                  <PartitionSegmentWithPopover
                    description={description}
                    status={AssetConditionEvaluationStatus.TRUE}
                    subset={trueSubset}
                    selectPartition={selectPartition}
                  />
                </Box>
              </td>
              <td>
                <TimeElapsed startUnix={startTimestamp} endUnix={endTimestamp} showMsec />
              </td>
            </EvaluationRow>
          );
        })}
      </tbody>
    </VeryCompactTable>
  );
};

const VeryCompactTable = styled(Table)`
  & tr td {
    vertical-align: middle;
  }

  & tr td:first-child {
    padding: 2px 16px;
  }

  & tr th:last-child,
  & tr td:last-child {
    box-shadow:
      inset 1px 1px 0 ${Colors.keylineDefault()},
      inset -1px 0 0 ${Colors.keylineDefault()} !important;
  }

  & tr:last-child td:last-child {
    box-shadow:
      inset -1px -1px 0 ${Colors.keylineDefault()},
      inset 1px 1px 0 ${Colors.keylineDefault()} !important;
  }
`;

type RowHighlightType = 'hovered' | 'highlighted' | 'none';

const EvaluationRow = styled.tr<{$highlight: RowHighlightType}>`
  cursor: pointer;
  background-color: ${({$highlight}) => {
    switch ($highlight) {
      case 'hovered':
        return Colors.backgroundLightHover();
      case 'highlighted':
        return Colors.backgroundDefaultHover();
      case 'none':
        return Colors.backgroundDefault();
    }
  }};

  ${({$highlight}) => {
    if ($highlight === 'hovered') {
      return css`
        && td {
          box-shadow:
            inset 0 -1px 0 ${Colors.keylineDefault()},
            inset 1px 1px 0 ${Colors.keylineDefault()} !important;
        }

        && td:last-child {
          box-shadow:
            inset -1px -1px 0 ${Colors.keylineDefault()},
            inset 1px 1px 0 ${Colors.keylineDefault()} !important;
        }
      `;
    }
    return '';
  }}
`;
