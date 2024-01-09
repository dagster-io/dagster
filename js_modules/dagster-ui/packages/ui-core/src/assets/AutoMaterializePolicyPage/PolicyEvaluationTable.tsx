import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  Dialog,
  Table,
  colorBackgroundDefault,
  colorBackgroundDefaultHover,
  colorBackgroundLightHover,
  colorKeylineDefault,
} from '@dagster-io/ui-components';
import * as React from 'react';
import styled, {css} from 'styled-components';

import {AssetConditionEvaluationStatus} from '../../graphql/types';
import {MetadataEntryFragment} from '../../metadata/types/MetadataEntry.types';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {AssetEventMetadataEntriesTable} from '../AssetEventMetadataEntriesTable';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

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

interface Props {
  evaluationRecord: Pick<AssetConditionEvaluationRecordFragment, 'evaluation'>;
  definition?: AssetViewDefinitionNodeFragment | null;
  selectPartition: (partitionKey: string | null) => void;
}

export const PolicyEvaluationTable = ({evaluationRecord, definition, selectPartition}: Props) => {
  const flattened = React.useMemo(() => flattenEvaluations(evaluationRecord), [evaluationRecord]);
  if (flattened[0]?.evaluation.__typename === 'PartitionedAssetConditionEvaluationNode') {
    return (
      <PartitionedPolicyEvaluationTable
        flattenedRecords={
          flattened as FlattenedConditionEvaluation<PartitionedAssetConditionEvaluationNodeFragment>[]
        }
        definition={definition}
        selectPartition={selectPartition}
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
    />
  );
};

const UnpartitionedPolicyEvaluationTable = ({
  flattenedRecords,
}: {
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
          const {description, status} = evaluation;
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
            >
              <td>
                <PolicyEvaluationCondition
                  icon={type === 'group' ? 'resource' : 'wysiwyg'}
                  label={description}
                  skipped={status === AssetConditionEvaluationStatus.SKIPPED}
                  depth={depth}
                  type={type}
                />
              </td>
              <td>
                <PolicyEvaluationStatusTag status={status} />
              </td>
              {startTimestamp && endTimestamp ? (
                <td>
                  <TimeElapsed startUnix={startTimestamp} endUnix={endTimestamp} />
                </td>
              ) : null}
              <td>
                {evaluation.metadataEntries ? <ViewDetailsButton evaluation={evaluation} /> : null}
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
}: {
  flattenedRecords: FlattenedConditionEvaluation<PartitionedAssetConditionEvaluationNodeFragment>[];
  definition?: AssetViewDefinitionNodeFragment | null;
  selectPartition: (partitionKey: string | null) => void;
}) => {
  const [hoveredKey, setHoveredKey] = React.useState<number | null>(null);

  return (
    <VeryCompactTable>
      <thead>
        <tr>
          <th>Condition</th>
          <th>Result</th>
          <th>Duration</th>
        </tr>
      </thead>
      <tbody>
        {flattenedRecords.map(({evaluation, id, parentId, depth, type}) => {
          const {
            description,
            endTimestamp,
            startTimestamp,
            numTrue,
            numFalse,
            numSkipped,
            trueSubset,
            falseSubset,
            candidateSubset,
          } = evaluation;

          return (
            <EvaluationRow
              key={id}
              $highlight={
                hoveredKey === id ? 'hovered' : parentId === hoveredKey ? 'highlighted' : 'none'
              }
              onMouseEnter={() => setHoveredKey(id)}
              onMouseLeave={() => setHoveredKey(null)}
            >
              <td>
                <PolicyEvaluationCondition
                  icon={type === 'group' ? 'resource' : 'wysiwyg'}
                  label={description}
                  depth={depth}
                  type={type}
                />
              </td>
              <td style={{width: 0}}>
                <Box
                  flex={{direction: 'row', alignItems: 'center', gap: 2}}
                  style={{width: FULL_SEGMENTS_WIDTH}}
                >
                  {numTrue > 0 ? (
                    <PartitionSegmentWithPopover
                      description={description}
                      status={AssetConditionEvaluationStatus.TRUE}
                      subset={trueSubset}
                      selectPartition={selectPartition}
                    />
                  ) : null}
                  {numFalse > 0 ? (
                    <PartitionSegmentWithPopover
                      status={AssetConditionEvaluationStatus.FALSE}
                      description={description}
                      subset={falseSubset}
                      selectPartition={selectPartition}
                    />
                  ) : null}
                  {numSkipped > 0 ? (
                    <PartitionSegmentWithPopover
                      status={AssetConditionEvaluationStatus.SKIPPED}
                      description={description}
                      subset={candidateSubset}
                      selectPartition={selectPartition}
                    />
                  ) : null}
                </Box>
              </td>
              <td>
                <TimeElapsed startUnix={startTimestamp} endUnix={endTimestamp} msec />
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
      inset 1px 1px 0 ${colorKeylineDefault()},
      inset -1px 0 0 ${colorKeylineDefault()} !important;
  }

  & tr:last-child td:last-child {
    box-shadow:
      inset -1px -1px 0 ${colorKeylineDefault()},
      inset 1px 1px 0 ${colorKeylineDefault()} !important;
  }
`;

type RowHighlightType = 'hovered' | 'highlighted' | 'none';

const EvaluationRow = styled.tr<{$highlight: RowHighlightType}>`
  background-color: ${({$highlight}) => {
    switch ($highlight) {
      case 'hovered':
        return colorBackgroundLightHover();
      case 'highlighted':
        return colorBackgroundDefaultHover();
      case 'none':
        return colorBackgroundDefault();
    }
  }};

  ${({$highlight}) => {
    if ($highlight === 'hovered') {
      return css`
        && td {
          box-shadow:
            inset 0 -1px 0 ${colorKeylineDefault()},
            inset 1px 1px 0 ${colorKeylineDefault()} !important;
        }

        && td:last-child {
          box-shadow:
            inset -1px -1px 0 ${colorKeylineDefault()},
            inset 1px 1px 0 ${colorKeylineDefault()} !important;
        }
      `;
    }
    return '';
  }}
`;
